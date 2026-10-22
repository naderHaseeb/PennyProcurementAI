
from pathlib import Path
import pandas as pd

# 1. Find the CSV dataset
csv_files = list(Path("data/raw").rglob("*.csv"))

if not csv_files:
    print("No CSV file found!")
    raise SystemExit(1)

file_path = csv_files[0]

# 2. Load the complete dataset
df = pd.read_csv(file_path, low_memory=False)

# 3. Display general information
print("\n=== DATASET OVERVIEW ===")
print("File:", file_path.name)
print("Total rows:", len(df))
print("Total columns:", len(df.columns))

# 4. Display missing values
print("\n=== MISSING VALUES ===")
print(df.isnull().sum().sort_values(ascending=False))

# 5. Check unique purchase orders
print("\n=== PURCHASE ORDERS ===")
print("Unique orders:", df["Purchase Order Number"].nunique())
print("Missing order numbers:", df["Purchase Order Number"].isnull().sum())

# 6. Examine price values
print("\n=== PRICE EXAMPLES ===")
print(df["Total Price"].head(10).to_string(index=False))

# 7. Convert price text into numbers
price_text = (
    df["Total Price"]
    .astype("string")
    .str.replace("$", "", regex=False)
    .str.replace(",", "", regex=False)
)

prices = pd.to_numeric(price_text, errors="coerce")

print("\n=== PRICE ANALYSIS ===")
print("Valid numeric prices:", prices.notna().sum())
print("Missing or invalid prices:", prices.isna().sum())
print("Negative prices:", (prices < 0).sum())

# 8. Examine dates
dates = pd.to_datetime(
    df["Creation Date"],
    format="%m/%d/%Y",
    errors="coerce"
)

print("\n=== DATE ANALYSIS ===")
print("Earliest date:", dates.min())
print("Latest date:", dates.max())
print("Missing or invalid dates:", dates.isna().sum())

print("\nInspection completed!")
