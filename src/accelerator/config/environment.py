from dataclasses import dataclass


@dataclass(frozen=True)
class EnvironmentConfig:
    bronze_schema: str
    silver_schema: str
    bronze_lakehouse: str | None = None
    silver_lakehouse: str | None = None

    def qualify_source(self, table_name: str) -> str:
        return self._qualify(table_name, self.bronze_schema, self.bronze_lakehouse)

    def qualify_target(self, table_name: str) -> str:
        return self._qualify(table_name, self.silver_schema, self.silver_lakehouse)

    @staticmethod
    def _qualify(table_name: str, schema: str, lakehouse: str | None) -> str:
        if lakehouse:
            return f"{lakehouse}.{schema}.{table_name}"
        return f"{schema}.{table_name}"
