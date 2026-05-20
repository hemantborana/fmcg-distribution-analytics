import pandas as pd
import os

BASE         = r"C:\Users\User\Desktop\major_project"
INPUT        = os.path.join(BASE, r"data_raw\sku_master.xlsx")
OUTPUT       = os.path.join(BASE, r"data_cleaned\sku_master_cleaned.xlsx")
STYLE_MAP_F  = os.path.join(BASE, r"data_cleaned\style_code_mapping.xlsx")

MRP_ADJUSTMENT = 20

# ── STEP 1: Load ──────────────────────────────────────────────────────────────
print("STEP 1: Loading sku_master.xlsx...")
df = pd.read_excel(INPUT, dtype={"Barcode": str, "Mat Code": str})
print(f"  ✓ Rows loaded : {len(df)}")
print(f"  ✓ Columns     : {list(df.columns)}\n")

# ── STEP 2: Drop duplicate and redundant columns ──────────────────────────────
print("STEP 2: Removing duplicate and redundant columns...")

# Handle duplicate column names — pandas adds .1 suffix automatically
# Drop second Mat Code and Cat'ry, Description, Stylecol, Color Name, second Style
cols_to_drop = []
seen = {}
final_cols_raw = []
for col in df.columns:
    base = col.replace(".1","").strip()
    if base in seen:
        cols_to_drop.append(col)   # duplicate
    else:
        seen[base] = True
        final_cols_raw.append(col)

# Also drop redundant content columns
for col in ["Description", "Stylecol"]:
    if col in df.columns and col not in cols_to_drop:
        cols_to_drop.append(col)

df.drop(columns=[c for c in cols_to_drop if c in df.columns], inplace=True)

# Clean up column names (remove .1 suffixes if any remain)
df.columns = [c.replace(".1","").strip() for c in df.columns]

# Rename Cat'ry to Category
df.rename(columns={"Cat'ry": "Category", "APEX / Reg": "Product_Tier"}, inplace=True)

print(f"  ✓ Dropped: {cols_to_drop}")
print(f"  ✓ Remaining columns: {list(df.columns)}\n")

# ── STEP 3: Fix Barcode ───────────────────────────────────────────────────────
print("STEP 3: Fixing Barcode...")
def fix_barcode(val):
    if pd.isna(val) or str(val).strip() == "":
        return None
    val_str = str(val).strip()
    if "E" in val_str.upper() or "." in val_str:
        try:
            return str(int(float(val_str)))
        except:
            return val_str
    return val_str

df["Barcode"] = df["Barcode"].apply(fix_barcode)
bad = df[df["Barcode"].apply(lambda x: len(str(x)) != 13 if x else True)].shape[0]
print(f"  {'✓ All barcodes 13 digits' if bad == 0 else f'⚠ {bad} non-13-digit barcodes'}\n")

# ── STEP 4: Fix MRP ───────────────────────────────────────────────────────────
print("STEP 4: Fixing MRP...")
df["MRP"] = pd.to_numeric(df["MRP"].astype(str).str.strip(), errors="coerce")
df["MRP"] = df["MRP"] + MRP_ADJUSTMENT
print(f"  ✓ MRP stripped, converted to numeric, +₹{MRP_ADJUSTMENT} applied")
print(f"  ✓ MRP range: ₹{df['MRP'].min():.0f} – ₹{df['MRP'].max():.0f}\n")

# ── STEP 5: Standardize Style, Color, Size ────────────────────────────────────
print("STEP 5: Standardizing Style, Color, Size...")
df["Style"]       = df["Style"].astype(str).str.strip().str.upper()
df["Color"]       = df["Color"].astype(str).str.strip().str.upper()
df["Color Name"]  = df["Color Name"].astype(str).str.strip().str.title()
df["Size"]        = df["Size"].astype(str).str.strip().str.upper()
df["Category"]     = df["Category"].astype(str).str.strip().str.upper()
df["Product_Tier"] = df["Product_Tier"].astype(str).str.strip().str.upper()
print(f"  ✓ Unique styles   : {df['Style'].nunique()}")
print(f"  ✓ Unique colors   : {df['Color'].nunique()}")
print(f"  ✓ Unique sizes    : {df['Size'].nunique()}")
print(f"  ✓ Categories      : {df['Category'].unique().tolist()}")
print(f"  ✓ Product tiers   : {df['Product_Tier'].unique().tolist()}\n")

# ── STEP 6: Apply style code anonymization ────────────────────────────────────
print("STEP 6: Applying style code anonymization...")
style_map_df = pd.read_excel(STYLE_MAP_F)
style_map    = dict(zip(
    style_map_df["Original_Style"].astype(str).str.strip().str.upper(),
    style_map_df["Anonymized_Style"].astype(str).str.strip()
))

before_styles = df["Style"].nunique()
df["Style"] = df["Style"].map(style_map).fillna(df["Style"])

# Rebuild SKU_Code
df["SKU_Code"] = df["Style"] + "_" + df["Color"] + "_" + df["Size"]

# Also anonymize Mat Code — it's an internal company material code, keep as-is
# but rename clearly
df.rename(columns={"Mat Code": "Mat_Code"}, inplace=True)

print(f"  ✓ Style codes anonymized: {before_styles} styles mapped")
print(f"  ✓ Unique anonymized styles: {df['Style'].nunique()}")
print(f"  ✓ Unique SKU_Codes: {df['SKU_Code'].nunique()}\n")

# ── STEP 7: Remove duplicates ─────────────────────────────────────────────────
print("STEP 7: Checking duplicates...")
dupes = df.duplicated().sum()
if dupes > 0:
    df.drop_duplicates(inplace=True)
    print(f"  ✓ Removed {dupes} duplicate rows")
else:
    print(f"  ✓ No duplicates found")
print()

# ── STEP 8: Final column order and save ──────────────────────────────────────
print("STEP 8: Saving...")
final_cols = [
    "Mat_Code", "Barcode", "Category", "Product_Tier",
    "Style", "Color", "Color Name", "Size", "SKU_Code", "MRP"
]
df = df[[c for c in final_cols if c in df.columns]]
df = df.sort_values(["Style", "Color", "Size"]).reset_index(drop=True)
df.to_excel(OUTPUT, index=False)

# ── SUMMARY ───────────────────────────────────────────────────────────────────
print("\n" + "=" * 55)
print("CLEANING COMPLETE — sku_master")
print("=" * 55)
print(f"  Total SKU entries     : {len(df)}")
print(f"  Unique styles         : {df['Style'].nunique()}")
print(f"  Unique SKU_Codes      : {df['SKU_Code'].nunique()}")
print(f"  Categories            : {df['Category'].value_counts().to_dict()}")
print(f"  Product tiers         : {df['Product_Tier'].value_counts().to_dict()}")
print(f"  MRP range             : ₹{df['MRP'].min():.0f} – ₹{df['MRP'].max():.0f}")
print("=" * 55)
print("\n✅ Saved: data_cleaned\\sku_master_cleaned.xlsx")