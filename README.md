# Metadata-Driven Bronze → Silver Spark Accelerator

En metadata-driven Spark-plattform för Bronze → Silver där YAML är **miljöneutral** och runtime binder till fysisk miljö.

## Designprincip

YAML beskriver endast **logisk modell**:
- modellnamn
- logiskt källtabellsnamn
- logiskt måltabellsnamn

YAML innehåller **inte**:
- schema (`bronze`, `silver`)
- lakehouse
- miljöspecifika paths

Miljöbindning görs via `EnvironmentConfig` i runtime.

## Arkitektur

```text
YAML (logical model)
  ↓
Loader
  ↓
Validator
  ↓
Environment binding (source/target/join tables)
  ↓
Schema Compare
  ↓
Context Builder
  ↓
Hash/Join/Filter/Date Builders
  ↓
Jinja Renderer
  ↓
IF dry_run: Print + Stop
ELSE: ALTER ADD + MERGE + Audit Log
```

## Environment binding

`src/accelerator/config/environment.py`

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class EnvironmentConfig:
    bronze_schema: str
    silver_schema: str
    bronze_lakehouse: str | None = None
    silver_lakehouse: str | None = None
```

- Fabric default-lakehouse: använd normalt bara schema (`bronze_schema` / `silver_schema`).
- Multi-lakehouse stöds via optional `*_lakehouse`.

## YAML contract (strict)

### Mandatory
- `name`
- `source`
- `target`
- `scd_type`
- `business_key`
- `columns`

### Optional
- `row_hash_columns`
- `row_filters`
- `joins`

### Viktig regel
`source`, `target`, och `joins[].table` måste vara logiska tabellnamn (utan punktnotation).

✅ Exempel:

```yaml
name: dim_customer
source: customer
target: dim_customer
```

❌ Ej tillåtet i YAML:

```yaml
source: bronze.customer
target: silver.dim_customer
```

## Runtime API

```python
from pyspark.sql import SparkSession
from accelerator.config.environment import EnvironmentConfig
from accelerator.runner import run_model

spark = SparkSession.builder.getOrCreate()

env = EnvironmentConfig(
    bronze_schema="bronze",
    silver_schema="silver",
)

result = run_model(
    spark,
    model_path="examples/models/dim_customer_scd2_with_left_join.yml",
    env=env,
    dry_run=True,
)
print(result)
```

## SCD, hash, schema drift

- SCD1 och SCD2 stöds.
- Deterministisk hash: cast → trim → lower → coalesce(null-token) → concat_ws → sha2(256).
- Datum normaliseras till `yyyy-MM-dd` och `<Column>Key` genereras som `yyyyMMdd` int.
- Schema drift: endast `ADD COLUMN` tillåtet automatiskt.
- SCD guard stoppar körning vid för hög ändringsratio utan override.

## Exempelmodeller (alla stödjda kombinationer)

Finns i `examples/models/`:

1. `dim_customer_scd1_minimal.yml`
   - Minimal SCD1.
2. `dim_customer_scd1_with_inner_left_full_joins.yml`
   - SCD1 + `inner`, `left`, `full` joins.
3. `dim_customer_scd2_with_left_join.yml`
   - SCD2 + datumkolumn + join.
4. `fact_customer_cross_join.yml`
   - SCD1 + `cross` join.
5. `operator_coverage.yml`
   - Samtliga filteroperatorer (`is_null`, `is_not_null`, `equals`, `not_equals`, `less_than`, `greater_than`, `less_or_equal`, `greater_or_equal`).

