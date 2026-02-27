from pathlib import Path

import yaml

from accelerator.metadata.schema_models import (
    BusinessKeySpec,
    ColumnSpec,
    FilterSpec,
    JoinOnSpec,
    JoinSpec,
    ModelSpec,
)


def load_model_spec(path: str | Path) -> ModelSpec:
    with Path(path).open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)

    return ModelSpec(
        name=payload["name"],
        source=payload["source"],
        target=payload["target"],
        scd_type=str(payload["scd_type"]),
        business_key=BusinessKeySpec(columns=list(payload["business_key"]["columns"])),
        columns=[ColumnSpec(name=col["name"], type=col["type"]) for col in payload["columns"]],
        row_hash_columns=list(payload.get("row_hash_columns") or []),
        row_filters=[
            FilterSpec(column=f["column"], operator=f["operator"], value=f.get("value"))
            for f in (payload.get("row_filters") or [])
        ],
        joins=[
            JoinSpec(
                table=j["table"],
                type=j["type"],
                alias=j.get("alias"),
                on=[
                    JoinOnSpec(
                        left_alias=o["left_alias"],
                        left_column=o["left_column"],
                        right_column=o["right_column"],
                    )
                    for o in (j.get("on") or [])
                ],
            )
            for j in (payload.get("joins") or [])
        ],
    )
