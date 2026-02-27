from accelerator.config.constants import MAX_ALLOWED_CHANGE_RATIO


class SCDGuardError(RuntimeError):
    pass


def evaluate_change_ratio(changed_rows: int, total_rows: int) -> float:
    if total_rows <= 0:
        return 0.0
    return changed_rows / total_rows


def assert_change_ratio_within_limit(
    changed_rows: int,
    total_rows: int,
    override: bool = False,
) -> float:
    ratio = evaluate_change_ratio(changed_rows, total_rows)
    if ratio > MAX_ALLOWED_CHANGE_RATIO and not override:
        raise SCDGuardError(
            f"Changed ratio {ratio:.4f} exceeds maximum {MAX_ALLOWED_CHANGE_RATIO:.4f}. "
            "Set override flag to continue."
        )
    return ratio
