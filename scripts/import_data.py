
import csv
import os
from pathlib import Path
from datetime import datetime
from decimal import Decimal, InvalidOperation

from dotenv import load_dotenv
from pymongo import MongoClient


# 1. Load database settings
load_dotenv()

mongo_uri = os.getenv(
    "MONGODB_URI",
    "mongodb://127.0.0.1:27017"
)

client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
db = client["procurement_ai"]
collection = db["purchases"]


# 2. Find the CSV dataset
csv_files = list(Path("data/raw").rglob("*.csv"))

if len(csv_files) != 1:
    raise SystemExit(
        f"Expected 1 CSV file, found {len(csv_files)}."
    )

file_path = csv_files[0]


# 3. Convert prices to integer cents
def clean_price(value):
    if not value:
        return None

    try:
        cleaned = value.replace("$", "").replace(",", "").strip()
        amount = Decimal(cleaned)
        cents = amount * 100

        if not amount.is_finite() or cents != cents.to_integral_value():
            return None

        return int(cents)

    except (InvalidOperation, ValueError):
        return None


# 4. Convert dates into Python datetime values
def clean_date(value):
    if not value:
        return None

    try:
        return datetime.strptime(value.strip(), "%m/%d/%Y")
    except ValueError:
        return None


# 5. Convert quantities to numbers
def clean_quantity(value):
    if not value:
        return None

    try:
        return float(value)
    except ValueError:
        return None


# 6. Connect to MongoDB
client.admin.command("ping")
print("Connected to MongoDB!")


# 7. Prevent accidentally importing duplicates
if collection.count_documents({}) > 0:
    raise SystemExit(
        "The purchases collection already contains data. "
        "Import stopped to avoid duplicates."
    )


# 8. Read and prepare each CSV record
batch = []
total_imported = 0

with open(file_path, newline="", encoding="utf-8-sig") as file:
    reader = csv.DictReader(file)

    for row in reader:
        # Convert empty strings to missing values
        document = {
            key: value if value != "" else None
            for key, value in row.items()
        }

        # Add fields designed for our AI queries
        document["creation_date"] = clean_date(
            row["Creation Date"]
        )

        document["purchase_date"] = clean_date(
            row["Purchase Date"]
        )

        document["purchase_order_number"] = row[
            "Purchase Order Number"
        ]

        document["supplier_name"] = row["Supplier Name"]
        document["item_name"] = row["Item Name"]

        document["quantity"] = clean_quantity(
            row["Quantity"]
        )

        document["total_price_cents"] = clean_price(
            row["Total Price"]
        )

        batch.append(document)

        # Insert records in batches of 1000
        if len(batch) == 1000:
            collection.insert_many(batch)
            total_imported += len(batch)
            batch = []

            print(f"Imported {total_imported} records")


# 9. Insert remaining records
if batch:
    collection.insert_many(batch)
    total_imported += len(batch)


# 10. Verify the import
print("\nImport complete!")
print("Records imported:", total_imported)
print("MongoDB records:", collection.count_documents({}))


# 11. Create indexes for common questions
collection.create_index("creation_date")
collection.create_index("purchase_order_number")
collection.create_index("supplier_name")
collection.create_index("item_name")

print("Indexes created successfully!")

client.close()
