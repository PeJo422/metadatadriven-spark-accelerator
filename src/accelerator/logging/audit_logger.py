import hashlib
from datetime import datetime, timezone


def log_sql_run(
    spark,
    *,
    model_name: str,
    source: str,
    target: str,
    scd_type: str,
    hash_version: int,
    changed_ratio: float,
    duration_seconds: float,
    sql_text: str,
    environment: str,
) -> None:
    checksum = hashlib.sha256(sql_text.encode("utf-8")).hexdigest()
    timestamp = datetime.now(tz=timezone.utc).isoformat()

    insert_sql = f"""
    INSERT INTO audit.sql_runs
    (model_name, source, target, scd_type, hash_version, changed_ratio, duration_seconds, timestamp, sql_checksum, environment)
    VALUES
    ('{model_name}', '{source}', '{target}', '{scd_type}', {hash_version}, {changed_ratio}, {duration_seconds}, '{timestamp}', '{checksum}', '{environment}')
    """.strip()

    spark.sql(insert_sql)
