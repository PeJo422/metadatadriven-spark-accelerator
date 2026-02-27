import time
from dataclasses import replace
from pathlib import Path

import yaml

from accelerator.config.environment import EnvironmentConfig
from accelerator.engine.context_builder import build_context
from accelerator.engine.scd_guard import assert_change_ratio_within_limit
from accelerator.engine.schema_manager import SchemaMismatchError, build_add_column_sql, compare_schema
from accelerator.executor.spark_executor import SparkExecutor
from accelerator.logging.audit_logger import log_sql_run
from accelerator.metadata.loader import load_model_spec
from accelerator.metadata.validator import validate_model_spec, validate_raw_payload

def _bind_model_to_environment(spec, env: EnvironmentConfig):
    bound_joins = [replace(join, table=env.qualify_source(join.table)) for join in spec.joins]
    return replace(spec, joins=bound_joins)


def run_model(
    spark,
    model_path: str,
    *,
    env: EnvironmentConfig,
    dry_run: bool = False,
    override_change_ratio: bool = False,
    environment: str = "dev",
    enable_audit_log: bool = True,
) -> dict:
    start = time.time()

    with Path(model_path).open("r", encoding="utf-8") as handle:
        raw_payload = yaml.safe_load(handle)
    validate_raw_payload(raw_payload)

    spec = load_model_spec(model_path)
    validate_model_spec(spec)

    source_table = env.qualify_source(spec.source)
    target_table = env.qualify_target(spec.target)
    bound_spec = _bind_model_to_environment(spec, env)

    executor = SparkExecutor(spark)
    target_schema = executor.fetch_table_schema(target_table)
    additions, mismatches = compare_schema(spec.columns, target_schema)
    if mismatches:
        raise SchemaMismatchError("Type mismatches found: " + "; ".join(mismatches))

    context = build_context(bound_spec, source_table=source_table, target_table=target_table)
    select_sql = executor.render_select_sql(context)
    merge_sql = executor.render_merge_sql(context)

    changed_rows_sql = f"""
    WITH source_prepared AS (
      {select_sql}
    )
    SELECT count(*)
    FROM source_prepared s
    JOIN {target_table} t
      ON t.business_hash = s.business_hash
    WHERE t.row_hash <> s.row_hash
    """.strip()
    total_rows_sql = f"SELECT count(*) FROM {target_table}"

    changed_rows = executor.scalar(changed_rows_sql)
    total_rows = executor.scalar(total_rows_sql)
    changed_ratio = assert_change_ratio_within_limit(
        changed_rows,
        total_rows,
        override=override_change_ratio,
    )

    alter_sql = build_add_column_sql(target_table, additions)

    if dry_run:
        print("=== DRY RUN ===")
        print(f"Model: {spec.name}")
        print(f"Source (resolved): {source_table}")
        print(f"Target (resolved): {target_table}")
        print(f"Schema changes: {[f'{c.name}:{c.type}' for c in additions]}")
        print(f"Hash version: {context['hash_version']}")
        print(f"SCD type: {spec.scd_type}")
        print("--- SELECT SQL ---")
        print(select_sql)
        print("--- MERGE SQL ---")
        print(merge_sql)
        return {
            "mode": "dry_run",
            "source_table": source_table,
            "target_table": target_table,
            "schema_changes": [c.name for c in additions],
            "changed_ratio": changed_ratio,
            "select_sql": select_sql,
            "merge_sql": merge_sql,
        }

    for alter in alter_sql:
        executor.run_sql(alter)

    executor.run_sql(f"CREATE OR REPLACE TEMP VIEW source_prepared AS {select_sql}")
    executor.run_sql(merge_sql)

    duration = time.time() - start
    if enable_audit_log:
        log_sql_run(
            spark,
            model_name=spec.name,
            source=source_table,
            target=target_table,
            scd_type=spec.scd_type,
            hash_version=context["hash_version"],
            changed_ratio=changed_ratio,
            duration_seconds=duration,
            sql_text=f"{select_sql}\n{merge_sql}",
            environment=environment,
        )

    return {
        "mode": "execute",
        "source_table": source_table,
        "target_table": target_table,
        "schema_changes": [c.name for c in additions],
        "changed_ratio": changed_ratio,
        "duration_seconds": duration,
    }
