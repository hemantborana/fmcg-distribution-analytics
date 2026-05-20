import pandas as pd
import os

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE           = r"C:\Users\User\Desktop\major_project"
INPUT          = os.path.join(BASE, r"data_raw\sales_billing_data.xlsx")
PARTY_LIST_OUT = os.path.join(BASE, r"data_cleaned\sales_party_name_review.xlsx")

# ── Load ──────────────────────────────────────────────────────────────────────
print("Loading sales_billing_data.xlsx...")
df = pd.read_excel(INPUT)
print(f"  Rows loaded : {len(df)}")
print(f"  Columns     : {list(df.columns)}\n")
print(f"  Date range  : {df['DocumentDate'].min()} → {df['DocumentDate'].max()}\n")

# ── Normalize BuyerTradeName ──────────────────────────────────────────────────
print("Normalizing BuyerTradeName...")
df["BuyerTradeName"] = (df["BuyerTradeName"]
                        .astype(str)
                        .str.strip()
                        .str.replace(r'\s+', ' ', regex=True)   # remove double spaces
                        .str.title())

# ── Build party summary ───────────────────────────────────────────────────────
party_summary = (
    df.groupby("BuyerTradeName")
    .agg(
        Total_Invoices = ("DocumentNumber", "nunique"),
        Total_Rows     = ("BuyerTradeName", "count"),
        Total_Qty      = ("Quantity", "sum"),
        First_Invoice  = ("DocumentDate", "min"),
        Last_Invoice   = ("DocumentDate", "max"),
    )
    .reset_index()
    .sort_values("BuyerTradeName")
    .reset_index(drop=True)
)

# ── Print to screen ───────────────────────────────────────────────────────────
print("\n" + "="*80)
print(f"  ALL UNIQUE BUYER NAMES IN SALES DATA ({len(party_summary)} total)")
print("="*80)
print(f"  {'#':<5} {'Buyer Name':<45} {'Invoices':>8} {'Total Qty':>10}")
print("-"*80)
for i, row in party_summary.iterrows():
    print(f"  {i+1:<5} {row['BuyerTradeName']:<45} {row['Total_Invoices']:>8} {row['Total_Qty']:>10}")
print("="*80)

# ── Save review file ──────────────────────────────────────────────────────────
party_summary["Correct Name"] = party_summary["BuyerTradeName"]
party_summary["Notes"]        = ""
party_summary.to_excel(PARTY_LIST_OUT, index=False)

print(f"\n  ✓ Saved to: data_cleaned\\sales_party_name_review.xlsx")
print(f"\n  → Open this file")
print(f"  → Fix any duplicate/inconsistent names in the 'Correct Name' column")
print(f"  → Also note which names match your app order retailers")
print(f"  → Save and run clean_02b_sales_billing.py\n")