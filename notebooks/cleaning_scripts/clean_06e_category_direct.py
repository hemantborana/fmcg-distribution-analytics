import pandas as pd, os

BASE          = r"C:\Users\User\Desktop\major_project"
PURCHASE_FILE = os.path.join(BASE, r"data_cleaned\purchase_data_cleaned.xlsx")
SKU_MASTER    = os.path.join(BASE, r"data_cleaned\sku_master_cleaned.xlsx")

df  = pd.read_excel(PURCHASE_FILE)
sku = pd.read_excel(SKU_MASTER)

# One category per style — take first occurrence only
style_cat = (sku[["Style","Category"]]
             .drop_duplicates(subset="Style", keep="first"))
style_map = dict(zip(style_cat["Style"], style_cat["Category"]))

# Map directly — no merge, no row explosion
df["Category"] = df["Style"].map(style_map)

# Insert Category after Quantity
cols = df.columns.tolist()
cols.remove("Category")
cols.insert(cols.index("Quantity") + 1, "Category")
df = df[cols]

df.to_excel(PURCHASE_FILE, index=False)
print(f"✅ Done — {len(df)} rows | Category added cleanly")
print(f"   Matched  : {df['Category'].notna().sum()}")
print(f"   Unmatched: {df['Category'].isna().sum()} (discontinued/NCP — expected)")