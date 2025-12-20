# EV Battery Data Extraction & Dashboard 

This is a data engineering process to extract important Electric Vehicle (EV) battery information (EV Manufacturer, model, battery type, battery capacity, engine power) from a text-based pdf table (obtained from a governmental/ministry tax/domestic component level listing document), and visualize the results in a streamlit dashboard with user credential operations, for climate-based policy making purposes.

The actual pdf source is not included to prevent copyright restrictions. please download at Kemenperin's official regulation website: https://jdih.kemenperin.go.id/dokumen/view?id=1759 for Indonesian opensource legal document to provide for EV_Manufacturer_Product_Specs.pdf

## 🔍 Overview

The system operates by:
1. **PDF Table Extraction** using camelot from EV_Manufacturer_Product_Specs.pdf

The extracted table from Kemenperin's regulation should be in the format:
| Company   | Type/Specs                                                 | Domestic Component Level  | Certification Date    |
|-----------|------------------------------------------------------------|---------------------------|-----------------------|
| ABC LLC   | Model: , Battery Type: , Battery Capacity: , Engine Power: | x%                        | MM: DD: YYYY          |
| XYZ LLC   | Model: , Battery Type: , Battery Capacity: , Engine Power: | x%                        | MM: DD: YYYY          |

2. **string information parsing** by cleaning model type and extracting battery specifications from the "Type/Specs" original table column.

3. **parsed table creation** with the new format:
   
| Manufacturer  | Model       | Battery Type   | Battery Capacity (kWh) | Engine Power (kW) |
|---------------|-------------|----------------|------------------------|-------------------|
| ABC LLC       | Type ABC EV | LiFePO4        | xx.x                   | xx.x              |
| XYZ LLC       | Type XYZ EV | Li(NiCoMn)O2   | xx.x                   | xx.x              |

4. **parsed table saving** into a csv file (EV_Battery_Data_Cleaned.csv)

5. **dashboard visualization** using streamlit, by providing for parsed table and plotting the number of each EV battery type in each manufacturer.  
