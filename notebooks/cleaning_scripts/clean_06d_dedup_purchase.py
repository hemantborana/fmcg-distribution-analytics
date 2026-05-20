import pandas as pd
import os

BASE          = r"C:\Users\User\Desktop\major_project"
PURCHASE_FILE = os.path.join(BASE, r"data_cleaned\purchase_data_cleaned.xlsx")

df = pd.read_excel(PURCHASE_FILE)
print(f"Before: {len(df)} rows")

# Deduplicate — keep first occurrence per invoice line
# Core unique identifier = Invoice_Number + SKU_Code_Raw
df.drop_duplicates(subset=["Invoice_Number", "SKU_Code_Raw"], keep="first", inplace=True)
print(f"After : {len(df)} rows")

df.to_excel(PURCHASE_FILE, index=False)
print("✅ Done")