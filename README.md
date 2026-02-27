# Metadata-Driven Bronze → Silver Spark Accelerator

This repository contains a **metadata-driven Bronze → Silver** platform for Spark, implemented with strict YAML contracts and deterministic SQL generation.

## Scope

### What this platform does
- Transforms **Bronze → Silver**.
- Uses strict **YAML metadata** as the model contract.
- Supports **SCD1** and **SCD2** merge behavior.
- Uses deterministic hashing for business and row hashes.
- Supports additive schema drift (**ADD COLUMN** only).
- Supports **dry run** (render + print, no execution).
- Executes in Spark SQL.
- Optionally logs execution metadata into `audit.sql_runs`.

### What this platform does not do
- Build Gold layers.
- Act as a generic SQL engine.
- Allow free-form SQL in YAML.
- Perform destructive schema changes (drop/rename/type-change).

## High-level flow

```text
YAML
 ↓
Loader
 ↓
Validator
 ↓
Schema Compare
 ↓
Context Builder
 ↓
Hash Builder
 ↓
Join Builder
 ↓
Filter Builder
 ↓
Jinja Renderer
 ↓
IF dry_run:
    Print + Stop
ELSE:
    ALTER ADD (if needed)
    MERGE
    Log
```

## Repository layout

```text
src/accelerator/
├── runner.py
├── config/
│   ├── constants.py
│   └── enums.py
├── metadata/
│   ├── loader.py
│   ├── schema_models.py
│   └── validator.py
├── engine/
│   ├── context_builder.py
│   ├── hash_builder.py
│   ├── join_builder.py
│   ├── filter_builder.py
│   ├── date_builder.py
│   ├── schema_manager.py
│   └── scd_guard.py
├── executor/
│   └── spark_executor.py
├── logging/
│   └── audit_logger.py
└── templates/
    ├── select.sql.j2
    ├── merge_scd1.sql.j2
    └── merge_scd2.sql.j2
```

## Non-configurable platform constants

These are hard-coded and must not be overridden by YAML:

- `HASH_ALGORITHM = "sha2_256"`
- `DELIMITER = "||"`
- `NULL_TOKEN = "__null__"`
- `HASH_VERSION = 1`
- `DATE_FORMAT = "yyyy-MM-dd"`
- `DATEKEY_FORMAT = "yyyyMMdd"`
- `SOURCE_ALIAS = "s"`
- `TARGET_ALIAS = "t"`
- `MAX_ALLOWED_CHANGE_RATIO = 0.30`

## YAML contract (strict)

### Mandatory keys
- `name`
- `source`
- `target`
- `scd_type`
- `business_key`
- `columns`

### Optional keys
- `row_hash_columns`
- `row_filters`
- `joins`

### Forbidden patterns
- SQL expressions in YAML.
- Custom hash definitions.
- Custom date formats.
- Arbitrary free-form `WHERE` logic.

## Supported operators and joins

### Row filter operators
- `is_null`
- `is_not_null`
- `equals`
- `not_equals`
- `less_than`
- `greater_than`
- `less_or_equal`
- `greater_or_equal`

Rules:
- Filters are combined with `AND`.
- No `OR` support.
- Filters are applied in the source CTE before joins when possible.

### Join types
- `inner`
- `left`
- `full`
- `cross`

Rules:
- `cross` cannot define `on`.
- Non-`cross` joins require at least one `on` predicate.
- `left_alias` must be `s` or a previously introduced join alias.
- If alias is omitted, aliases are auto-generated as `j1`, `j2`, ...

## Hash and date behavior

### Deterministic hash strategy
For each hash input column, the engine applies:
1. `cast(... as string)`
2. `trim(...)`
3. `lower(...)`
4. `coalesce(..., '__null__')`

Then it concatenates with `'||'` and applies `sha2(..., 256)`.

`business_hash` and `row_hash` are generated separately.

### Date handling
For every `columns[].type == date`:
- value is normalized to `yyyy-MM-dd`.
- `<ColumnName>Key` is generated as `INT` in `yyyyMMdd` format.
- DateKey is null when source date is null.
- Hashing uses normalized date string (`yyyy-MM-dd`).

## Schema drift policy

Automatically allowed:
- `ADD COLUMN`

Rejected:
- `DROP COLUMN`
- type change
- rename

## SCD behavior

### SCD1
- `MERGE` by `business_hash`
- `WHEN MATCHED` and `row_hash` changes → `UPDATE`
- `WHEN NOT MATCHED` → `INSERT`

### SCD2
- Uses `valid_from`, `valid_to`, `is_current`
- Closes current record when `row_hash` changes
- Inserts new current version

## Guards

Before execute:
- changed row count and total target row count are compared.
- if ratio > `MAX_ALLOWED_CHANGE_RATIO`, execution fails unless explicit override is provided.

## Runtime modes

### Dry run
`run_model(..., dry_run=True)`
- Loads + validates YAML
- Compares schema
- Renders SQL
- Prints schema changes, hash version, SCD type, SQL
- Does not execute ALTER/MERGE or audit logging

### Execution
`run_model(..., dry_run=False)`
- Executes additive `ALTER TABLE ADD COLUMN` if needed
- Executes merge
- Applies SCD guard
- Optionally logs audit run

## Basic usage

```python
from pyspark.sql import SparkSession
from accelerator.runner import run_model

spark = SparkSession.builder.getOrCreate()

result = run_model(
    spark,
    yaml_path="examples/models/dim_customer_scd2_with_left_join.yml",
    dry_run=True,
)
print(result)
```

## Example YAML models

See `examples/models/` for examples covering:
- minimal SCD1
- SCD1 with multiple non-cross joins
- SCD2 with date handling
- cross join example
- full filter operator coverage

