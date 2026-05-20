import pandas as pd

df = pd.read_excel(r"C:\Users\User\Desktop\major_project\data_cleaned\sales_billing_data_cleaned.xlsx")

# Just add a firm identifier column — don't remove anything
df["Firm"] = df["Invoice_Number"].astype(str).str.upper().str.startswith("K").map({True: "CURRENT", False: "PREVIOUS"})

print(df.groupby("Firm").agg(
    Rows        = ("Invoice_Number", "count"),
    Invoices    = ("Invoice_Number", "nunique"),
    From        = ("Invoice_Date",   "min"),
    To          = ("Invoice_Date",   "max"),
    Total_Qty   = ("Quantity",       "sum"),
    Total_Value = ("Item_Total",     "sum")
))

df.to_excel(r"C:\Users\User\Desktop\major_project\data_cleaned\sales_billing_data_cleaned.xlsx", index=False)
print("\n✅ Firm column added — no data removed")