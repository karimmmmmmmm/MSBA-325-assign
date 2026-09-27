# Lebanon Tourism Evidence Explorer

Interactive Streamlit exploration of the Tourism-Lebanon-2023 dataset for MSBA 325.

## Purpose
The app examines reported developable tourism attractions, tourism initiatives in the previous five years, Tourism Index values, and the quantity of four hospitality-establishment categories: hotels, guest houses, restaurants, and cafés.

The app is intentionally exploratory. It does not classify areas as good or bad investments and does not hide observations that weaken a simple tourism-opportunity narrative.

## Linked interactions
1. **Geographic level** — choose Governorate or District.
2. **Area** — available areas update based on the geographic level selected.

An optional town selector supports further drill-down.

## Visualizations
1. Initiative status among observations with reported developable attractions.
2. Tourism Index versus hospitality-establishment quantity.

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deployment
Deploy this repository on Streamlit Community Cloud.

Public Streamlit URL: _add after deployment_

## Submission files
- `app.py`
- `tourism_lebanon_2023.csv`
- `requirements.txt`
- `README.md`
- `MSBA325_Streamlit_Report.docx`
