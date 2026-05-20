import pandas as pd
import numpy as np
import os

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE          = r"C:\Users\User\Desktop\major_project"
INPUT         = os.path.join(BASE, r"data_raw\app_order_data.xlsx")
PARTY_REVIEW  = os.path.join(BASE, r"data_cleaned\party_name_review.xlsx")
OUTPUT        = os.path.join(BASE, r"data_cleaned\app_order_data_cleaned.xlsx")
MAPPING_OUT   = os.path.join(BASE, r"data_cleaned\retailer_name_mapping.xlsx")

TEST_ORDERS = {
    "K1","K2","K3","K4","K5","K6","K7",
    "K11","K12","K15","K16","K17","K18","K19","K20",
    "K21","K22","K23","K24","K25","K26"
}

# ── Load raw data ─────────────────────────────────────────────────────────────
print("Loading app_order_data.xlsx...")
df = pd.read_excel(INPUT, dtype={"Barcode": str})

# ── Load your corrected party name review file ────────────────────────────────
print("Loading your corrected party_name_review.xlsx...")
review = pd.read_excel(PARTY_REVIEW)

# Build correction map: normalized name → your corrected name
correction_map = dict(zip(
    review["Party Name"].astype(str).str.strip(),
    review["Correct Name"].astype(str).str.strip()
))
print(f"  ✓ Loaded {len(correction_map)} party name mappings\n")

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 1 — Remove test orders
# ═══════════════════════════════════════════════════════════════════════════════
print("STEP 1: Removing test/debug orders...")
df["Order Number"] = df["Order Number"].astype(str).str.strip()
before = len(df)
df = df[~df["Order Number"].isin(TEST_ORDERS)]
print(f"  ✓ Removed {before - len(df)} test rows | Remaining: {len(df)}\n")

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 2 — Normalize and apply party name corrections
# ═══════════════════════════════════════════════════════════════════════════════
print("STEP 2: Applying party name corrections...")
df["Party Name"] = (df["Party Name"].astype(str).str.strip().str.title()
                    .map(correction_map)
                    .fillna(df["Party Name"].astype(str).str.strip().str.title()))

# Tag stock orders
stock_mask = df["Party Name"].str.lower().str.contains("stock", na=False)
df["Order Type"] = "RETAILER"
df.loc[stock_mask, "Order Type"] = "STOCK_ORDER"
print(f"  ✓ Party names corrected and applied")
print(f"  ✓ Stock orders tagged: {stock_mask.sum()} rows\n")

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 3 — Fix Timestamp
# ═══════════════════════════════════════════════════════════════════════════════
print("STEP 3: Fixing Timestamp...")
df["Timestamp"] = pd.to_datetime(df["Timestamp"], utc=True, errors="coerce")
df.insert(df.columns.get_loc("Timestamp"),   "Order Date", df["Timestamp"].dt.date)
df.insert(df.columns.get_loc("Timestamp")+1, "Order Time", df["Timestamp"].dt.strftime("%H:%M:%S"))
df.drop(columns=["Timestamp"], inplace=True)
print(f"  ✓ Date range: {df['Order Date'].min()} → {df['Order Date'].max()}\n")

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 4 — Fix Color
# ═══════════════════════════════════════════════════════════════════════════════
print("STEP 4: Fixing Color column...")
df["Color"] = df["Color"].astype(str).str.strip().str.upper()
print(f"  ✓ Unique colors: {df['Color'].nunique()}\n")

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 5 — Fix Barcode
# ═══════════════════════════════════════════════════════════════════════════════
print("STEP 5: Fixing Barcode...")

def fix_barcode(val):
    if pd.isna(val) or str(val).strip() == "":
        return None
    val_str = str(val).strip()
    if "E" in val_str.upper():
        try:
            return str(int(float(val_str)))
        except:
            return val_str
    if "." in val_str:
        try:
            return str(int(float(val_str)))
        except:
            return val_str
    return val_str

df["Barcode"] = df["Barcode"].apply(fix_barcode)
bad_barcodes = df[df["Barcode"].apply(lambda x: len(str(x)) != 13 if x else True)]
if len(bad_barcodes) > 0:
    print(f"  ⚠ {len(bad_barcodes)} rows with non-13-digit barcodes (check manually)")
else:
    print(f"  ✓ All barcodes 13 digits")
print()

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 6 — Anonymize Order Note
# ═══════════════════════════════════════════════════════════════════════════════
print("STEP 6: Categorizing Order Notes...")

def categorize_note(note):
    if pd.isna(note) or str(note).strip() == "":
        return "STANDARD"
    n = str(note).lower()
    if "hold"    in n: return "HOLD_ORDER"
    if "fragile" in n or "handle with care" in n: return "FRAGILE_HANDLING"
    if "urgent"  in n or "asap" in n: return "URGENT"
    if "call"    in n: return "CALL_BEFORE_DISPATCH"
    if "partial" in n: return "PARTIAL_DELIVERY"
    return "SPECIAL_INSTRUCTION"

df["Order Note"] = df["Order Note"].apply(categorize_note)
print(f"  ✓ Note categories: {df['Order Note'].value_counts().to_dict()}\n")

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 7 — Standardize Style and Size
# ═══════════════════════════════════════════════════════════════════════════════
print("STEP 7: Standardizing Style, Color, Size...")
df["Style"] = df["Style"].astype(str).str.strip().str.upper()
df["Size"]  = df["Size"].astype(str).str.strip().str.upper()
print(f"  ✓ Unique styles: {df['Style'].nunique()} | Unique sizes: {df['Size'].nunique()}\n")

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 8 — Numeric columns
# ═══════════════════════════════════════════════════════════════════════════════
print("STEP 8: Fixing numeric columns...")
df["Quantity"]   = pd.to_numeric(df["Quantity"],   errors="coerce").fillna(0).astype(int)
df["MRP"]        = pd.to_numeric(df["MRP"],        errors="coerce")
df["Item Total"] = pd.to_numeric(df["Item Total"], errors="coerce")
print(f"  ✓ Quantity, MRP, Item Total confirmed\n")

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 9 — Create SKU_Code
# ═══════════════════════════════════════════════════════════════════════════════
print("STEP 9: Creating SKU_Code...")
df["SKU_Code"] = df["Style"] + "_" + df["Color"] + "_" + df["Size"]
print(f"  ✓ Unique SKUs: {df['SKU_Code'].nunique()}\n")

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 10 — Anonymize Party Name → RETAILER_001 codes + save private mapping
# ═══════════════════════════════════════════════════════════════════════════════
print("STEP 10: Creating anonymized retailer codes...")
retailer_names = sorted(df[df["Order Type"] == "RETAILER"]["Party Name"].dropna().unique())
stock_names    = sorted(df[df["Order Type"] == "STOCK_ORDER"]["Party Name"].dropna().unique())

retailer_code_map = {name: f"RETAILER_{str(i+1).zfill(3)}"
                     for i, name in enumerate(retailer_names)}
stock_code_map    = {name: f"STOCK_{str(i+1).zfill(3)}"
                     for i, name in enumerate(stock_names)}

full_map = {**retailer_code_map, **stock_code_map}

# Save private mapping
mapping_df = pd.DataFrame(list(full_map.items()),
                           columns=["Actual Name", "Anonymized Code"])
mapping_df.to_excel(MAPPING_OUT, index=False)

df["Party Name"] = df["Party Name"].map(full_map).fillna(df["Party Name"])
print(f"  ✓ {len(retailer_names)} retailers → RETAILER_001 to RETAILER_{str(len(retailer_names)).zfill(3)}")
print(f"  ✓ {len(stock_names)} stock entries → STOCK_001 etc.")
print(f"  ✓ Private mapping saved: data_cleaned\\retailer_name_mapping.xlsx\n")

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 11 — Remove duplicates, final column order, save
# ═══════════════════════════════════════════════════════════════════════════════
print("STEP 11: Final cleanup and saving...")
dupes = df.duplicated().sum()
if dupes > 0:
    df.drop_duplicates(inplace=True)
    print(f"  ✓ Removed {dupes} duplicate rows")

final_cols = [
    "Order Number", "Order Date", "Order Time", "Order Type",
    "Party Name", "Order Note",
    "Style", "Color", "Size", "SKU_Code",
    "Barcode", "Quantity", "MRP", "Item Total"
]
df = df[final_cols]
df.to_excel(OUTPUT, index=False)

# ═══════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("CLEANING COMPLETE — app_order_data")
print("="*60)
print(f"  Total rows            : {len(df)}")
print(f"  Date range            : {df['Order Date'].min()} → {df['Order Date'].max()}")
print(f"  Unique order numbers  : {df['Order Number'].nunique()}")
print(f"  Retailer orders (rows): {(df['Order Type']=='RETAILER').sum()}")
print(f"  Stock orders (rows)   : {(df['Order Type']=='STOCK_ORDER').sum()}")
print(f"  Unique retailer codes : {df[df['Order Type']=='RETAILER']['Party Name'].nunique()}")
print(f"  Unique SKUs           : {df['SKU_Code'].nunique()}")
print(f"  Unique styles         : {df['Style'].nunique()}")
print(f"  Total qty ordered     : {df['Quantity'].sum():,}")
print(f"  Total order value     : ₹{df['Item Total'].sum():,.0f}")
print("="*60)
print("\n✅ Saved: data_cleaned\\app_order_data_cleaned.xlsx")
print("🔒 Private mapping: data_cleaned\\retailer_name_mapping.xlsx  ← DO NOT SUBMIT")