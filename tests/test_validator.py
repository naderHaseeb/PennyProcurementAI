import pytest
from backend.app.agent.validator import validate_pipeline


def test_valid_january_query():
    pipeline = [
        {"$match": {
            "creation_date": {
                "$gte": {"$date": "2014-01-01T00:00:00Z"},
                "$lt": {"$date": "2014-02-01T00:00:00Z"}
            }
        }},
        {"$group": {"_id": "$purchase_order_number"}},
        {"$count": "total_orders"}
    ]
    assert validate_pipeline(pipeline) is True


def test_reject_write_operation():
    with pytest.raises(ValueError):
        validate_pipeline([{"$out": "another_collection"}])


def test_reject_unknown_field():
    with pytest.raises(ValueError):
        validate_pipeline([{"$match": {"secret_field": "test"}}])


def test_reject_invalid_date():
    with pytest.raises(ValueError):
        validate_pipeline([
            {"$match": {
                "creation_date": {
                    "$gte": {"$date": "not-a-date"}
                }
            }}
        ])
