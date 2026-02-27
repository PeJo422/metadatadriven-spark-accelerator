from accelerator.metadata.schema_models import FilterSpec


_OPERATOR_SQL = {
    "is_null": "{col} IS NULL",
    "is_not_null": "{col} IS NOT NULL",
    "equals": "{col} = {val}",
    "not_equals": "{col} <> {val}",
    "less_than": "{col} < {val}",
    "greater_than": "{col} > {val}",
    "less_or_equal": "{col} <= {val}",
    "greater_or_equal": "{col} >= {val}",
}


def _format_value(value: object) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, str):
        escaped = value.replace("'", "''")
        return f"'{escaped}'"
    return str(value)


def build_filters_where_clause(filters: list[FilterSpec], source_alias: str = "s") -> str:
    if not filters:
        return ""

    conditions = []
    for row_filter in filters:
        template = _OPERATOR_SQL[row_filter.operator]
        col = f"{source_alias}.{row_filter.column}"
        condition = template.format(col=col, val=_format_value(row_filter.value))
        conditions.append(condition)

    return " AND ".join(conditions)
