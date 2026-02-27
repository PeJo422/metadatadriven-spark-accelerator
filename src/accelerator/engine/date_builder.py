from accelerator.config.constants import DATEKEY_FORMAT, DATE_FORMAT


def build_date_projection(alias: str, column_name: str) -> tuple[str, str, str]:
    cast_expr = f"cast({alias}.{column_name} as date)"
    normalized = f"date_format({cast_expr}, '{DATE_FORMAT}')"
    key_expr = f"cast(date_format({cast_expr}, '{DATEKEY_FORMAT}') as int)"
    return normalized, key_expr, f"{column_name}Key"
