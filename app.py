import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Lebanon Tourism Evidence Explorer", page_icon="🇱🇧", layout="wide")
DATA_FILE = "tourism_lebanon_2023.csv"

@st.cache_data
def load_data():
    df = pd.read_csv(DATA_FILE)

    def clean_area(value):
        s = str(value).rsplit("/", 1)[-1].replace("_", " ")
        replacements = {
            "ZahlÃ©": "Zahlé",
            "MiniyehâDanniyeh": "Miniyeh–Danniyeh",
            "â": "–",
            "Ã©": "é",
        }
        for bad, good in replacements.items():
            s = s.replace(bad, good)
        return s.strip()

    df["Area"] = df["refArea"].apply(clean_area)
    df["Geographic Level"] = df["Area"].apply(
        lambda x: "District" if "District" in x else ("Governorate" if "Governorate" in x else "Other")
    )

    quantity_cols = [
        "Total number of hotels", "Total number of cafes",
        "Total number of guest houses", "Total number of restaurants",
    ]
    for c in quantity_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    df["Hospitality Establishments"] = df[quantity_cols].sum(axis=1)
    df["Tourism Index"] = pd.to_numeric(df["Tourism Index"], errors="coerce")

    # Explicit affirmative fields prevent accidental inversion of the binary meaning.
    potential_col = "Existence of touristic attractions prone to be exploited and developed - exists"
    initiative_col = "Existence of initiatives and projects in the past five years to improve the tourism sector - exists"

    df["Developable Attraction"] = pd.to_numeric(df[potential_col], errors="coerce").fillna(0).astype(int)
    df["Recent Initiative"] = pd.to_numeric(df[initiative_col], errors="coerce").fillna(0).astype(int)
    df["Initiative Status"] = df["Recent Initiative"].map({1: "Initiative reported", 0: "No initiative reported"})
    df["Potential Status"] = df["Developable Attraction"].map({
        1: "Developable attraction reported",
        0: "No developable attraction reported"
    })
    df["Town"] = df["Town"].astype(str).str.strip()
    return df

df = load_data()

st.title("🇱🇧 Lebanon Tourism Evidence Explorer")
st.caption(
    "Explore how reported developable tourism attractions, recent tourism initiatives, "
    "Tourism Index values, and hospitality-establishment quantities vary across Lebanese areas."
)
st.info(
    "This dashboard is exploratory. It does not label an area as a good or bad investment. "
    "Patterns are shown as reported in the dataset, including observations that do not support "
    "a simple tourism-opportunity story."
)

with st.sidebar:
    st.header("Drill down")
    levels = [x for x in ["Governorate", "District"] if x in set(df["Geographic Level"])]
    geo_level = st.radio(
        "1. Geographic level", levels,
        help="Choose one geographic scale so districts and governorates are not compared as equivalent units."
    )

    level_df = df[df["Geographic Level"] == geo_level].copy()
    areas = sorted(level_df["Area"].dropna().unique())
    area = st.selectbox(
        "2. Area", areas,
        help="This list changes automatically when the geographic level changes."
    )

    area_df = level_df[level_df["Area"] == area].copy()
    towns = ["All towns"] + sorted(area_df["Town"].dropna().astype(str).unique().tolist())
    town = st.selectbox("3. Town (optional)", towns)

    st.divider()
    only_potential = st.checkbox(
        "Show only observations with a reported developable attraction",
        value=False,
        help="Optional analytical focus. Turn it off to retain the full selected-area context."
    )

view_df = area_df.copy()
if town != "All towns":
    view_df = view_df[view_df["Town"] == town]
if only_potential:
    view_df = view_df[view_df["Developable Attraction"] == 1]

potential_n = int(view_df["Developable Attraction"].sum())
potential_no_init_n = int(((view_df["Developable Attraction"] == 1) & (view_df["Recent Initiative"] == 0)).sum())
potential_with_init_n = int(((view_df["Developable Attraction"] == 1) & (view_df["Recent Initiative"] == 1)).sum())
median_hosp = float(view_df["Hospitality Establishments"].median()) if len(view_df) else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Developable attractions reported", f"{potential_n:,}")
c2.metric("With initiative reported", f"{potential_with_init_n:,}")
c3.metric("Without initiative reported", f"{potential_no_init_n:,}")
c4.metric("Median hospitality establishments", f"{median_hosp:,.0f}")

st.subheader(f"1. Initiative status among reported developable attractions — {area}")
potential_df = view_df[view_df["Developable Attraction"] == 1].copy()
status_order = ["Initiative reported", "No initiative reported"]
status_counts = (
    potential_df["Initiative Status"].value_counts()
    .reindex(status_order, fill_value=0)
    .rename_axis("Initiative Status").reset_index(name="Observations")
)

if potential_n > 0:
    fig1 = px.bar(
        status_counts, x="Initiative Status", y="Observations", text="Observations",
        title="Reported initiative status among observations with developable attractions",
        labels={"Initiative Status": "", "Observations": "Number of observations"},
    )
    fig1.update_traces(textposition="outside")
    fig1.update_layout(template="plotly_white", showlegend=False)
    st.plotly_chart(fig1, use_container_width=True)

    pct_no_init = 100 * potential_no_init_n / potential_n
    st.write(
        f"**What the data says:** {potential_no_init_n} of {potential_n} ({pct_no_init:.1f}%) "
        f"observations with a reported developable attraction have no reported tourism initiative "
        f"in the previous five years. The remaining {potential_with_init_n} do report an initiative."
    )
else:
    st.info("No developable-attraction observations are reported for this selection.")

st.subheader("2. Tourism Index and hospitality-establishment quantity")
fig2 = px.scatter(
    view_df,
    x="Hospitality Establishments", y="Tourism Index",
    color="Initiative Status", symbol="Potential Status",
    hover_name="Town",
    hover_data={
        "Hospitality Establishments": True, "Tourism Index": True,
        "Total number of hotels": True, "Total number of guest houses": True,
        "Total number of restaurants": True, "Total number of cafes": True,
        "Area": False,
    },
    title="Hospitality-establishment quantity vs. Tourism Index",
    labels={"Hospitality Establishments": "Hotels + guest houses + restaurants + cafés"},
)
fig2.update_layout(template="plotly_white")
st.plotly_chart(fig2, use_container_width=True)

if len(view_df) >= 2:
    corr = view_df["Hospitality Establishments"].corr(view_df["Tourism Index"])
    if pd.notna(corr):
        st.write(
            f"**What the data says:** Within the current selection, the Pearson correlation "
            f"between Tourism Index and hospitality-establishment quantity is **{corr:.2f}**. "
            f"This is an association, not evidence of causation."
        )

with st.expander("Design justification: linked interactions"):
    st.markdown("""
**Interaction 1 — Geographic level**  
**User question:** At what geographic scale do I want to explore the tourism data?  
A radio button is used because the user must choose one mutually exclusive scale at a time. This provides context and avoids mixing governorates and districts in the same comparison. It follows the course principles of reducing unnecessary cognitive load and focusing attention.

**Interaction 2 — Area**  
**User question:** Which area within the selected geographic scale do I want to investigate?  
A dropdown is used because there are many named areas and displaying all of them as buttons would add clutter. It is linked to the first control: changing the geographic level changes the available area options. This supports progressive drill-down and keeps only relevant choices visible.
""")

with st.expander("Interpretation and ethical-use notes"):
    st.markdown("""
- The dashboard is designed to **explore** patterns, not to prove a predetermined conclusion.
- Both initiative and no-initiative observations remain visible when relevant, reducing the risk of a one-sided story.
- A reported developable attraction with no recent initiative is **not automatically an investment opportunity**.
- **Hospitality Establishments** is only a quantity measure: hotels + guest houses + restaurants + cafés in this dataset.
- The dataset does not measure visitor demand, profitability, accessibility, attraction quality, project size, or the number/value of initiatives.
- Correlation is presented as association only; it should not be interpreted as causation.
""")
