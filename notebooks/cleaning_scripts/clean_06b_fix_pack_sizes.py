import pandas as pd
import os

BASE          = r"C:\Users\User\Desktop\major_project"
PURCHASE_FILE = os.path.join(BASE, r"data_cleaned\purchase_data_cleaned.xlsx")

df = pd.read_excel(PURCHASE_FILE)

# Drop pack size columns — not applicable, billing is per piece
df.drop(columns=["Pack_Size", "Actual_Units"], inplace=True)

df.to_excel(PURCHASE_FILE, index=False)

print(f"✅ Done — Pack_Size and Actual_Units removed")
print(f"   Category column kept for grouping analysis")
print(f"   Remaining columns: {df.columns.tolist()}")
print(f"   Total rows: {len(df)}")