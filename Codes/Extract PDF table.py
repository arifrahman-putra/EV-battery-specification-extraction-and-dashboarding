import camelot
import pandas as pd
import re

# Assume combined_df already exists and has column "Tipe/Spesifikasi"
def extract_specs(spec_text):
    if pd.isna(spec_text):
        return pd.Series([None, None, None])

    # Normalize whitespace
    spec_text = " ".join(str(spec_text).split())

    # 1. Extract Kapasitas Baterai
    baterai_match = re.search(r'Kapasitas Baterai[:\s]*([0-9.,\skWhKWh]+)', spec_text, re.IGNORECASE)
    kapasitas_baterai = baterai_match.group(1).strip() if baterai_match else None

    # 2. Extract Jenis Baterai
    jenis_match = re.search(r',\s*Baterai[:\s]*([A-Za-z0-9\s/-]+)', spec_text, re.IGNORECASE)
    jenis_baterai = jenis_match.group(1).strip() if jenis_match else None

    # 3. Extract Engine Power
    engine_match = re.search(r'\(Engine Power\)[:\s]*([0-9\s\w/.-]+)', spec_text, re.IGNORECASE)
    engine_power = engine_match.group(1).strip() if engine_match else None

    return pd.Series([kapasitas_baterai, jenis_baterai, engine_power])


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


# Apply specs ectraction to the dataframe
combined_df[['Kapasitas Baterai', 'Jenis Baterai', 'Engine Power']] = combined_df['Tipe/Spesifikasi'].apply(extract_specs)


# Save the cleaned dataframe to Excel
out_path = "ExtractedData\\2025kmperin5096_Cleaned.xlsx"
combined_df.to_excel(out_path, index=False)

print("Done, data has been exported to", out_path)
