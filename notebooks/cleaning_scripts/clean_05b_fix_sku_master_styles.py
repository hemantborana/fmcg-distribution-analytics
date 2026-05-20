import pandas as pd
import re
import random
import os

BASE         = r"C:\Users\User\Desktop\major_project"
CLEANED      = os.path.join(BASE, "data_cleaned")
SKU_FILE     = os.path.join(CLEANED, "sku_master_cleaned.xlsx")
MAPPING_FILE = os.path.join(CLEANED, "style_code_mapping.xlsx")

PREFIX_MAP = {
    "A":"D","AB":"DB","BB":"GB","BR":"HR","CB":"NB","CH":"NH","CR":"NR","CW":"NW",
    "E":"G","EC":"GC","F":"H","FB":"HB","IB":"KB","IO":"KO","IP":"KP","MB":"RB",
    "MH":"RH","MS":"RS","MT":"RT","P":"Q","PB":"QB","PH":"QH","PP":"QQ","SB":"TB","TS":"VS",
}

# ── Load existing mapping ─────────────────────────────────────────────────────
print("Loading files...")
sku        = pd.read_excel(SKU_FILE)
mapping_df = pd.read_excel(MAPPING_FILE)
style_map  = dict(zip(
    mapping_df["Original_Style"].astype(str).str.strip().str.upper(),
    mapping_df["Anonymized_Style"].astype(str).str.strip()
))
print(f"  ✓ SKU master rows    : {len(sku)}")
print(f"  ✓ Existing mappings  : {len(style_map)}")

# ── Find unmapped original styles in SKU master ───────────────────────────────
def has_original_prefix(style):
    return bool(re.match(
        r'^(A|E|F|SB|MH|MB|IP|IB|IO|CB|CH|CR|CW|AB|BB|BR|PP|PH|PB|P|TS)\d+$',
        str(style)
    ))

unmapped = [s for s in sku["Style"].dropna().unique()
            if has_original_prefix(s) and s not in style_map]

print(f"\n  ⚠ Unmapped original styles found: {len(unmapped)}")
print(f"    {sorted(unmapped)}\n")

# ── Generate new anonymized codes for unmapped styles ─────────────────────────
random.seed(99)  # different seed so no clash with previous mapping

def split_style(code):
    match = re.match(r'^([A-Za-z]+)(\d+)$', str(code).strip())
    if match:
        return match.group(1).upper(), match.group(2)
    return None, None

# Get all already-used anonymized codes to avoid collision
used_codes = set(style_map.values())

new_mappings = {}
for style in sorted(unmapped):
    prefix, number = split_style(style)
    if not prefix:
        new_mappings[style] = f"XX{str(len(new_mappings)+1).zfill(3)}"
        continue
    new_prefix = PREFIX_MAP.get(prefix, prefix)
    num_digits = len(number)
    max_val    = 10 ** num_digits
    # Find a unique code not already used
    attempts = 0
    while attempts < 1000:
        new_num  = random.randint(1, max_val - 1)
        new_code = new_prefix + str(new_num).zfill(num_digits)
        if new_code not in used_codes:
            used_codes.add(new_code)
            new_mappings[style] = new_code
            break
        attempts += 1

print("  New codes generated:")
for orig, anon in sorted(new_mappings.items()):
    print(f"    {orig:<15} → {anon}")

# ── Merge new mappings into existing mapping file ─────────────────────────────
style_map.update(new_mappings)

# Save updated mapping file
updated_mapping = pd.DataFrame(
    [(k, v) for k, v in sorted(style_map.items())],
    columns=["Original_Style", "Anonymized_Style"]
)
updated_mapping.to_excel(MAPPING_FILE, index=False)
print(f"\n  ✓ Mapping file updated: now {len(style_map)} total mappings")

# ── Apply updated mapping to SKU master ───────────────────────────────────────
print("\nApplying updated mapping to SKU master...")
sku["Style"]    = sku["Style"].astype(str).str.strip().str.upper().map(style_map).fillna(sku["Style"])
sku["SKU_Code"] = sku["Style"] + "_" + sku["Color"] + "_" + sku["Size"]
sku.to_excel(SKU_FILE, index=False)

# ── Verify ────────────────────────────────────────────────────────────────────
remaining = [s for s in sku["Style"].dropna().unique() if has_original_prefix(s)]
print(f"\n{'='*55}")
print(f"FIX COMPLETE")
print(f"{'='*55}")
print(f"  Original codes remaining in SKU master : {len(remaining)}")
if remaining:
    print(f"  Still found: {remaining}")
else:
    print(f"  ✓ Zero original codes remaining — all files clean")
print(f"  Total unique styles in SKU master      : {sku['Style'].nunique()}")
print(f"  Total SKU entries                      : {len(sku)}")
print(f"{'='*55}")
print(f"\n✅ Saved: data_cleaned\\sku_master_cleaned.xlsx")
print(f"✅ Saved: data_cleaned\\style_code_mapping.xlsx")