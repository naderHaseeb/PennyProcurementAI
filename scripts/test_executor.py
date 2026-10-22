from backend.app.agent.executor import execute_pipeline

# Our independently verified January 2014 query
pipeline = [
    {
        "$match": {
            "creation_date": {
                "$gte": {"$date": "2014-01-01T00:00:00Z"},
                "$lt": {"$date": "2014-02-01T00:00:00Z"}
            }
        }
    },
    {
        "$group": {
            "_id": "$purchase_order_number"
        }
    },
    {
        "$count": "total_orders"
    }
]

print("Executing verified MongoDB query...")

results = execute_pipeline(pipeline)

print("Database result:", results)

assert results == [{"total_orders": 4557}]
print("SUCCESS: Result matches our verified answer!")
