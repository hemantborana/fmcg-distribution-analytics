import pandas as pd
import os
import re
from pathlib import Path

BASE         = r"C:\Users\User\Desktop\major_project"
STOCK_DIR    = os.path.join(BASE, r"data_raw\stock_files")
OUTPUT       = os.path.join(BASE, r"data_cleaned\stock_snapshots_cleaned.xlsx")
MAPPING_FILE = os.path.join(BASE, r"data_cleaned\style_code_mapping.xlsx")

# ── Load style mapping ────────────────────────────────────────────────────────
print("Loading style code mapping...")
mapping_df = pd.read_excel(MAPPING_FILE)
style_map  = dict(zip(
    mapping_df["Original_Style"].astype(str).str.strip().str.upper(),
    mapping_df["Anonymized_Style"].astype(str).str.strip()
))
print(f"  ✓ {len(style_map)} style mappings loaded\n")

# ── Parse product description → Style, Color, Size ───────────────────────────
def parse_product(desc):
    """
    Input : 'A014-NPNW-P1, BLACK, 38C'
    Output: ('A014', 'BLACK', '38C')
    """
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

# ── Extract date from filename ────────────────────────────────────────────────
def extract_date(filename):
    """
    'cleaned_inventory_report_20251110_145454.xlsx' → '2025-11-10'
    """
    match = re.search(r'_(\d{8})_', filename)
    if match:
        d = match.group(1)
        return pd.to_datetime(d, format="%Y%m%d").date()
    return None

# ── Process all stock files ───────────────────────────────────────────────────
print("Processing stock snapshot files...")
stock_files = sorted(Path(STOCK_DIR).glob("cleaned_inventory_report_*.xlsx"))
print(f"  ✓ Found {len(stock_files)} files\n")

all_frames   = []
sync_files   = []
normal_files = []
parse_errors = 0

for i, filepath in enumerate(stock_files):
    filename     = filepath.name
    snap_date    = extract_date(filename)

    df = pd.read_excel(filepath, dtype={"stock": float})

    # Tag sync files — all stock values are zero or file is empty
    total_stock = pd.to_numeric(df["stock"], errors="coerce").fillna(0).sum()
    is_sync     = (total_stock == 0)

    if is_sync:
        sync_files.append(filename)
    else:
        normal_files.append(filename)

    # Parse product → Style, Color, Size
    parsed = df["product"].apply(
        lambda x: pd.Series(parse_product(x), index=["Style","Color","Size"])
    )
    df = pd.concat([df, parsed], axis=1)

    # Count parse failures
    parse_errors += df["Style"].isna().sum()

    # Apply style anonymization
    df["Style"] = df["Style"].astype(str).str.strip().str.upper().map(style_map).fillna(df["Style"])

    # Build SKU_Code
    df["SKU_Code"] = df["Style"] + "_" + df["Color"] + "_" + df["Size"]

    # Add metadata columns
    df["Snapshot_Date"] = snap_date
    df["Is_Sync_File"]  = is_sync
    df["Source_File"]   = filename

    # Drop original product column
    df.drop(columns=["product"], inplace=True)

    # Rename stock and category
    df.rename(columns={"stock": "Stock_Qty", "category": "Category"}, inplace=True)

    # Fix stock qty
    df["Stock_Qty"] = pd.to_numeric(df["Stock_Qty"], errors="coerce").fillna(0).astype(int)
    df["Category"]  = df["Category"].astype(str).str.strip().str.upper()

    all_frames.append(df)

    # Progress every 25 files
    if (i + 1) % 25 == 0 or (i + 1) == len(stock_files):
        print(f"  Processed {i+1}/{len(stock_files)} files...")

# ── Combine all frames ────────────────────────────────────────────────────────
print("\nCombining all snapshots...")
combined = pd.concat(all_frames, ignore_index=True)

# ── Final column order ────────────────────────────────────────────────────────
final_cols = [
    "Snapshot_Date", "Is_Sync_File", "Source_File",
    "Category", "Style", "Color", "Size", "SKU_Code", "Stock_Qty"
]
combined = combined[[c for c in final_cols if c in combined.columns]]
combined = combined.sort_values(["Snapshot_Date", "SKU_Code"]).reset_index(drop=True)

# ── Save ──────────────────────────────────────────────────────────────────────
print("Saving...")
combined.to_excel(OUTPUT, index=False)

# ── Summary ───────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("CLEANING COMPLETE — stock_snapshots")
print("="*60)
print(f"  Total files processed  : {len(stock_files)}")
print(f"  Normal snapshots       : {len(normal_files)}")
print(f"  Sync files (all zero)  : {len(sync_files)}")
if sync_files:
    print(f"  Sync file dates:")
    for f in sync_files:
        d = extract_date(f)
        print(f"    → {d}  ({f})")
print(f"\n  Total rows (combined)  : {len(combined)}")
print(f"  Date range             : {combined['Snapshot_Date'].min()} → {combined['Snapshot_Date'].max()}")
print(f"  Unique SKUs tracked    : {combined['SKU_Code'].nunique()}")
print(f"  Unique styles tracked  : {combined['Style'].nunique()}")
print(f"  Parse errors           : {parse_errors} rows")
print(f"\n  Non-sync rows          : {(~combined['Is_Sync_File']).sum():,}")
print(f"  Sync rows (excluded)   : {combined['Is_Sync_File'].sum():,}")
print("="*60)
print("\n✅ Saved: data_cleaned\\stock_snapshots_cleaned.xlsx")
print("\n⚠  For all analysis use: combined[combined['Is_Sync_File'] == False]")
print("   Never include sync file rows in stock calculations")