import pandas as pd
import os

BASE          = r"C:\Users\User\Desktop\major_project"
PURCHASE_FILE = os.path.join(BASE, r"data_cleaned\purchase_data_cleaned.xlsx")
SKU_MASTER    = os.path.join(BASE, r"data_cleaned\sku_master_cleaned.xlsx")

print("Loading files...")
df  = pd.read_excel(PURCHASE_FILE)
sku = pd.read_excel(SKU_MASTER)
print(f"  ✓ Purchase rows before fix : {len(df)}")

# ── Find which SKU_Codes have multiple categories in master ───────────────────
sku_cat = sku[["SKU_Code","Category"]].drop_duplicates()
dup_skus = sku_cat[sku_cat.duplicated("SKU_Code", keep=False)]
if len(dup_skus) > 0:
    print(f"\n  ⚠ SKU_Codes with multiple categories in master:")
    print(dup_skus.sort_values("SKU_Code").to_string(index=False))

# ── Fix: drop Category from purchase, re-join using Style only ───────────────
# Use Style → Category mapping (first occurrence per style wins)
style_cat = sku[["Style","Category"]].drop_duplicates(subset="Style", keep="first")
style_map  = dict(zip(style_cat["Style"], style_cat["Category"]))

# Drop existing Category column and re-assign from style map
df.drop(columns=["Category"], inplace=True)
df["Category"] = df["Style"].map(style_map)

# Verify row count unchanged
print(f"\n  ✓ Purchase rows after fix  : {len(df)}")
print(f"  ✓ Category matched         : {df['Category'].notna().sum()} rows")
print(f"  ⚠ Category unmatched       : {df['Category'].isna().sum()} rows (discontinued/NCP)")

# ── Reorder columns ───────────────────────────────────────────────────────────
cols = df.columns.tolist()
cols.remove("Category")
qty_idx = cols.index("Quantity")
cols.insert(qty_idx + 1, "Category")
df = df[cols]

df.to_excel(PURCHASE_FILE, index=False)

print(f"\n✅ Fixed — rows restored to {len(df)}")
print(f"   Columns: {df.columns.tolist()}")