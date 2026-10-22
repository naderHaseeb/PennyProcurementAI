import re
from datetime import datetime, timezone

from backend.app.agent.executor import execute_pipeline


def dates(start, end):
    def iso(year, month):
        return f"{year:04d}-{month:02d}-01T00:00:00Z"

    return {
        "$gte": {"$date": iso(*start)},
        "$lt": {"$date": iso(*end)}
    }


def run(pipeline):
    return execute_pipeline(pipeline)


def try_answer(question):
    q = question.lower().strip()
    year_match = re.search(r"\b(201[2-5])\b", q)
    year = int(year_match.group(1)) if year_match else None

    months = {
        "january": 1, "february": 2, "march": 3,
        "april": 4, "may": 5, "june": 6,
        "july": 7, "august": 8, "september": 9,
        "october": 10, "november": 11, "december": 12
    }

    month = next((v for k, v in months.items() if k in q), None)

    def period_filter(y, m=None):
        if m:
            start = (y, m)
            end = (y + 1, 1) if m == 12 else (y, m + 1)
        else:
            start, end = (y, 1), (y + 1, 1)

        return {"$match": {"creation_date": dates(start, end)}}

    def result(answer, pipeline, rows):
        return {
            "question": question,
            "answer": answer,
            "pipeline": pipeline,
            "results": rows
        }

    # Unique purchase-order counts
    if year and ("how many orders" in q or "number of orders" in q):
        pipeline = [
            period_filter(year, month),
            {"$group": {"_id": "$purchase_order_number"}},
            {"$count": "total_orders"}
        ]
        rows = run(pipeline)
        count = rows[0]["total_orders"] if rows else 0
        period = next((k.title() for k, v in months.items() if v == month), None)
        label = f"{period} {year}" if period else str(year)
        return result(
            f"{count:,} unique purchase orders were created in {label}.",
            pipeline, rows
        )

    # Four independently calculated calendar quarters
    if year and "quarter" in q and "spending" in q:
        totals = []
        pipelines = []

        for quarter in range(4):
            start_month = quarter * 3 + 1
            end_month = start_month + 3
            end = (
                (year + 1, 1) if end_month == 13
                else (year, end_month)
            )

            pipeline = [
                {"$match": {
                    "creation_date": dates((year, start_month), end)
                }},
                {"$group": {
                    "_id": None,
                    "total_cents": {"$sum": "$total_price_cents"}
                }}
            ]

            rows = run(pipeline)
            cents = rows[0]["total_cents"] if rows else 0
            totals.append({"quarter": quarter + 1, "total_cents": cents})
            pipelines.append(pipeline)

        highest = max(totals, key=lambda x: x["total_cents"])

        lines = [
            f"Q{r['quarter']}: ${r['total_cents'] / 100:,.2f}"
            for r in totals
        ]

        answer = (
            f"Highest spending in {year}: Q{highest['quarter']}\n\n"
            + "\n".join(lines)
        )

        return result(answer, pipelines, totals)

    # Most frequently appearing item names
    if "item" in q and (
        "frequent" in q or "most ordered" in q or "popular" in q
    ):
        n = re.search(r"top\s+(\d+)", q)
        limit = min(int(n.group(1)), 10) if n else 5

        pipeline = [
            {"$match": {"item_name": {"$ne": None}}},
            {"$group": {
                "_id": "$item_name",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}},
            {"$limit": limit}
        ]

        # The initial validator only supports date comparison or
        # basic equality matching. Remove $match and exclude missing
        # names when presenting results in this prototype.
        pipeline = pipeline[1:]

        rows = run(pipeline)
        rows = [r for r in rows if r["_id"] is not None]
        lines = [
            f"{i}. {r['_id']} — {r['count']:,} line records"
            for i, r in enumerate(rows, 1)
        ]

        return result(
            "Most frequent item names:\n" + "\n".join(lines),
            pipeline, rows
        )

    # Supplier spending ranking
    if "supplier" in q and (
        "spending" in q or "spent" in q or "highest" in q
    ):
        n = re.search(r"top\s+(\d+)", q)
        limit = min(int(n.group(1)), 10) if n else 5

        pipeline = [
            {"$group": {
                "_id": "$supplier_name",
                "total_cents": {"$sum": "$total_price_cents"}
            }},
            {"$sort": {"total_cents": -1}},
            {"$limit": limit}
        ]

        rows = run(pipeline)
        rows = [r for r in rows if r["_id"] is not None]
        lines = [
            f"{i}. {r['_id']} — ${r['total_cents'] / 100:,.2f}"
            for i, r in enumerate(rows, 1)
        ]

        return result(
            "Top suppliers by net recorded spending:\n"
            + "\n".join(lines),
            pipeline, rows
        )

    # Let the existing LLM-powered LangGraph handle other questions.
    return None
