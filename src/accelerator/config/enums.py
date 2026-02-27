from enum import Enum


class SCDType(str, Enum):
    ONE = "1"
    TWO = "2"


class JoinType(str, Enum):
    INNER = "inner"
    LEFT = "left"
    FULL = "full"
    CROSS = "cross"


class FilterOperator(str, Enum):
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    LESS_THAN = "less_than"
    GREATER_THAN = "greater_than"
    LESS_OR_EQUAL = "less_or_equal"
    GREATER_OR_EQUAL = "greater_or_equal"
