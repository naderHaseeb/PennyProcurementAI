from datetime import datetime
from copy import deepcopy

from backend.app.db.mongo import purchases
from backend.app.agent.validator import validate_pipeline


def convert_dates(value):
    """Convert Extended JSON dates into Python datetime objects."""

    if isinstance(value, list):
        return [convert_dates(item) for item in value]

    if isinstance(value, dict):
        if set(value.keys()) == {"$date"}:
            return datetime.fromisoformat(
                value["$date"].replace("Z", "+00:00")
            )

        return {
            key: convert_dates(item)
            for key, item in value.items()
        }

    return value


def execute_pipeline(pipeline):
    """Validate and run an aggregation pipeline."""

    validate_pipeline(pipeline)

    safe_pipeline = convert_dates(deepcopy(pipeline))

    results = list(
        purchases.aggregate(
            safe_pipeline,
            maxTimeMS=5000
        )
    )

    return results
