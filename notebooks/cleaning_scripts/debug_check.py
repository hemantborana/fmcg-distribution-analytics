import pandas as pd
df = pd.read_excel(r"C:\Users\User\Desktop\major_project\data_cleaned\stock_snapshots_cleaned.xlsx")
errors = df[df["Style"].isna() | (df["Style"] == "NAN")]
print(errors[["Snapshot_Date","Category","SKU_Code"]].drop_duplicates().head(20))