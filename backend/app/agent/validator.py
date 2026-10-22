from datetime import datetime

ALLOWED_FIELDS = {
    "creation_date", "purchase_date",
    "purchase_order_number", "supplier_name",
    "item_name", "quantity", "total_price_cents"
}

ALLOWED_STAGES = {
    "$match", "$group", "$count", "$sort", "$limit"
}


def validate_pipeline(pipeline):
    if not isinstance(pipeline, list) or not 1 <= len(pipeline) <= 8:
        raise ValueError("Pipeline must contain 1-8 stages")

    available_fields = set(ALLOWED_FIELDS)

    for stage in pipeline:
        if not isinstance(stage, dict) or len(stage) != 1:
            raise ValueError("Invalid pipeline stage")

        operation, value = next(iter(stage.items()))

        if operation not in ALLOWED_STAGES:
            raise ValueError(f"Forbidden operation: {operation}")

        if operation == "$match":
            if not isinstance(value, dict) or not value:
                raise ValueError("Invalid match")

            for field, condition in value.items():
                if field not in ALLOWED_FIELDS:
                    raise ValueError(f"Unknown field: {field}")

                if isinstance(condition, dict):
                    if field not in {"creation_date", "purchase_date"}:
                        raise ValueError("Unsupported comparison field")
                    if not condition:
                        raise ValueError("Empty comparison")

                    for op, date_value in condition.items():
                        if op not in {"$gte", "$gt", "$lt", "$lte"}:
                            raise ValueError("Forbidden comparison")
                        if not isinstance(date_value, dict) or set(date_value) != {"$date"}:
                            raise ValueError("Invalid date format")
                        try:
                            datetime.fromisoformat(
                                date_value["$date"].replace("Z", "+00:00")
                            )
                        except (ValueError, TypeError, AttributeError):
                            raise ValueError("Invalid date")

                elif condition is not None and type(condition) not in (str, int, float, bool):
                    raise ValueError("Invalid match value")

        elif operation == "$group":
            if not isinstance(value, dict) or "_id" not in value:
                raise ValueError("Invalid group")

            group_by = value["_id"]
            if group_by is not None:
                if not isinstance(group_by, str) or not group_by.startswith("$"):
                    raise ValueError("Invalid group field")
                if group_by[1:] not in ALLOWED_FIELDS:
                    raise ValueError("Unknown group field")

            for name, expression in value.items():
                if name == "_id":
                    continue
                if not name.isidentifier() or name.startswith("_"):
                    raise ValueError("Invalid output name")
                if not isinstance(expression, dict) or set(expression) != {"$sum"}:
                    raise ValueError("Only $sum is supported")

                source = expression["$sum"]
                if isinstance(source, str):
                    if not source.startswith("$") or source[1:] not in {
                        "total_price_cents", "quantity"
                    }:
                        raise ValueError("Invalid sum field")
                elif type(source) not in (int, float):
                    raise ValueError("Invalid sum expression")

                available_fields.add(name)

            available_fields.add("_id")

        elif operation == "$count":
            if not isinstance(value, str) or not value.isidentifier():
                raise ValueError("Invalid count name")
            available_fields.add(value)

        elif operation == "$sort":
            if not isinstance(value, dict) or not value:
                raise ValueError("Invalid sort")
            for field, direction in value.items():
                if field not in available_fields or type(direction) is not int or direction not in (1, -1):
                    raise ValueError("Invalid sort field or direction")

        elif operation == "$limit":
            if type(value) is not int or not 1 <= value <= 100:
                raise ValueError("Limit must be 1-100")

    return True
