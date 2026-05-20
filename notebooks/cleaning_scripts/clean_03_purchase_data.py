import pandas as pd
import os

BASE    = r"C:\Users\User\Desktop\major_project"
PUR_DIR = os.path.join(BASE, r"data_raw\purchase_files")
OUTPUT  = os.path.join(BASE, r"data_cleaned\purchase_data_cleaned.xlsx")

FILES = {
    "FY2023_24": os.path.join(PUR_DIR, "purchase_FY2023_24.xlsx"),
    "FY2024_25": os.path.join(PUR_DIR, "purchase_FY2024_25.xlsx"),
    "FY2025_26": os.path.join(PUR_DIR, "purchase_FY2025_26.xlsx"),
}

print("STEP 1: Loading all purchase files...")
frames = []
for fy, path in FILES.items():
    temp = pd.read_excel(path, dtype={"EAN CODE": str, "SKU Code": str})
    temp["FY"] = fy
    frames.append(temp)
    print(f"  ✓ {fy}: {len(temp)} rows")
df = pd.concat(frames, ignore_index=True)
print(f"  ✓ Combined total: {len(df)} rows\n")

print("STEP 2: Renaming columns...")
df.rename(columns={
    "Inv Date": "Invoice_Date", "Inv No": "Invoice_Number",
    "Bill No": "Bill_Number", "Depo GST No": "Depo_GST",
    "Supplier Code": "Supplier_Code", "Supplier Name": "Supplier_Name",
    "SKU Code": "SKU_Code_Raw", "SKU Name": "SKU_Name",
    "HSN Code": "HSN_Code", "EAN CODE": "EAN_Code",
    "Qty": "Quantity", "Rate": "Unit_Rate", "MRP": "MRP",
    "Amount": "Item_Amount", "Disc": "Discount",
    "Taxable Amount": "Taxable_Amount",
    "IGST %": "IGST_Pct", "IGST Amt": "IGST_Amt",
    "CGST %": "CGST_Pct", "CGST Amt": "CGST_Amt",
    "SGST %": "SGST_Pct", "SGST Amt": "SGST_Amt",
    "CESS %": "CESS_Pct", "CESS Amt": "CESS_Amt",
    "Net Amount": "Invoice_Net_Total",
}, inplace=True)
print(f"  ✓ Columns renamed\n")

print("STEP 3: Dropping sensitive columns...")
df.drop(columns=[c for c in ["Bill_Number","Depo_GST","Supplier_Code"] if c in df.columns], inplace=True)
df["Supplier_Name"] = "Brand Principal"
print(f"  ✓ Sensitive columns dropped | Supplier masked\n")

print("STEP 4: Fixing Invoice Date...")
df["Invoice_Date"] = pd.to_datetime(df["Invoice_Date"], dayfirst=True, errors="coerce")
bad_dates = df["Invoice_Date"].isna().sum()
if bad_dates > 0:
    print(f"  ⚠ {bad_dates} rows with invalid/blank dates — showing them:")
    print(df[df["Invoice_Date"].isna()][["FY","Invoice_Number","SKU_Code_Raw"]].to_string())
    df.dropna(subset=["Invoice_Date"], inplace=True)
    print(f"  ✓ Dropped {bad_dates} bad date rows")
df["Invoice_Date"] = df["Invoice_Date"].dt.date
print(f"  ✓ Date range: {df['Invoice_Date'].min()} → {df['Invoice_Date'].max()}\n")

print("STEP 5: Extracting Style, Color, Size from SKU Name...")
def parse_sku_name(desc):
    try:
        parts = str(desc).strip().split(",")
        if len(parts) < 3:
            return None, None, None
        style = parts[0].strip().split("-")[0].strip().upper()
        color = parts[1].strip().upper()
        size  = parts[2].strip().upper()
        return style, color, size
    except:
        return None, None, None

parsed = df["SKU_Name"].apply(lambda x: pd.Series(parse_sku_name(x), index=["Style","Color","Size"]))
df = pd.concat([df, parsed], axis=1)
df.drop(columns=["SKU_Name"], inplace=True)
df["SKU_Code"] = df["Style"] + "_" + df["Color"] + "_" + df["Size"]
failed = df["Style"].isna().sum()
print(f"  ✓ Unique styles: {df['Style'].nunique()} | Colors: {df['Color'].nunique()} | Sizes: {df['Size'].nunique()}")
print(f"  ✓ Unique SKUs  : {df['SKU_Code'].nunique()}")
if failed > 0:
    print(f"  ⚠ {failed} rows could not be parsed")
print()

print("STEP 6: Fixing EAN Code...")
def fix_ean(val):
    if pd.isna(val) or str(val).strip() == "":
        return None
    val_str = str(val).strip()
    if "E" in val_str.upper() or "." in val_str:
        try:
            return str(int(float(val_str)))
        except:
            return val_str
    return val_str
df["EAN_Code"] = df["EAN_Code"].apply(fix_ean)
bad_ean = df[df["EAN_Code"].apply(lambda x: len(str(x)) != 13 if x else True)].shape[0]
print(f"  {'✓ All EAN codes 13 digits' if bad_ean == 0 else f'⚠ {bad_ean} non-13-digit EAN codes'}\n")

print("STEP 7: Fixing numeric columns...")
for col in ["Quantity","Unit_Rate","MRP","Item_Amount","Discount","Taxable_Amount",
            "IGST_Pct","IGST_Amt","CGST_Pct","CGST_Amt","SGST_Pct","SGST_Amt",
            "CESS_Pct","CESS_Amt","Invoice_Net_Total"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
df["Quantity"] = df["Quantity"].fillna(0).astype(int)
print(f"  ✓ All numeric columns confirmed\n")

print("STEP 8: Checking duplicates...")
dupes = df.duplicated().sum()
if dupes > 0:
    df.drop_duplicates(inplace=True)
    print(f"  ✓ Removed {dupes} duplicate rows")
else:
    print(f"  ✓ No duplicates found")
print()

print("STEP 9: Saving...")
final_cols = [
    "FY","Invoice_Date","Invoice_Number","Supplier_Name",
    "SKU_Code_Raw","EAN_Code","Style","Color","Size","SKU_Code",
    "HSN_Code","Quantity","Unit_Rate","MRP","Item_Amount","Discount",
    "Taxable_Amount","IGST_Pct","IGST_Amt","CGST_Pct","CGST_Amt",
    "SGST_Pct","SGST_Amt","CESS_Pct","CESS_Amt","Invoice_Net_Total"
]
df = df[[c for c in final_cols if c in df.columns]]
df = df.sort_values(["Invoice_Date","Invoice_Number"]).reset_index(drop=True)
df.to_excel(OUTPUT, index=False)

print("\n" + "="*60)
print("CLEANING COMPLETE — purchase_data (all 3 FY combined)")
print("="*60)
print(f"  Total rows            : {len(df)}")
print(f"  Date range            : {df['Invoice_Date'].min()} → {df['Invoice_Date'].max()}")
print(f"  Unique invoices       : {df['Invoice_Number'].nunique()}")
print(f"  Unique SKUs purchased : {df['SKU_Code'].nunique()}")
print(f"  Unique styles         : {df['Style'].nunique()}")
print(f"\n  FY-wise breakdown:")
for fy_name, row in df.groupby("FY").agg(
    Rows=("Invoice_Number","count"),
    Invoices=("Invoice_Number","nunique"),
    Qty=("Quantity","sum"),
    Amt=("Item_Amount","sum")
).iterrows():
    print(f"    {fy_name}: {row['Rows']} rows | {row['Invoices']} invoices | Qty: {row['Qty']:,} | ₹{row['Amt']:,.0f}")
print(f"\n  Total qty purchased   : {df['Quantity'].sum():,}")
print(f"  Total purchase value  : ₹{df['Item_Amount'].sum():,.0f}")
print("="*60)
print("\n✅ Saved: data_cleaned\\purchase_data_cleaned.xlsx")