from accelerator.config.constants import HASH_VERSION, SOURCE_ALIAS, TARGET_ALIAS
from accelerator.engine.date_builder import build_date_projection
from accelerator.engine.filter_builder import build_filters_where_clause
from accelerator.engine.hash_builder import build_sha256_hash_expr
from accelerator.engine.join_builder import build_join_sql
from accelerator.metadata.schema_models import ModelSpec


def build_context(spec: ModelSpec, *, source_table: str, target_table: str) -> dict:
    select_exprs: list[str] = []
    hash_source_exprs: dict[str, str] = {}

    for column in spec.columns:
        if column.type.lower() == "date":
            normalized, key_expr, date_key_name = build_date_projection(SOURCE_ALIAS, column.name)
            select_exprs.append(f"{normalized} as {column.name}")
            select_exprs.append(f"{key_expr} as {date_key_name}")
            hash_source_exprs[column.name] = normalized
        else:
            expr = f"{SOURCE_ALIAS}.{column.name}"
            select_exprs.append(f"{expr} as {column.name}")
            hash_source_exprs[column.name] = expr

    row_hash_columns = spec.row_hash_columns or [c.name for c in spec.columns]
    business_hash_expr = build_sha256_hash_expr([hash_source_exprs[c] for c in spec.business_key.columns])
    row_hash_expr = build_sha256_hash_expr([hash_source_exprs[c] for c in row_hash_columns])

    joins, join_sql = build_join_sql(spec.joins)
    filter_sql = build_filters_where_clause(spec.row_filters, SOURCE_ALIAS)

    return {
        "model_name": spec.name,
        "source": source_table,
        "target": target_table,
        "source_alias": SOURCE_ALIAS,
        "target_alias": TARGET_ALIAS,
        "select_columns": select_exprs,
        "business_hash_expr": business_hash_expr,
        "row_hash_expr": row_hash_expr,
        "business_key_columns": spec.business_key.columns,
        "joins": joins,
        "join_sql": join_sql,
        "filter_sql": filter_sql,
        "scd_type": spec.scd_type,
        "hash_version": HASH_VERSION,
    }
