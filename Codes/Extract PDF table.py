import re
import camelot
import pandas as pd

# === INPUT PDF PATH (user must providee) ===
# for indonesian 4 wheelere and bus ev products, get: https://jdih.kemenperin.go.id/dokumen/view?id=1759
initial_columns = ["Company", "Type/Specs", "Domestic Component Level", "Certification Date"]
parsed_columns = ["Manufacturer", "Model", "Battery Type", "Battery Capacity (kWh)", "Engine Power (kW)"]

pdf_path = "EV_Manufacturer_Product_Specs.pdf"
tables = camelot.read_pdf(pdf_path, pages='all')

# Combine all tables
dfs = [t.df for t in tables]
combined_df = pd.concat(dfs, ignore_index=True)

# Set first row as header
combined_df.columns = combined_df.iloc[0]
combined_df = combined_df[1:].reset_index(drop=True)

# ----------------- FUNCTIONS -----------------

def clean_model_type(text):
    if pd.isna(text):
        return text
    text = str(text).replace("\n", " ")
    m = re.search(r"^(.*?\b[AM]/T\b)", text, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return text.strip()

Battery_Types = ["LiFePO4", "Li(NiCoMn)O2", "Li-ion (unknown)", "Unknown"]

def normalize_battery_type(text):
    if pd.isna(text):
        return "Unknown"

    t = str(text).lower()

    lfp_patterns = [
        r"\blfp\b", r"life\s*po\s*4", r"lifepo4", r"lifepo",
        r"li\s*fe\s*po\s*4", r"lithium\s+iron\s+phos",
        r"lithium\s+iron\s+phosphate", r"lithium\s+iron\s+graphite",
        r"lithium\s+ion\s+lfp", r"lithium\s+ferro\s+phosphate",
    ]

    nmc_patterns = [
        r"\bnmc\b", r"nickel", r"cobalt", r"manganese", r"li-ion\s*polymer"
    ]

    liion_patterns = [
        r"lithium\s*ion\s*battery", r"li-ion\s*battery", r"li-\s*ion", r"li-ion"
    ]

    for p in lfp_patterns:
        if re.search(p, t):
            return Battery_Types[0]
    for q in nmc_patterns:
        if re.search(q, t):
            return Battery_Types[1]
    for r in liion_patterns:
        if re.search(r, t):
            return Battery_Types[2]

    return Battery_Types[3]

def extract_numeric_value(text):
    if pd.isna(text):
        return None
    t = str(text).lower()
    m = re.search(r"\d+[.,]?\d*", t)
    if not m:
        return None
    num_str = m.group(0).replace(",", ".")
    try:
        return float(num_str)
    except ValueError:
        return None

# ----------------- DATA CLEANING -----------------

# Drop repeated header rows
drop_rows = []
for i in range(len(combined_df)):
    row = combined_df.iloc[i]
    if all(str(row[col]).strip() == str(col).strip() for col in combined_df.columns):
        drop_rows.append(i)
combined_df = combined_df.drop(drop_rows).reset_index(drop=True)

# Forward fill company/manufacturer names
if initial_columns[0] in combined_df.columns:
    combined_df = combined_df.rename(columns={initial_columns[0]: parsed_columns[0]})
    last_val = ""
    for i in range(len(combined_df)):
        val = combined_df.at[i, parsed_columns[0]]
        if val is None or str(val).strip() == "":
            combined_df.at[i, parsed_columns[0]] = last_val
        else:
            last_val = val

# Rename other columns to English general names
if initial_columns[1] in combined_df.columns:
    # "Model" parsed column
    combined_df = combined_df.rename(columns={initial_columns[1]: parsed_columns[1]})


# Create new standardized columns
combined_df[parsed_columns[2]] = "" # "Battery Type" parsed column
combined_df[parsed_columns[3]] = "" # "Battery Capacity (kWh)" parsed column
combined_df[parsed_columns[4]] = "" # "Engine Power (kW)" parsed column

for i, row in combined_df.iterrows():
    text = str(row[parsed_columns[1]]).replace("\n", " ")

    # Battery Type
    m = re.search(r"\b(Lithium|Li-|LFP|LiFe)[a-zA-Z\s]{0,20}\b", text, re.IGNORECASE)
    if m:
        combined_df.at[i, parsed_columns[2]] = normalize_battery_type(m.group(0).strip())

    # Battery Capacity
    m = re.search(r"\b\d+[.,]?\d*\s*kwh\b", text, re.IGNORECASE)
    if m:
        combined_df.at[i, parsed_columns[3]] = extract_numeric_value(m.group(0))

    # Engine Power
    m = re.search(r"\b\d+[.,]?\d*\s*kw\b", text, re.IGNORECASE)
    if m and "kwh" not in m.group(0).lower():
        combined_df.at[i, parsed_columns[4]] = extract_numeric_value(m.group(0))


# Clean Model Type
combined_df[parsed_columns[1]] = combined_df[parsed_columns[1]].apply(clean_model_type)
combined_df = combined_df[parsed_columns]

# Save cleaned data
out_path = "EV_Battery_Data_Cleaned.csv"
combined_df.to_csv(out_path, index=False)
print("Done! Cleaned data saved to", out_path)


#-------- Streamlit Dashboard --------#
import streamlit as st
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

# set up security credentials for user
USER = "Username"
PASS = "12345"

# check for login attempts
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# if client hasn't been logged in
if not st.session_state.logged_in:
    st.title("🔒 Login to Access Dashboard")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username == USER and password == PASS:
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Your username or password is incorrect.")

else:
    st.success("✅ You are logged in, welcome to the dashboard.")
    st.header("EV battery specification analysis dashboard")

    # Display data
    st.subheader("🚗⚡️ EV Product Specification List")
    st.dataframe(combined_df)


    New_Manufacturers = []
    num_bats = []

    Manufacturers = combined_df[parsed_columns[0]].tolist()
    for manufacturer in Manufacturers:
        manufacturer_df = combined_df.loc[combined_df[parsed_columns[0]] == manufacturer]
        for batt_type in Battery_Types:
            batt_df = manufacturer_df.loc[manufacturer_df[parsed_columns[2]] == batt_type]
            New_Manufacturers.append(manufacturer)
            num_bats.append(len(batt_df))

    diagram_dict = {"Manufacturer": New_Manufacturers, "Battery Type": Battery_Types, "Number": num_bats}
    diagram_df = pd.DataFrame(diagram_dict)

    st.subheader("🔋 EV Battery Type Diagram")
    fig_trans = px.bar(diagram_df, x='Manufacturer', y='Number', color='Battery Type',
                       color_discrete_map={Battery_Types[0]: "green",
                                           Battery_Types[1]: "blue",
                                           Battery_Types[2]: "yellow",
                                           Battery_Types[3]: "red"})
    st.plotly_chart(fig_trans, use_container_width=True)
