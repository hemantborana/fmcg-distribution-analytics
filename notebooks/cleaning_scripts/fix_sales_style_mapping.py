import pandas as pd
import os

BASE         = r"C:\Users\User\Desktop\major_project"
CLEANED      = os.path.join(BASE, "data_cleaned")
SALES_FILE   = os.path.join(CLEANED, "sales_billing_data_cleaned.xlsx")
MAPPING_FILE = os.path.join(CLEANED, "style_code_mapping.xlsx")

MRP_ADJUSTMENT = 20

# ── Load existing mapping — DO NOT REGENERATE ─────────────────────────────────
print("Loading existing style mapping...")
mapping_df = pd.read_excel(MAPPING_FILE)
style_map  = dict(zip(
    mapping_df["Original_Style"].astype(str).str.strip().str.upper(),
    mapping_df["Anonymized_Style"].astype(str).str.strip()
))
print(f"  ✓ {len(style_map)} mappings loaded from style_code_mapping.xlsx")

# ── Load restored sales file ──────────────────────────────────────────────────
print("\nLoading restored sales file...")
sales = pd.read_excel(SALES_FILE)
print(f"  ✓ {len(sales)} rows loaded")
print(f"  Sample styles before: {sales['Style'].head(5).tolist()}")

# ── Check if styles are already anonymized or still original ──────────────────
import re
original_pattern = re.compile(
    r'^(A|E|F|SB|MH|MB|IP|IB|IO|CB|CH|CR|CW|AB|BB|BR|PP|PH|PB|P|TS)\d+$'
)
already_anonymized = sales["Style"].dropna().apply(
    lambda x: not bool(original_pattern.match(str(x)))
).sum()
print(f"\n  Already anonymized styles: {already_anonymized}")
print(f"  Original style codes     : {len(sales) - already_anonymized}")

if already_anonymized > len(sales) * 0.5:
    print("\n  ⚠ Sales file appears already anonymized.")
    print("  Please re-run clean_02b and clean_02c first, then run this script.")
    exit()

# ── Apply mapping ONCE — no loop, no regeneration ────────────────────────────
print("\nApplying style mapping to sales data (single pass)...")
sales["Style"] = (sales["Style"].astype(str).str.strip().str.upper()
                  .map(style_map).fillna(sales["Style"]))

# Rebuild SKU_Code
sales["SKU_Code"] = sales["Style"] + "_" + sales["Color"] + "_" + sales["Size"]

print(f"  ✓ Style codes mapped")
print(f"  Sample styles after: {sales['Style'].head(5).tolist()}")
print(f"  Unique styles      : {sales['Style'].nunique()}")
print(f"  Unique SKU_Codes   : {sales['SKU_Code'].nunique()}")

# ── Save ──────────────────────────────────────────────────────────────────────
sales.to_excel(SALES_FILE, index=False)
print(f"\n✅ Saved: sales_billing_data_cleaned.xlsx")

# ── Verify against purchase data ──────────────────────────────────────────────
print("\nVerifying against purchase data...")
purchase = pd.read_excel(os.path.join(CLEANED, "purchase_data_cleaned.xlsx"))

sales_styles    = set(sales["Style"].dropna().unique())
purchase_styles = set(purchase["Style"].dropna().unique())
common          = sales_styles & purchase_styles

print(f"  Sales unique styles    : {len(sales_styles)}")
print(f"  Purchase unique styles : {len(purchase_styles)}")
print(f"  Common styles          : {len(common)}")
print(f"  Overlap rate           : {len(common)/len(sales_styles)*100:.1f}%")

# SKU_Code overlap
sales_skus    = set(sales["SKU_Code"].dropna().unique())
purchase_skus = set(purchase["SKU_Code"].dropna().unique())
sku_overlap   = sales_skus & purchase_skus
print(f"\n  Sales unique SKU_Codes    : {len(sales_skus)}")
print(f"  Purchase unique SKU_Codes : {len(purchase_skus)}")
print(f"  Common SKU_Codes          : {len(sku_overlap)}")
print(f"  SKU overlap rate          : {len(sku_overlap)/len(sales_skus)*100:.1f}%")