import pandas as pd
import numpy as np
import os

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE   = r"C:\Users\User\Desktop\major_project"
INPUT  = os.path.join(BASE, r"data_raw\app_order_data.xlsx")
OUTPUT = os.path.join(BASE, r"data_cleaned\app_order_data_cleaned.xlsx")
PARTY_LIST_OUT  = os.path.join(BASE, r"data_cleaned\party_name_review.xlsx")
MAPPING_OUT     = os.path.join(BASE, r"data_cleaned\retailer_name_mapping.xlsx")

# ── Test / debug order numbers to exclude ─────────────────────────────────────
TEST_ORDERS = {
    "K1","K2","K3","K4","K5","K6","K7",
    "K11","K12","K15","K16","K17","K18","K19","K20",
    "K21","K22","K23","K24","K25","K26"
}

# ── Load ──────────────────────────────────────────────────────────────────────
print("Loading app_order_data.xlsx...")
df = pd.read_excel(INPUT, dtype={"Barcode": str})
print(f"  Rows loaded : {len(df)}")
print(f"  Columns     : {list(df.columns)}\n")

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 1 — Remove test / debug orders
# ═══════════════════════════════════════════════════════════════════════════════
print("STEP 1: Removing test/debug orders...")
df["Order Number"] = df["Order Number"].astype(str).str.strip()
before = len(df)
df = df[~df["Order Number"].isin(TEST_ORDERS)]
removed = before - len(df)
print(f"  ✓ Removed {removed} rows belonging to test orders: {sorted(TEST_ORDERS)}")
print(f"  ✓ Remaining rows: {len(df)}\n")

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 2 — Normalize Party Name (strip + title case)
# ═══════════════════════════════════════════════════════════════════════════════
print("STEP 2: Normalizing Party Name...")
df["Party Name Raw"] = df["Party Name"].astype(str).str.strip()   # keep raw for mapping
df["Party Name"]     = df["Party Name Raw"].str.title()            # Title Case normalize
print(f"  ✓ Party names normalized to Title Case\n")

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 3 — Identify STOCK orders in Party Name
# ═══════════════════════════════════════════════════════════════════════════════
print("STEP 3: Identifying stock orders in Party Name...")
stock_mask = df["Party Name"].str.lower().str.contains("stock", na=False)
stock_orders = df[stock_mask]["Order Number"].unique()
print(f"  ✓ Found {stock_mask.sum()} rows with 'stock' in party name")
print(f"  ✓ Order numbers flagged as stock orders: {sorted(stock_orders)}")

# Tag them with a new column
df["Order Type"] = "RETAILER"
df.loc[stock_mask, "Order Type"] = "STOCK_ORDER"
print(f"  ✓ Tagged with Order Type column: RETAILER / STOCK_ORDER\n")

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 4 — Print ALL unique party names for your review
# ═══════════════════════════════════════════════════════════════════════════════
print("STEP 4: Extracting all unique party names for review...")

party_summary = (
    df.groupby("Party Name")
    .agg(
        Order_Type   = ("Order Type", "first"),
        Total_Orders = ("Order Number", "nunique"),
        Total_Rows   = ("Order Number", "count"),
        Total_Qty    = ("Quantity", "sum") if "Quantity" in df.columns else ("Order Number", "count")
    )
    .reset_index()
    .sort_values("Party Name")
)

print("\n" + "="*70)
print(f"  ALL UNIQUE PARTY NAMES ({len(party_summary)} total)")
print("="*70)
print(f"  {'#':<5} {'Party Name':<40} {'Type':<15} {'Orders'}")
print("-"*70)
for i, row in party_summary.iterrows():
    print(f"  {i+1:<5} {row['Party Name']:<40} {row['Order_Type']:<15} {row['Total_Orders']}")
print("="*70)

# Save party list to Excel for your manual review
party_review_df = party_summary.copy()
party_review_df["Correct Name"] = party_summary["Party Name"]  # you fill this column
party_review_df["Notes"]        = ""
party_review_df.to_excel(PARTY_LIST_OUT, index=False)
print(f"\n  ✓ Party name review file saved to: data_cleaned\\party_name_review.xlsx")
print(f"  → Open this file, check 'Correct Name' column, edit any wrong names, save it")
print(f"  → Then run Part 2 script to apply your corrections\n")

print("="*70)
print("  SCRIPT PAUSED — review party_name_review.xlsx before continuing")
print("  Run clean_01b_apply_mapping.py after you have corrected the names")
print("="*70)