import pandas as pd
import os

BASE         = r"C:\Users\User\Desktop\major_project"
INPUT        = os.path.join(BASE, r"data_raw\outlet_master.xlsx")
OUTPUT       = os.path.join(BASE, r"data_cleaned\outlet_master_cleaned.xlsx")
SALES_MAP_F  = os.path.join(BASE, r"data_cleaned\sales_retailer_mapping.xlsx")
SE_MAP_OUT   = os.path.join(BASE, r"data_cleaned\salesman_mapping.xlsx")

# ── STEP 1: Load ──────────────────────────────────────────────────────────────
print("STEP 1: Loading outlet_master.xlsx...")
df = pd.read_excel(INPUT, dtype=str)
print(f"  ✓ Rows loaded : {len(df)}")
print(f"  ✓ Columns     : {list(df.columns)}\n")

# ── STEP 2: Drop sensitive columns ────────────────────────────────────────────
print("STEP 2: Dropping sensitive columns...")
drop_cols = [
    "CREATION", "DB NAME", "DB CODE",
    "LANDLINE NO", "BANK NAME", "IFCCODE", "ACCOUNT NO.",
    "CONTACT PERSON", "CONTACT MOBILE", "CONTACT EMAIL",
    "ADDRESS1", "ADDRESS2", "ADDRESS3",
    "CREATED BY", "MODIFIED BY",
    "ASSET NAME", "BRAND NAME",
    "MERCHANDISER", "CREATED DATE", "MODIFIED DATE"
]
dropped = [c for c in drop_cols if c in df.columns]
df.drop(columns=dropped, inplace=True)
print(f"  ✓ Dropped {len(dropped)} sensitive columns")
print(f"  ✓ Remaining: {list(df.columns)}\n")

# ── STEP 3: Rename columns cleanly ───────────────────────────────────────────
print("STEP 3: Renaming columns...")
df.rename(columns={
    "OUTLET UID"   : "Outlet_UID",
    "OUTLET NAME"  : "Outlet_Name",
    "TYPE1"        : "Outlet_Type",
    "TYPE2"        : "Outlet_Subtype",
    "PROGRAM"      : "Program",
    "BEAT"         : "Beat",
    "SALESMAN NAME": "Salesman_Name",
    "STATE"        : "State",
    "TOWN"         : "Town",
    "PIN CODE"     : "Pin_Code",
    "PAYMENT MODE" : "Payment_Mode",
    "CR. DAYS"     : "Credit_Days",
    "CR. AMOUNT"   : "Credit_Amount",
    "ACTIVE FROM"  : "Active_From",
    "ACTIVE TO"    : "Active_To",
    "WEEKLY OFF"   : "Weekly_Off",
}, inplace=True)
print(f"  ✓ Columns renamed\n")

# ── STEP 4: Normalize Outlet_Name ─────────────────────────────────────────────
print("STEP 4: Normalizing Outlet Name...")
df["Outlet_Name"] = (df["Outlet_Name"].astype(str).str.strip()
                     .str.replace(r'\s+', ' ', regex=True).str.title())

# ── STEP 5: Map Outlet_Name to RETAILER codes using existing sales mapping ────
print("STEP 5: Mapping outlets to RETAILER codes...")
sales_map_df = pd.read_excel(SALES_MAP_F)
retailer_map = dict(zip(
    sales_map_df["Actual Name"].astype(str).str.strip().str.title(),
    sales_map_df["Anonymized Code"].astype(str).str.strip()
))

df["Retailer_Code"] = df["Outlet_Name"].map(retailer_map)
matched   = df["Retailer_Code"].notna().sum()
unmatched = df["Retailer_Code"].isna().sum()
print(f"  ✓ Matched to existing RETAILER codes : {matched} outlets")
print(f"  ⚠ Not in sales/app data              : {unmatched} outlets")

# For unmatched — assign OUTLET_XXX codes
unmatched_names = df[df["Retailer_Code"].isna()]["Outlet_Name"].unique()
outlet_only_map = {
    name: f"OUTLET_{str(i+1).zfill(3)}"
    for i, name in enumerate(sorted(unmatched_names))
}
df["Retailer_Code"] = df.apply(
    lambda row: row["Retailer_Code"] if pd.notna(row["Retailer_Code"])
    else outlet_only_map.get(row["Outlet_Name"], "OUTLET_UNKNOWN"),
    axis=1
)
print(f"  ✓ {len(unmatched_names)} unmatched outlets assigned OUTLET_001 codes\n")

# Drop original outlet name
df.drop(columns=["Outlet_Name"], inplace=True)

# ── STEP 6: Anonymize Salesman Name ──────────────────────────────────────────
print("STEP 6: Anonymizing Salesman Name...")
df["Salesman_Name"] = df["Salesman_Name"].astype(str).str.strip().str.title()
unique_se = sorted(df["Salesman_Name"].dropna().unique())
unique_se = [s for s in unique_se if s.lower() not in ["nan", "", "none"]]
se_map    = {name: f"SE_{str(i+1).zfill(2)}" for i, name in enumerate(unique_se)}

# Save salesman mapping privately
se_map_df = pd.DataFrame(list(se_map.items()), columns=["Actual_Name", "SE_Code"])
se_map_df.to_excel(SE_MAP_OUT, index=False)

df["Salesman_Code"] = df["Salesman_Name"].map(se_map).fillna("SE_UNKNOWN")
df.drop(columns=["Salesman_Name"], inplace=True)
print(f"  ✓ {len(unique_se)} salesmen anonymized → SE_01 to SE_{str(len(unique_se)).zfill(2)}")
print(f"  ✓ Salesman mapping saved: data_cleaned\\salesman_mapping.xlsx\n")

# ── STEP 7: Fix date columns ──────────────────────────────────────────────────
print("STEP 7: Fixing date columns...")
for col in ["Active_From", "Active_To"]:
    df[col] = pd.to_datetime(df[col], dayfirst=True, errors="coerce").dt.date
print(f"  ✓ Active_From and Active_To converted to dates\n")

# ── STEP 8: Add active status column ──────────────────────────────────────────
print("STEP 8: Adding Active_Status column...")
import datetime
today = datetime.date(2026, 3, 31)  # end of our data period
df["Active_Status"] = df["Active_To"].apply(
    lambda x: "INACTIVE" if pd.notna(x) and x <= today else "ACTIVE"
)
active   = (df["Active_Status"] == "ACTIVE").sum()
inactive = (df["Active_Status"] == "INACTIVE").sum()
print(f"  ✓ Active outlets   : {active}")
print(f"  ✓ Inactive outlets : {inactive}\n")

# ── STEP 9: Clean remaining columns ──────────────────────────────────────────
print("STEP 9: Cleaning remaining columns...")
for col in ["Outlet_Type", "Outlet_Subtype", "Program", "Beat",
            "State", "Town", "Payment_Mode", "Weekly_Off"]:
    if col in df.columns:
        df[col] = df[col].astype(str).str.strip().str.upper().replace("NAN", "")

df["Credit_Days"]   = pd.to_numeric(df["Credit_Days"],   errors="coerce").fillna(0).astype(int)
df["Credit_Amount"] = pd.to_numeric(df["Credit_Amount"], errors="coerce").fillna(0)
print(f"  ✓ All remaining columns standardized\n")

# ── STEP 10: Final column order and save ─────────────────────────────────────
print("STEP 10: Saving...")
final_cols = [
    "Outlet_UID", "Retailer_Code", "Salesman_Code",
    "Outlet_Type", "Outlet_Subtype", "Program",
    "Beat", "Town", "State", "Pin_Code",
    "Payment_Mode", "Credit_Days", "Credit_Amount",
    "Active_From", "Active_To", "Active_Status", "Weekly_Off"
]
df = df[[c for c in final_cols if c in df.columns]]
df = df.sort_values("Retailer_Code").reset_index(drop=True)
df.to_excel(OUTPUT, index=False)

# ── SUMMARY ───────────────────────────────────────────────────────────────────
print("=" * 55)
print("CLEANING COMPLETE — outlet_master")
print("=" * 55)
print(f"  Total outlets         : {len(df)}")
print(f"  Active outlets        : {active}")
print(f"  Inactive outlets      : {inactive}")
print(f"  Unique retailer codes : {df['Retailer_Code'].nunique()}")
print(f"  Unique salesmen       : {df['Salesman_Code'].nunique()}")
print(f"  Unique beats          : {df['Beat'].nunique()}")
print(f"  Outlet types          : {df['Outlet_Type'].value_counts().to_dict()}")
print(f"  Payment modes         : {df['Payment_Mode'].value_counts().to_dict()}")
print("=" * 55)
print("\n✅ Saved: data_cleaned\\outlet_master_cleaned.xlsx")
print("🔒 Private: data_cleaned\\salesman_mapping.xlsx  ← DO NOT SUBMIT")