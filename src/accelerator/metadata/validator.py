from accelerator.config.enums import FilterOperator, JoinType, SCDType
from accelerator.metadata.schema_models import ModelSpec


class ValidationError(ValueError):
    pass


_REQUIRED_KEYS = {"name", "source", "target", "scd_type", "business_key", "columns"}
_OPTIONAL_KEYS = {"row_hash_columns", "row_filters", "joins"}
_FORBIDDEN_KEYS = {"sql", "where", "hash", "date_format"}


def validate_raw_payload(payload: dict) -> None:
    unknown = set(payload.keys()) - _REQUIRED_KEYS - _OPTIONAL_KEYS
    if unknown:
        raise ValidationError(f"Unknown top-level keys: {sorted(unknown)}")

    missing = _REQUIRED_KEYS - set(payload.keys())
    if missing:
        raise ValidationError(f"Missing mandatory keys: {sorted(missing)}")

    forbidden_present = _FORBIDDEN_KEYS & set(payload.keys())
    if forbidden_present:
        raise ValidationError(f"Forbidden keys present: {sorted(forbidden_present)}")


def validate_model_spec(spec: ModelSpec) -> None:
    if spec.scd_type not in {SCDType.ONE.value, SCDType.TWO.value}:
        raise ValidationError("scd_type must be '1' or '2'")

    column_names = [col.name for col in spec.columns]
    if len(column_names) != len(set(column_names)):
        raise ValidationError("columns contain duplicate names")

    for bk in spec.business_key.columns:
        if bk not in column_names:
            raise ValidationError(f"business_key column '{bk}' missing from columns")

    for rh in spec.row_hash_columns:
        if rh not in column_names:
            raise ValidationError(f"row_hash column '{rh}' missing from columns")

    valid_ops = {item.value for item in FilterOperator}
    for row_filter in spec.row_filters:
        if row_filter.operator not in valid_ops:
            raise ValidationError(f"Unsupported row filter operator '{row_filter.operator}'")

    valid_join_types = {item.value for item in JoinType}
    aliases = ["s"]
    for index, join in enumerate(spec.joins, start=1):
        if join.type.lower() not in valid_join_types:
            raise ValidationError(f"Unsupported join type '{join.type}'")

        alias = join.alias or f"j{index}"
        if alias in aliases:
            raise ValidationError(f"Duplicate join alias '{alias}'")

        if join.type.lower() == JoinType.CROSS.value and join.on:
            raise ValidationError("CROSS join cannot define ON conditions")

        if join.type.lower() != JoinType.CROSS.value and not join.on:
            raise ValidationError("Non-CROSS joins require at least one ON condition")

        for on in join.on:
            if on.left_alias not in aliases:
                raise ValidationError(
                    f"Join alias '{on.left_alias}' not available for join '{alias}'"
                )

        aliases.append(alias)
