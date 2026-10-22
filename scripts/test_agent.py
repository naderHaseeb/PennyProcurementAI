import json

from backend.app.agent.graph import agent

question = "How many orders were created in January 2014?"

print("\nQuestion:", question)

try:
    result = agent.invoke({
        "question": question
    })

    print("\nGenerated MongoDB query:")
    print(json.dumps(result["pipeline"], indent=2))

    print("\nDatabase results:")
    print(result["results"])

    print("\nAssistant answer:")
    print(result["answer"])

    assert result["results"] == [{"total_orders": 4557}]
    print("\nSUCCESS: Answer matches verified MongoDB result!")

except Exception as error:
    print("\nTest failed:", type(error).__name__, str(error))
    raise
