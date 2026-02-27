from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from validate import ModelValidationError, load_yaml, validate_model


def _build_jinja_env(templates_dir: Path) -> Environment:
    return Environment(
        loader=FileSystemLoader(str(templates_dir)),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )


def _selected_columns(model: dict[str, Any]) -> list[str]:
    result: list[str] = [column["name"] for column in model["columns"]]

    for column in model["columns"]:
        if column["type"] in {"date", "datetime"}:
            result.append(f"{column['name']}Key")

    if model.get("row_hash_columns"):
        result.append("row_hash")

    result.append("_compiled_at")
    return result


def render_sql(model_path: Path, project_root: Path) -> Path:
    schema_path = project_root / "schema" / "model_schema.json"
    templates_dir = project_root / "templates"
    output_dir = project_root / "output"

    model = load_yaml(model_path)
    validate_model(model, schema_path)

    output_dir.mkdir(parents=True, exist_ok=True)
    env = _build_jinja_env(templates_dir)

    row_hash_columns = [
        f"{model['source']['alias']}.{column}" for column in model.get("row_hash_columns", [])
    ]

    select_sql = env.get_template("select.sql.j2").render(
        **model,
        joins=model.get("joins", []),
        row_filters=model.get("row_filters", []),
        incremental=model.get("incremental", {"enabled": False}),
        row_hash_columns=row_hash_columns,
    ).strip()

    if model["scd_type"] == 1:
        selected_cols = _selected_columns(model)
        sql = env.get_template("merge_scd1.sql.j2").render(
            **model,
            select_sql=select_sql,
            insert_columns=selected_cols,
            update_columns=selected_cols,
        )
    else:
        sql = select_sql

    output_path = output_dir / f"{model['name']}.sql"
    output_path.write_text(sql.strip() + "\n", encoding="utf-8")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Compile YAML model to SQL")
    parser.add_argument("model", type=Path, help="Path to YAML model")
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Root directory containing schema/templates/output",
    )
    args = parser.parse_args()

    try:
        output_path = render_sql(args.model, args.project_root)
    except ModelValidationError as exc:
        raise SystemExit(str(exc))

    print(f"Generated SQL: {output_path}")


if __name__ == "__main__":
    main()
