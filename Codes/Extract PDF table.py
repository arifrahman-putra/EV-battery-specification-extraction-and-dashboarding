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

# Make sure Tipe/Spesifikasi column exists
if "Tipe/Spesifikasi" in combined_df.columns:

    # Create new columns
    combined_df["Kapasitas_Baterai"] = ""
    combined_df["Jenis_Baterai"] = ""
    combined_df["Engine_Power"] = ""
    combined_df["SUT"] = ""

    for i, row in combined_df.iterrows():
        text = str(row["Tipe/Spesifikasi"]).replace("\n", " ")  # flatten line breaks

        # 1. Extract Kapasitas Baterai / Energy
        m = re.search(r"(Kapasitas Baterai[:\s]*[\d,\.]+ *kWh)", text, re.IGNORECASE)
        if not m:
            m = re.search(r"(Energy[:\s]*[\d,\.]+ *kWh)", text, re.IGNORECASE)
        if not m:
            m = re.search(r"(Energi[:\s]*[\d,\.]+ *kWh)", text, re.IGNORECASE)
        if not m:
            m = re.search(r"(Kapasitas[:\s]*[\d,\.]+ *kWh)", text, re.IGNORECASE)
        if m:
            combined_df.at[i, "Kapasitas_Baterai"] = m.group(1)

        # 2. Extract Jenis Baterai
        m = re.search(r"(Jenis Baterai[:\s]*[^,;]+)", text, re.IGNORECASE)
        if not m:
            m = re.search(r"(Baterai[:\s]*[^,;]+)", text, re.IGNORECASE)
        if m:
            combined_df.at[i, "Jenis_Baterai"] = m.group(1)

        # 3. Extract Engine Power
        m = re.search(r"\(Engine Power\)[:\s]*([^,;]+)", text, re.IGNORECASE)
        if m:
            combined_df.at[i, "Engine_Power"] = m.group(1)

        # 4. Extract SUT / SK Variant
        m = re.search(r"(No SUT\s*:\s*[^;]+|SUT\s*:\s*[^;]+|Nomor SUT\s*:\s*[^;]+|SK Variant\s*:\s*[^;]+)", text, re.IGNORECASE)
        if m:
            combined_df.at[i, "SUT"] = m.group(1)

out_path = "ExtractedData\\2025kmperin5096_Cleaned_v2.xlsx"
combined_df.to_excel(out_path, index=False)
print("Done, data exported to", out_path)
