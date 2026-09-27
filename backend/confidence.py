"""
Canonical Confidence Normalization Contract (Sprint 3.2B-R2)
Single authoritative normalization function for all ingestion, persistence,
API validation, and migration paths.
"""

import math
from typing import Any


class InvalidConfidenceError(ValueError):
    """Raised when a confidence score violates the canonical contract."""
    pass


def normalize_confidence(value: Any) -> float:
    """
    Canonical confidence normalization:
    1. Finite real number in [0.0, 1.0]: kept as-is (raw probability).
       e.g. 0 -> 0.0, 0.965 -> 0.965, 1 -> 1.0.
    2. Finite real number in (1.0, 100.0]: divided by 100.0 (legacy percentage).
       e.g. 1.0001 -> 0.010001, 2 -> 0.02, 96.5 -> 0.965, 100 -> 1.0.
    3. Rejected with InvalidConfidenceError:
       - None, booleans, non-numeric strings, complex types
       - NaN, +Inf, -Inf
       - value < 0.0
       - value > 100.0
    No clamping to 0 or 1 is permitted. Invalid values are never converted to 0.
    """
    if value is None:
        raise InvalidConfidenceError("Confidence cannot be None")

    # In Python, bool is a subclass of int: isinstance(True, int) is True. Reject bool explicitly!
    if isinstance(value, bool):
        raise InvalidConfidenceError(f"Invalid confidence type: bool ({value})")

    try:
        val = float(value)
    except (ValueError, TypeError) as e:
        raise InvalidConfidenceError(f"Confidence cannot be converted to float: {value!r}") from e

    if math.isnan(val) or math.isinf(val):
        raise InvalidConfidenceError(f"Confidence must be finite, got: {val}")

    if val < 0.0:
        raise InvalidConfidenceError(f"Confidence cannot be negative, got: {val}")

    if val > 100.0:
        raise InvalidConfidenceError(f"Confidence cannot exceed 100.0 (or 1.0), got: {val}")

    if val <= 1.0:
        return float(val)

    return float(val / 100.0)