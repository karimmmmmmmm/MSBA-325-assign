# Lebanon Tourism Explorer: MSBA 325

Interactive Streamlit exploration of the Tourism-Lebanon-2023 dataset.

## Analytical question
How do reported tourism potential, recent initiatives, Tourism Index values, and hospitality-establishment quantities vary across Lebanon?

## Linked interactions
The dashboard uses a geographic drill-down: **Lebanon → Governorate/District → Town**. The selected geographic level changes the available area choices, and the selected area changes the available town choices. Both analytical views and the map respond to the same selection.

## Visualizations
- Initiative status among observations reporting a developable tourism attraction.
- Tourism Index versus the combined quantity of hotels, guest houses, restaurants and cafés.
- Context map that follows the current geographic selection.

## Design and ethics
Course concepts are made visible on the page: providing context, reducing clutter, focusing attention, progressive disclosure, coordinated views and appropriate chart choice. The dashboard is exploratory rather than persuasive: it does not hide counter-evidence, does not infer causation from correlation, and flags selections with too few observations for meaningful relationship analysis.

## Map note
Town locations are geocoded on demand through OpenStreetMap Nominatim. If a precise town match is unavailable, the app falls back to an approximate area center and labels that limitation rather than inventing a precise location.

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deployment
Deploy `app.py` from this repository on Streamlit Community Cloud.
