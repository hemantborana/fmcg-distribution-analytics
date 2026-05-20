import pandas as pd
import os

BASE     = r"C:\Users\User\Desktop\major_project"
CLEANED  = os.path.join(BASE, "data_cleaned")

sales    = pd.read_excel(os.path.join(CLEANED, "sales_billing_data_cleaned.xlsx"))
purchase = pd.read_excel(os.path.join(CLEANED, "purchase_data_cleaned.xlsx"))
orders   = pd.read_excel(os.path.join(CLEANED, "app_order_data_cleaned.xlsx"))
sku      = pd.read_excel(os.path.join(CLEANED, "sku_master_cleaned.xlsx"))

sales_styles    = set(sales["Style"].dropna().unique())
purchase_styles = set(purchase["Style"].dropna().unique())
order_styles    = set(orders["Style"].dropna().unique())
sku_styles      = set(sku["Style"].dropna().unique())

print("=" * 55)
print("STYLE CODE CONSISTENCY CHECK")
print("=" * 55)
print(f"  Sales    unique styles : {len(sales_styles)}")
print(f"  Purchase unique styles : {len(purchase_styles)}")
print(f"  Orders   unique styles : {len(order_styles)}")
print(f"  SKU Master styles      : {len(sku_styles)}")

# Styles in sales but not in SKU master
s_not_sku = sales_styles - sku_styles
p_not_sku = purchase_styles - sku_styles
o_not_sku = order_styles - sku_styles

print(f"\n  Styles in sales NOT in SKU master    : {len(s_not_sku)}")
print(f"  Styles in purchase NOT in SKU master : {len(p_not_sku)}")
print(f"  Styles in orders NOT in SKU master   : {len(o_not_sku)}")

# Check if any raw brand codes leaked through (A, E, F, SB prefixes)
import re
def has_original_prefix(style):
    return bool(re.match(r'^(A|E|F|SB|MH|MB|IP|IB|IO|CB|CH|CR|CW|AB|BB|BR|PP|PH|PB|P|TS)\d+$', str(style)))

for name, styles in [("Sales", sales_styles), ("Purchase", purchase_styles),
                      ("Orders", order_styles), ("SKU Master", sku_styles)]:
    leaked = [s for s in styles if has_original_prefix(s)]
    if leaked:
        print(f"\n  ⚠ ORIGINAL CODES FOUND IN {name}: {sorted(leaked)[:10]}")
    else:
        print(f"  ✓ {name} — no original style codes found")

print("\n" + "=" * 55)
print("  All styles in all files use anonymized codes ✓" if not any([
    any(has_original_prefix(s) for s in sales_styles),
    any(has_original_prefix(s) for s in purchase_styles),
    any(has_original_prefix(s) for s in order_styles),
]) else "  ⚠ Some original codes still present — check above")
print("=" * 55)