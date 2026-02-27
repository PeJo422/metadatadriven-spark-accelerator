from accelerator.metadata.schema_models import ColumnSpec


class SchemaMismatchError(RuntimeError):
    pass


def compare_schema(
    declared_columns: list[ColumnSpec],
    target_schema: dict[str, str],
) -> tuple[list[ColumnSpec], list[str]]:
    to_add: list[ColumnSpec] = []
    mismatches: list[str] = []

    for col in declared_columns:
        target_type = target_schema.get(col.name)
        if target_type is None:
            to_add.append(col)
        elif target_type.lower() != col.type.lower():
            mismatches.append(f"{col.name}: declared={col.type} target={target_type}")

    return to_add, mismatches


def build_add_column_sql(target_table: str, additions: list[ColumnSpec]) -> list[str]:
    return [f"ALTER TABLE {target_table} ADD COLUMN ({col.name} {col.type})" for col in additions]
