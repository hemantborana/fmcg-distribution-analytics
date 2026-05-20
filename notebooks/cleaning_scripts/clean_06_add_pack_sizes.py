import pandas as pd
import os

BASE          = r"C:\Users\User\Desktop\major_project"
PURCHASE_FILE = os.path.join(BASE, r"data_cleaned\purchase_data_cleaned.xlsx")
SKU_MASTER    = os.path.join(BASE, r"data_cleaned\sku_master_cleaned.xlsx")

# ── Pack size rules ───────────────────────────────────────────────────────────
# Category-based pack sizes
CATEGORY_PACK = {
    "NCP-P05" : 5,
    "NCP-P010": 10,
}

# Style-based pack sizes (anonymized codes)
STYLE_PACK = {
    "TB69": 5,   # was SB06 before anonymization
}

# ── Load ──────────────────────────────────────────────────────────────────────
print("Loading purchase_data_cleaned.xlsx...")
df  = pd.read_excel(PURCHASE_FILE)
sku = pd.read_excel(SKU_MASTER)[["SKU_Code", "Category"]].drop_duplicates()
print(f"  ✓ Purchase rows : {len(df)}")
print(f"  ✓ SKU master    : {len(sku)} entries\n")

# ── Join Category from SKU master ─────────────────────────────────────────────
print("Joining Category from SKU master...")
before_cols = df.columns.tolist()
df = df.merge(sku, on="SKU_Code", how="left")
matched   = df["Category"].notna().sum()
unmatched = df["Category"].isna().sum()
print(f"  ✓ Matched   : {matched} rows")
print(f"  ⚠ Unmatched : {unmatched} rows (NCP or discontinued SKUs — expected)\n")

# ── Assign Pack Size ──────────────────────────────────────────────────────────
print("Assigning pack sizes...")

def get_pack_size(row):
    # Check style first
    if row["Style"] in STYLE_PACK:
        return STYLE_PACK[row["Style"]]
    # Then check category
    cat = row.get("Category", None)
    if pd.notna(cat) and cat in CATEGORY_PACK:
        return CATEGORY_PACK[cat]
    return 1   # default — single piece

df["Pack_Size"]    = df.apply(get_pack_size, axis=1)
df["Actual_Units"] = df["Quantity"] * df["Pack_Size"]

# Summary of pack size distribution
pack_summary = df.groupby("Pack_Size").agg(
    Rows         = ("Quantity", "count"),
    Total_Orders = ("Quantity", "sum"),
    Total_Units  = ("Actual_Units", "sum")
).reset_index()

print(f"  Pack size breakdown:")
for _, row in pack_summary.iterrows():
    label = f"× {int(row['Pack_Size'])}"
    print(f"    {label} | {row['Rows']} rows | "
          f"Ordered qty: {row['Total_Orders']:,} | "
          f"Actual units: {int(row['Total_Units']):,}")

print(f"\n  Total ordered qty   : {df['Quantity'].sum():,}")
print(f"  Total actual units  : {df['Actual_Units'].sum():,}")
diff = df['Actual_Units'].sum() - df['Quantity'].sum()
print(f"  Extra units from packs: {diff:,}\n")

# ── Save ──────────────────────────────────────────────────────────────────────
print("Saving updated purchase_data_cleaned.xlsx...")

# Final column order — insert Pack_Size and Actual_Units after Quantity
cols = df.columns.tolist()
# Remove them first if already there
for c in ["Pack_Size", "Actual_Units", "Category"]:
    if c in cols:
        cols.remove(c)

# Insert after Quantity
qty_idx = cols.index("Quantity")
cols.insert(qty_idx + 1, "Category")
cols.insert(qty_idx + 2, "Pack_Size")
cols.insert(qty_idx + 3, "Actual_Units")

df = df[cols]
df.to_excel(PURCHASE_FILE, index=False)

print("\n" + "=" * 55)
print("PACK SIZE UPDATE COMPLETE — purchase_data")
print("=" * 55)
print(f"  Total rows          : {len(df)}")
print(f"  Columns added       : Category, Pack_Size, Actual_Units")
print(f"  Pack × 1 rows       : {(df['Pack_Size']==1).sum():,}")
print(f"  Pack × 5 rows       : {(df['Pack_Size']==5).sum():,}")
print(f"  Pack × 10 rows      : {(df['Pack_Size']==10).sum():,}")
print(f"  Total ordered qty   : {df['Quantity'].sum():,}")
print(f"  Total actual units  : {df['Actual_Units'].sum():,}")
print("=" * 55)
print("\n✅ Saved: data_cleaned\\purchase_data_cleaned.xlsx")
print("\n⚠  NOTE: Pack_Size and Actual_Units apply to PURCHASE data only.")
print("   Sales and order data always record individual piece quantities.")