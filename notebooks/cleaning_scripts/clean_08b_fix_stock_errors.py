import pandas as pd

f = r"C:\Users\User\Desktop\major_project\data_cleaned\stock_snapshots_cleaned.xlsx"
df = pd.read_excel(f)

print(f"Before: {len(df)} rows")

# Only drop rows where product could not be parsed at all
# These have NaN Style AND NaN Size — truly blank/footer rows
df = df[df["Style"].notna() & (df["Style"].astype(str).str.strip() != "NAN")]

print(f"After : {len(df)} rows")
print(f"Removed: {99524 - len(df)} rows")

df.to_excel(f, index=False)
print("✅ Done")