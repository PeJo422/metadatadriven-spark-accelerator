from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from accelerator.config.enums import SCDType


class SparkExecutor:
    def __init__(self, spark_session) -> None:
        self.spark = spark_session
        templates_path = Path(__file__).resolve().parent.parent / "templates"
        self.jinja = Environment(
            loader=FileSystemLoader(str(templates_path)),
            undefined=StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render_select_sql(self, context: dict) -> str:
        return self.jinja.get_template("select.sql.j2").render(**context)

    def render_merge_sql(self, context: dict) -> str:
        template_name = (
            "merge_scd2.sql.j2"
            if context["scd_type"] == SCDType.TWO.value
            else "merge_scd1.sql.j2"
        )
        return self.jinja.get_template(template_name).render(**context)

    def run_sql(self, sql_text: str) -> None:
        self.spark.sql(sql_text)

    def fetch_table_schema(self, table_name: str) -> dict[str, str]:
        rows = self.spark.sql(f"DESCRIBE {table_name}").collect()
        schema: dict[str, str] = {}
        for row in rows:
            col_name = str(row.col_name).strip()
            data_type = str(row.data_type).strip()
            if col_name and not col_name.startswith("#") and data_type:
                schema[col_name] = data_type
        return schema

    def scalar(self, sql_text: str) -> int:
        return int(self.spark.sql(sql_text).first()[0])
