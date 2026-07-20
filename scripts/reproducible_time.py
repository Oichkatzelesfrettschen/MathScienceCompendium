"""Provide deterministic timestamps for generated repository artifacts."""

from __future__ import annotations

import os
from datetime import datetime, timezone


DEFAULT_SOURCE_DATE_EPOCH = 0


def generated_at_utc() -> str:
    """Return SOURCE_DATE_EPOCH as an ISO 8601 UTC timestamp.

    Repository generators default to the Unix epoch so repeated runs do not
    modify tracked artifacts solely because wall-clock time advanced.
    """
    raw_epoch = os.environ.get("SOURCE_DATE_EPOCH", str(DEFAULT_SOURCE_DATE_EPOCH))
    try:
        epoch = int(raw_epoch)
    except ValueError as error:
        raise ValueError("SOURCE_DATE_EPOCH must be an integer") from error
    if epoch < 0:
        raise ValueError("SOURCE_DATE_EPOCH must be non-negative")
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()
