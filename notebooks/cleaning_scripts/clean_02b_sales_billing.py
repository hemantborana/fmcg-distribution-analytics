import pandas as pd
import numpy as np
import os
import re

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE             = r"C:\Users\User\Desktop\major_project"
INPUT            = os.path.join(BASE, r"data_raw\sales_billing_data.xlsx")
PARTY_REVIEW     = os.path.join(BASE, r"data_cleaned\sales_party_name_review.xlsx")
APP_MAPPING      = os.path.join(BASE, r"data_cleaned\retailer_name_mapping.xlsx")
OUTPUT           = os.path.join(BASE, r"data_cleaned\sales_billing_data_cleaned.xlsx")
SALES_MAPPING    = os.path.join(BASE, r"data_cleaned\sales_retailer_mapping.xlsx")

# ── Load ──────────────────────────────────────────────────────────────────────
print("Loading files...")
df      = pd.read_excel(INPUT)
review  = pd.read_excel(PARTY_REVIEW)
app_map = pd.read_excel(APP_MAPPING)   # actual name → RETAILER_001 from app data cleaning

print(f"  ✓ Sales rows loaded  : {len(df)}")
print(f"  ✓ Party corrections  : {len(review)}")
print()

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 1 — Rename columns clearly
# ═══════════════════════════════════════════════════════════════════════════════
print("STEP 1: Renaming columns...")
df.rename(columns={
    "DocumentNumber"   : "Invoice_Number",
    "DocumentDate"     : "Invoice_Date",
    "DocumentType"     : "Invoice_Type",
    "SupplyType"       : "Supply_Type",
    "BuyerTradeName"   : "Party_Name",
    "BuyerLocation"    : "Location",
    "HSNcode"          : "HSN_Code",
    "UnitPrice"        : "Unit_Price",
    "GrossAmount"      : "Gross_Amount",
    "Taxablevalue"     : "Taxable_Value",
    "GSTRate(%)"       : "GST_Rate_Pct",
    "SgstAmt(Rs)"      : "Item_SGST",     # SGST for this line item
    "CgstAmt(Rs)"      : "Item_CGST",     # CGST for this line item
    "ItemTotal"        : "Item_Total",
    "TotalTaxablevalue": "Invoice_Taxable_Total",
    "SgstAmt"          : "Invoice_SGST",  # SGST for full invoice
    "CgstAmt"          : "Invoice_CGST",  # CGST for full invoice
    "Roundoff"         : "Round_Off",
    "TotalInvoicevalue": "Invoice_Total",
}, inplace=True)
print(f"  ✓ All columns renamed clearly\n")

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 2 — Fix Invoice Date
# ═══════════════════════════════════════════════════════════════════════════════
print("STEP 2: Fixing Invoice Date...")
df["Invoice_Date"] = pd.to_datetime(df["Invoice_Date"], dayfirst=True, errors="coerce")
df["Invoice_Date"] = df["Invoice_Date"].dt.date
print(f"  ✓ Date range: {df['Invoice_Date'].min()} → {df['Invoice_Date'].max()}\n")

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 3 — Extract Style, Color, Size from ProductDescription
# ═══════════════════════════════════════════════════════════════════════════════
print("STEP 3: Extracting Style, Color, Size from ProductDescription...")

def parse_product_description(desc):
    """
    Input  : 'SB06-BRA-NPNW-P1, BLACK, L'
    Output : ('SB06', 'BLACK', 'L')
    Logic  : Split by comma → 3 parts
             Style = first part before first hyphen (e.g. SB06)
             Color = second part stripped
             Size  = third part stripped
    """
    try:
        desc = str(desc).strip()
        parts = desc.split(",")
        if len(parts) < 3:
            return None, None, None
        # Style: everything before the first hyphen in part[0]
        style_full = parts[0].strip()
        style      = style_full.split("-")[0].strip().upper()
        color      = parts[1].strip().upper()
        size        = parts[2].strip().upper()
        return style, color, size
    except:
        return None, None, None

parsed = df["ProductDescription"].apply(
    lambda x: pd.Series(parse_product_description(x),
                        index=["Style", "Color", "Size"])
)
df = pd.concat([df, parsed], axis=1)

# Drop original ProductDescription
df.drop(columns=["ProductDescription"], inplace=True)

# Create SKU_Code for joining
df["SKU_Code"] = df["Style"] + "_" + df["Color"] + "_" + df["Size"]

failed = df["Style"].isna().sum()
print(f"  ✓ Style, Color, Size extracted from ProductDescription")
print(f"  ✓ ProductDescription column deleted")
print(f"  ✓ Unique styles : {df['Style'].nunique()}")
print(f"  ✓ Unique colors : {df['Color'].nunique()}")
print(f"  ✓ Unique sizes  : {df['Size'].nunique()}")
print(f"  ✓ Unique SKUs   : {df['SKU_Code'].nunique()}")
if failed > 0:
    print(f"  ⚠ {failed} rows could not be parsed — check manually")
print()

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 4 — Normalize Party Name and apply corrections
# ═══════════════════════════════════════════════════════════════════════════════
print("STEP 4: Normalizing and correcting Party Names...")

# Build correction map from your review file
df["Party_Name"] = (df["Party_Name"]
                    .astype(str)
                    .str.strip()
                    .str.replace(r'\s+', ' ', regex=True)
                    .str.title())

correction_map = dict(zip(
    review["BuyerTradeName"].astype(str).str.strip(),
    review["Correct Name"].astype(str).str.strip()
))
df["Party_Name"] = df["Party_Name"].map(correction_map).fillna(df["Party_Name"])
print(f"  ✓ Party names corrected\n")

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 5 — Map to same RETAILER_001 codes as app order data
# ═══════════════════════════════════════════════════════════════════════════════
print("STEP 5: Mapping to RETAILER_001 codes (matching app order data)...")

# app_map has columns: Actual Name | Anonymized Code
# Try to match sales party names to app retailer mapping
app_code_map = dict(zip(
    app_map["Actual Name"].astype(str).str.strip().str.title(),
    app_map["Anonymized Code"].astype(str).str.strip()
))

# Assign codes — matched ones get same code as app data
# Unmatched ones (retailers in ERP but not in app) get new codes
matched   = []
unmatched = []
for name in df["Party_Name"].unique():
    if name in app_code_map:
        matched.append(name)
    else:
        unmatched.append(name)

print(f"  ✓ Matched to app retailer codes : {len(matched)} retailers")
print(f"  ⚠ Not in app data (ERP only)    : {len(unmatched)} retailers")
if unmatched:
    print(f"    These retailers appear in billing but not in app orders:")
    for u in sorted(unmatched):
        print(f"    → {u}")

# Give unmatched retailers new codes starting from RETAILER_099 downward
#   so they don't clash with app data codes
erp_only_map = {name: f"ERP_ONLY_{str(i+1).zfill(3)}"
                for i, name in enumerate(sorted(unmatched))}

full_code_map = {**app_code_map, **erp_only_map}
df["Party_Code"] = df["Party_Name"].map(full_code_map)

# Save the sales mapping privately
sales_mapping_df = pd.DataFrame([
    {"Actual Name": k, "Anonymized Code": v, "Source": "APP+ERP" if k in app_code_map else "ERP_ONLY"}
    for k, v in full_code_map.items()
    if k in df["Party_Name"].values
])
sales_mapping_df.to_excel(SALES_MAPPING, index=False)
print(f"  ✓ Mapping saved: data_cleaned\\sales_retailer_mapping.xlsx\n")

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 6 — Drop original Party_Name, keep only code
# ═══════════════════════════════════════════════════════════════════════════════
df.drop(columns=["Party_Name"], inplace=True)

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 7 — Numeric columns
# ═══════════════════════════════════════════════════════════════════════════════
print("STEP 7: Fixing numeric columns...")
numeric_cols = [
    "Quantity", "Unit_Price", "Gross_Amount", "Taxable_Value",
    "GST_Rate_Pct", "Item_SGST", "Item_CGST", "Item_Total",
    "Invoice_Taxable_Total", "Invoice_SGST", "Invoice_CGST",
    "Round_Off", "Invoice_Total"
]
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")
df["Quantity"] = df["Quantity"].fillna(0).astype(int)
print(f"  ✓ All numeric columns confirmed\n")

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 8 — Remove duplicates
# ═══════════════════════════════════════════════════════════════════════════════
print("STEP 8: Checking duplicates...")
dupes = df.duplicated().sum()
if dupes > 0:
    df.drop_duplicates(inplace=True)
    print(f"  ✓ Removed {dupes} duplicate rows")
else:
    print(f"  ✓ No duplicates found")
print()

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 9 — Final column order and save
# ═══════════════════════════════════════════════════════════════════════════════
print("STEP 9: Saving cleaned file...")

final_cols = [
    "Invoice_Date", "Invoice_Number", "Invoice_Type", "Supply_Type",
    "Party_Code", "Location",
    "HSN_Code", "Style", "Color", "Size", "SKU_Code",
    "Quantity", "Unit_Price", "Gross_Amount",
    "Taxable_Value", "GST_Rate_Pct",
    "Item_SGST", "Item_CGST", "Item_Total",
    "Invoice_Taxable_Total", "Invoice_SGST", "Invoice_CGST",
    "Round_Off", "Invoice_Total"
]
df = df[final_cols]
df.to_excel(OUTPUT, index=False)

# ═══════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("CLEANING COMPLETE — sales_billing_data")
print("="*60)
print(f"  Total rows              : {len(df)}")
print(f"  Date range              : {df['Invoice_Date'].min()} → {df['Invoice_Date'].max()}")
print(f"  Unique invoices         : {df['Invoice_Number'].nunique()}")
print(f"  Unique retailers (coded): {df['Party_Code'].nunique()}")
print(f"  Unique styles           : {df['Style'].nunique()}")
print(f"  Unique SKUs             : {df['SKU_Code'].nunique()}")
print(f"  Total qty billed        : {df['Quantity'].sum():,}")
print(f"  Total billed value      : ₹{df['Item_Total'].sum():,.0f}")
print(f"  Total invoice value     : ₹{df['Invoice_Total'].sum():,.0f}")
print("="*60)
print("\n✅ Saved: data_cleaned\\sales_billing_data_cleaned.xlsx")
print("🔒 Private mapping: data_cleaned\\sales_retailer_mapping.xlsx  ← DO NOT SUBMIT")