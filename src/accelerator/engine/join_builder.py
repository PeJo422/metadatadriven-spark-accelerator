from accelerator.metadata.schema_models import JoinSpec


def build_join_sql(joins: list[JoinSpec]) -> tuple[list[dict], str]:
    alias_chain = ["s"]
    rendered: list[dict] = []
    sql_parts: list[str] = []

    for index, join in enumerate(joins, start=1):
        alias = join.alias or f"j{index}"
        join_type = join.type.upper()

        if join_type == "CROSS":
            clause = f"CROSS JOIN {join.table} {alias}"
        else:
            on_sql = " AND ".join(
                [f"{on.left_alias}.{on.left_column} = {alias}.{on.right_column}" for on in join.on]
            )
            clause = f"{join_type} JOIN {join.table} {alias} ON {on_sql}"

        sql_parts.append(clause)
        alias_chain.append(alias)
        rendered.append({"table": join.table, "alias": alias, "type": join_type, "on": join.on})

    return rendered, "\n".join(sql_parts)
