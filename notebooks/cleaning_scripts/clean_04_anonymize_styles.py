import pandas as pd
import re
import os
import random

BASE    = r"C:\Users\User\Desktop\major_project"
CLEANED = os.path.join(BASE, "data_cleaned")

SALES_FILE    = os.path.join(CLEANED, "sales_billing_data_cleaned.xlsx")
PURCHASE_FILE = os.path.join(CLEANED, "purchase_data_cleaned.xlsx")
ORDERS_FILE   = os.path.join(CLEANED, "app_order_data_cleaned.xlsx")
MAPPING_OUT   = os.path.join(CLEANED, "style_code_mapping.xlsx")

MRP_ADJUSTMENT = 20

PREFIX_MAP = {
    "A" : "D",  "AB": "DB", "BB": "GB", "BR": "HR",
    "CB": "NB", "CH": "NH", "CR": "NR", "CW": "NW",
    "E" : "G",  "EC": "GC", "F" : "H",  "FB": "HB",
    "IB": "KB", "IO": "KO", "IP": "KP", "MB": "RB",
    "MH": "RH", "MS": "RS", "MT": "RT", "P" : "Q",
    "PB": "QB", "PH": "QH", "PP": "QQ", "SB": "TB",
    "TS": "VS",
}

# ── STEP 1: Load ──────────────────────────────────────────────────────────────
print("STEP 1: Loading cleaned files...")
sales    = pd.read_excel(SALES_FILE)
purchase = pd.read_excel(PURCHASE_FILE)
orders   = pd.read_excel(ORDERS_FILE)
print(f"  ✓ Sales: {len(sales)} | Purchase: {len(purchase)} | Orders: {len(orders)}\n")

# ── STEP 2: Collect all unique styles ────────────────────────────────────────
print("STEP 2: Collecting all unique style codes...")
all_styles = set()
for df in [sales, purchase, orders]:
    if "Style" in df.columns:
        all_styles.update(df["Style"].dropna().astype(str).str.strip().str.upper().unique())
all_styles = sorted(all_styles)
print(f"  ✓ Total unique styles: {len(all_styles)}\n")

# ── STEP 3: Parse and group by prefix ────────────────────────────────────────
print("STEP 3: Grouping styles by prefix...")

def split_style(code):
    match = re.match(r'^([A-Za-z]+)(\d+)$', str(code).strip())
    if match:
        return match.group(1).upper(), match.group(2)
    return None, None

prefix_groups = {}
unparseable   = []
for style in all_styles:
    prefix, number = split_style(style)
    if prefix and number:
        prefix_groups.setdefault(prefix, []).append((style, number))
    else:
        unparseable.append(style)

for pfx, items in sorted(prefix_groups.items()):
    print(f"  {pfx:<6} → {PREFIX_MAP.get(pfx, pfx):<6} | {len(items)} styles")
if unparseable:
    print(f"  ⚠ Unparseable: {unparseable}")
print()

# ── STEP 4: Generate unique shuffled numbers per prefix group ─────────────────
print("STEP 4: Generating anonymized style codes...")
random.seed(42)
style_map = {}

for prefix, items in prefix_groups.items():
    new_prefix     = PREFIX_MAP.get(prefix, prefix)
    original_codes = [item[0] for item in items]
    num_digits     = max(len(item[1]) for item in items)
    count          = len(original_codes)
    max_possible   = 10 ** num_digits

    # Sample unique random numbers for this prefix group
    pool = random.sample(range(1, max_possible), count)

    for original, new_num in zip(original_codes, pool):
        style_map[original] = new_prefix + str(new_num).zfill(num_digits)

for i, style in enumerate(unparseable):
    style_map[style] = f"XX{str(i+1).zfill(3)}"

print(f"  ✓ {len(style_map)} unique mappings generated\n")

# ── STEP 5: Save mapping + print full old → new list ─────────────────────────
print("STEP 5: Saving mapping file and printing full list...")

mapping_rows = []
for orig in sorted(style_map.keys()):
    prefix, number = split_style(orig)
    mapping_rows.append({
        "Original_Style"  : orig,
        "Anonymized_Style": style_map[orig],
    })

mapping_df = pd.DataFrame(mapping_rows).sort_values("Original_Style").reset_index(drop=True)
mapping_df.to_excel(MAPPING_OUT, index=False)

print("\n" + "=" * 40)
print(f"  {'Original':<15} → {'Anonymized'}")
print("=" * 40)
for _, row in mapping_df.iterrows():
    print(f"  {row['Original_Style']:<15} → {row['Anonymized_Style']}")
print("=" * 40)
print(f"\n  ✓ Saved: data_cleaned\\style_code_mapping.xlsx")
print(f"  🔒 DO NOT SUBMIT\n")

# ── STEP 6: Apply to SALES ────────────────────────────────────────────────────
print("STEP 6: Updating sales file...")
sales["Style"]    = sales["Style"].astype(str).str.strip().str.upper().map(style_map).fillna(sales["Style"])
sales["SKU_Code"] = sales["Style"] + "_" + sales["Color"] + "_" + sales["Size"]
sales.to_excel(SALES_FILE, index=False)
print(f"  ✓ Done — no MRP in sales file\n")

# ── STEP 7: Apply to PURCHASE ─────────────────────────────────────────────────
print("STEP 7: Updating purchase file...")
purchase["Style"]    = purchase["Style"].astype(str).str.strip().str.upper().map(style_map).fillna(purchase["Style"])
purchase["SKU_Code"] = purchase["Style"] + "_" + purchase["Color"] + "_" + purchase["Size"]
if "MRP" in purchase.columns:
    purchase["MRP"] = pd.to_numeric(purchase["MRP"], errors="coerce") + MRP_ADJUSTMENT
    print(f"  ✓ MRP +₹{MRP_ADJUSTMENT} applied | Unit_Rate unchanged")
purchase.to_excel(PURCHASE_FILE, index=False)
print(f"  ✓ Done\n")

# ── STEP 8: Apply to ORDERS ───────────────────────────────────────────────────
print("STEP 8: Updating orders file...")
orders["Style"]    = orders["Style"].astype(str).str.strip().str.upper().map(style_map).fillna(orders["Style"])
orders["SKU_Code"] = orders["Style"] + "_" + orders["Color"] + "_" + orders["Size"]
if "MRP" in orders.columns:
    orders["MRP"] = pd.to_numeric(orders["MRP"], errors="coerce") + MRP_ADJUSTMENT
    print(f"  ✓ MRP +₹{MRP_ADJUSTMENT} applied")
if "Item_Total" in orders.columns:
    orders["Item_Total"] = orders["Quantity"] * orders["MRP"]
    print(f"  ✓ Item_Total recalculated")
orders.to_excel(ORDERS_FILE, index=False)
print(f"  ✓ Done\n")

# ── SUMMARY ───────────────────────────────────────────────────────────────────
print("=" * 60)
print("ANONYMIZATION COMPLETE")
print("=" * 60)
print(f"  Styles anonymized  : {len(style_map)}")
print(f"  Prefix changes     : {len(PREFIX_MAP)} prefix groups remapped")
print(f"  MRP adjustment     : +₹{MRP_ADJUSTMENT} on purchase and orders")
print(f"  Files updated      : 3")
print(f"\n  ✅ Updated:")
print(f"     sales_billing_data_cleaned.xlsx")
print(f"     purchase_data_cleaned.xlsx")
print(f"     app_order_data_cleaned.xlsx")
print(f"\n  🔒 Never submit:")
print(f"     style_code_mapping.xlsx")
print(f"     retailer_name_mapping.xlsx")
print(f"     sales_retailer_mapping.xlsx")
print("=" * 60)