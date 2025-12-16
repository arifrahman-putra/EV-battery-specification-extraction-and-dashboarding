import re
import camelot
import pandas as pd

pdf_path = "RawData\\2025kmperin5096.pdf"
tables = camelot.read_pdf(pdf_path, pages='all')

# Combine all tables from all pages
dfs = [t.df for t in tables]
combined_df = pd.concat(dfs, ignore_index=True)

# Set the first row as header
combined_df.columns = combined_df.iloc[0]
combined_df = combined_df[1:].reset_index(drop=True)

def clean_vehicle_type(text):
    if pd.isna(text):
        return text

    text = str(text).replace("\n", " ")

    m = re.search(r"^(.*?\b[AM]/T\b)", text, re.IGNORECASE)
    if m:
        return m.group(1).strip()

    return text.strip()


def normalize_battery_type(text):
    if pd.isna(text):
        return text

    t = str(text).lower()

    # All known LFP variants & typos
    lfp_patterns = [
        r"\blfp\b",
        r"life\s*po\s*4",
        r"lifepo4",
        r"lifepo",
        r"li\s*fe\s*po\s*4",
        r"lithium\s+iron\s+phos",
        r"lithium\s+iron\s+phosphate",
        r"lithium\s+iron\s+graphite",
        r"lithium\s+ion\s+lfp",
        r"lithium\s+ferro\s+phosphate",
        r"lfp\s+kapasitas",
        r"pherophospat",
    ]

    liion_patterns = [
        r"lithium\s*ion\s*battery",
        r"li-ion\s*battery",
        r"li-\s*ion",
        r"li-ion",
    ]

    nmc_patterns = [
        r"li-ion\s*polymer"
    ]

    for p in lfp_patterns:
        if re.search(p, t):
            return "LiFePO4"

    for q in nmc_patterns:
        if re.search(q, t):
            return "Li(NiCoMn)O2"

    for r in liion_patterns:
        if re.search(r, t):
            return "Li-ion (unknown)"

    # If nothing matched → return original cleaned string
    return text.strip()


# Automatically drop rows that are identical to the header (often repeated on each page)
drop_rows = []
for i in range(len(combined_df)):
    row = combined_df.iloc[i]
    if all(str(row[col]).strip() == str(col).strip() for col in combined_df.columns):
        drop_rows.append(i)

combined_df = combined_df.drop(drop_rows).reset_index(drop=True)

# Forward fill the "Nama Perusahaan" column
if "Nama Perusahaan" in combined_df.columns:
    last_value = ""
    for i in range(len(combined_df)):
        val = combined_df.at[i, "Nama Perusahaan"]
        if val is None or str(val).strip() == "":
            combined_df.at[i, "Nama Perusahaan"] = last_value
        else:
            last_value = val

# === Extraction based on VALUE, not prefix ===

combined_df["Kapasitas_Baterai"] = ""
combined_df["Engine_Power"] = ""
combined_df["SUT"] = ""
combined_df["Jenis_Baterai"] = ""

for i, row in combined_df.iterrows():
    text = str(row["Tipe/Spesifikasi"]).replace("\n", " ")

    # 1. Kapasitas Baterai → number + kWh
    m = re.search(r"\b\d+[.,]?\d*\s*kwh\b", text, re.IGNORECASE)
    if m:
        combined_df.at[i, "Kapasitas_Baterai"] = m.group(0)

    # 2. Engine Power → number + kW (exclude kWh)
    m = re.search(r"\b\d+[.,]?\d*\s*kw\b", text, re.IGNORECASE)
    if m and "kwh" not in m.group(0).lower():
        combined_df.at[i, "Engine_Power"] = m.group(0)

    # 3. SUT → KP followed by anything until space
    m = re.search(r"\bKP[.\-/][^\s,;]+", text, re.IGNORECASE)
    if m:
        combined_df.at[i, "SUT"] = m.group(0)

    # 4. Jenis Baterai (heuristic, best effort)
    m = re.search(
        r"\b(Lithium|Li-|LFP|LiFe)[a-zA-Z\s]{0,20}\b",
        text,
        re.IGNORECASE
    )
    if m:
        combined_df.at[i, "Jenis_Baterai"] = m.group(0).strip()

combined_df = combined_df.drop(columns=["No"])

combined_df["Model_Type"] = combined_df["Tipe/Spesifikasi"].apply(clean_vehicle_type)
combined_df["Jenis_Baterai"] = (combined_df["Jenis_Baterai"].apply(normalize_battery_type))


out_path = "ExtractedData\\2025kmperin5096_Cleaned_v4.xlsx"
combined_df.to_excel(out_path, index=False)
print("Done, data exported to", out_path)
