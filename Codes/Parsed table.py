import pandas as pd

extracted_path = "ExtractedData\\2025kmperin5096_Cleaned_v4.xlsx"
df_extracted = pd.read_excel(extracted_path)

df_parsed = df_extracted[["Nama Perusahaan", "Model_Type", "TKDN",
                          "SUT", "Jenis_Baterai",
                          "Kapasitas_Baterai_kWh",
                          "Engine_Power_kW"]]

df_parsed.to_excel("ExtractedData\\Manual parsed\\2025kmperin5096_Cleaned_v4.xlsx")
