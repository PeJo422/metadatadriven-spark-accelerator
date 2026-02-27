from accelerator.config.constants import DELIMITER, NULL_TOKEN


def _normalize_expr(column_expr: str) -> str:
    return f"coalesce(lower(trim(cast({column_expr} as string))), '{NULL_TOKEN}')"


def build_sha256_hash_expr(column_exprs: list[str]) -> str:
    normalized = [_normalize_expr(col) for col in column_exprs]
    joined = f"concat_ws('{DELIMITER}', {', '.join(normalized)})"
    return f"sha2({joined}, 256)"
