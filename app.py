import re
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Lebanon Tourism Explorer", page_icon="🇱🇧", layout="wide", initial_sidebar_state="collapsed")
DATA_FILE = "tourism_lebanon_2023.csv"

# ---------- visual system ----------
st.markdown("""
<style>
:root { --ink:#16212b; --muted:#68737d; --line:#e8ecef; --paper:#ffffff; --soft:#f7f8f7; --accent:#9b2c2c; }
.block-container {padding-top:1.25rem; padding-bottom:2rem; max-width:1450px;}
[data-testid="stHeader"] {background:rgba(255,255,255,.92)}
h1,h2,h3 {letter-spacing:-0.02em; color:var(--ink)}
.small-kicker {font-size:.78rem; text-transform:uppercase; letter-spacing:.11em; color:#7a838b; font-weight:700;}
.hero {padding:.35rem 0 1rem 0; border-bottom:1px solid var(--line); margin-bottom:1rem;}
.hero h1 {font-size:2.25rem; margin:.15rem 0 .2rem 0;}
.hero p {color:var(--muted); font-size:1.02rem; margin:0; max-width:850px;}
.context {font-size:.86rem; color:var(--muted); margin-top:.4rem;}
.panel-note {border-top:1px solid var(--line); padding-top:.7rem; margin-top:.4rem; color:#4e5963; font-size:.92rem;}
.insight {background:var(--soft); border:1px solid var(--line); border-radius:14px; padding:1rem 1.1rem; min-height:118px;}
.insight b {color:var(--ink)}
.ethics {border-left:3px solid #8b949c; padding:.2rem 0 .2rem 1rem; color:#4e5963;}
[data-testid="stMetric"] {background:transparent; border-top:1px solid var(--line); padding-top:.7rem;}
div[data-baseweb="select"] > div {border-radius:10px;}
.stRadio [role="radiogroup"] {gap:.35rem;}
.stRadio [role="radiogroup"] label {background:#f5f6f6; border:1px solid #e4e7e9; border-radius:999px; padding:.25rem .7rem;}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    df = pd.read_csv(DATA_FILE)
    def clean_area(value):
        s = str(value).rsplit("/", 1)[-1].replace("_", " ")
        for bad, good in {"ZahlÃ©":"Zahlé", "MiniyehâDanniyeh":"Miniyeh–Danniyeh", "â":"–", "Ã©":"é"}.items():
            s = s.replace(bad, good)
        return s.strip()
    df["Area"] = df["refArea"].apply(clean_area)
    df["Geographic Level"] = df["Area"].apply(lambda x: "District" if "District" in x else ("Governorate" if "Governorate" in x else "Other"))
    qty = ["Total number of hotels","Total number of cafes","Total number of guest houses","Total number of restaurants"]
    for c in qty: df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    df["Hospitality Establishments"] = df[qty].sum(axis=1)
    df["Tourism Index"] = pd.to_numeric(df["Tourism Index"], errors="coerce")
    p = "Existence of touristic attractions prone to be exploited and developed - exists"
    i = "Existence of initiatives and projects in the past five years to improve the tourism sector - exists"
    df["Developable Attraction"] = pd.to_numeric(df[p], errors="coerce").fillna(0).astype(int)
    df["Recent Initiative"] = pd.to_numeric(df[i], errors="coerce").fillna(0).astype(int)
    df["Initiative Status"] = df["Recent Initiative"].map({1:"Initiative reported",0:"No initiative reported"})
    df["Potential Status"] = df["Developable Attraction"].map({1:"Developable attraction reported",0:"No developable attraction reported"})
    df["Town"] = df["Town"].astype(str).str.strip()
    return df

df = load_data()

# Approximate centers used only as map fallbacks/context. Towns are geocoded on demand when possible.
CENTERS = {
    "Lebanon": (33.8547, 35.8623), "Beirut Governorate":(33.8938,35.5018), "Mount Lebanon Governorate":(33.82,35.63),
    "North Governorate":(34.43,35.85), "Akkar Governorate":(34.54,36.08), "Baalbek-Hermel Governorate":(34.15,36.30),
    "Beqaa Governorate":(33.85,35.99), "South Governorate":(33.35,35.30), "Nabatieh Governorate":(33.38,35.48),
    "Batroun District":(34.25,35.66), "Byblos District":(34.12,35.65), "Keserwan District":(33.98,35.70), "Baabda District":(33.83,35.60),
    "Aley District":(33.81,35.60), "Chouf District":(33.70,35.58), "Tripoli District":(34.44,35.84), "Zgharta District":(34.40,35.90),
    "Bsharri District":(34.25,36.00), "Koura District":(34.37,35.84), "Miniyeh–Danniyeh District":(34.45,36.03), "Akkar District":(34.54,36.08),
    "Zahle District":(33.85,35.90), "Zahlé District":(33.85,35.90), "West Beqaa District":(33.62,35.78), "Rashaya District":(33.50,35.84),
    "Baalbek District":(34.01,36.21), "Hermel District":(34.39,36.38), "Sidon District":(33.56,35.37), "Tyre District":(33.27,35.20),
    "Jezzine District":(33.54,35.58), "Nabatieh District":(33.38,35.48), "Bint Jbeil District":(33.12,35.43), "Marjeyoun District":(33.36,35.59),
    "Hasbaya District":(33.40,35.68), "Beirut District":(33.8938,35.5018), "Matn District":(33.91,35.67)
}

def normalize_area(s):
    return re.sub(r"\s+", " ", str(s)).strip()

@st.cache_data(show_spinner=False, ttl=86400)
def geocode_place(place):
    try:
        r = requests.get("https://nominatim.openstreetmap.org/search", params={"q":f"{place}, Lebanon","format":"jsonv2","limit":1,"countrycodes":"lb"}, headers={"User-Agent":"MSBA325-AUB-tourism-coursework/1.0"}, timeout=3)
        r.raise_for_status(); js=r.json()
        if js: return float(js[0]["lat"]), float(js[0]["lon"]), True
    except Exception:
        pass
    return None, None, False

def map_point(level, area, town):
    if town and town != "All towns":
        lat, lon, exact = geocode_place(town)
        if exact: return lat, lon, f"{town}", True
    key = area if area else "Lebanon"
    lat, lon = CENTERS.get(normalize_area(key), CENTERS["Lebanon"])
    return lat, lon, key, False

# ---------- header ----------
st.markdown("""<div class='hero'><div class='small-kicker'>MSBA 325 · Tourism-Lebanon-2023</div><h1>Lebanon Tourism Explorer</h1><p>How do reported tourism potential, recent initiatives and hospitality infrastructure vary across Lebanon?</p></div>""", unsafe_allow_html=True)

# ---------- linked controls ----------
control_a, control_b, control_c = st.columns([1.1,1.4,1.4], gap="medium")
with control_a:
    level = st.radio("Explore by", ["Lebanon","Governorate","District"], horizontal=True, label_visibility="visible")

area = None; town = "All towns"
if level == "Lebanon":
    base_df = df.copy()
    with control_b: st.selectbox("Area", ["All Lebanon"], disabled=True)
    with control_c: st.selectbox("Town", ["All towns"], disabled=True)
else:
    base_df = df[df["Geographic Level"] == level].copy()
    areas = sorted(base_df["Area"].dropna().unique())
    with control_b: area = st.selectbox(f"{level}", areas)
    area_df = base_df[base_df["Area"] == area].copy()
    towns = ["All towns"] + sorted(area_df["Town"].dropna().unique().tolist())
    with control_c: town = st.selectbox("Town (optional)", towns)
    base_df = area_df

view_df = base_df if town == "All towns" else base_df[base_df["Town"] == town]
selection = "Lebanon" if level == "Lebanon" else (town if town != "All towns" else area)

st.markdown(f"<div class='context'>Current view: <b>{selection}</b> · {len(view_df):,} observations shown · Source: Tourism-Lebanon-2023</div>", unsafe_allow_html=True)

# ---------- summary metrics ----------
potential_n = int(view_df["Developable Attraction"].sum())
with_init = int(((view_df["Developable Attraction"]==1)&(view_df["Recent Initiative"]==1)).sum())
without_init = int(((view_df["Developable Attraction"]==1)&(view_df["Recent Initiative"]==0)).sum())
med_hosp = float(view_df["Hospitality Establishments"].median()) if len(view_df) else 0

m1, m2, m3, m4 = st.columns(4)
m1.metric("Developable attractions", f"{potential_n:,}")
m2.metric("With initiative", f"{with_init:,}")
m3.metric("Without initiative", f"{without_init:,}")
m4.metric("Median establishments", f"{med_hosp:,.0f}")

if potential_n:
    pct = 100 * without_init / potential_n
    st.markdown(
        f"<div class='insight'><div class='small-kicker'>What stands out</div>"
        f"<b>{without_init} of {potential_n} ({pct:.1f}%)</b> observations reporting a developable "
        f"attraction do <b>not</b> report a tourism initiative in the previous five years. "
        f"This is a descriptive gap, not proof of an investment opportunity.</div>",
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        "<div class='insight'><div class='small-kicker'>What stands out</div>"
        "No observations in this selection report a developable attraction. "
        "Widen the geographic view to compare a larger evidence base.</div>",
        unsafe_allow_html=True,
    )

# ---------- map + two analytical views on one horizontal level ----------
map_col, chart1, chart2 = st.columns([0.95, 1.05, 1.25], gap="medium")

with map_col:
    st.subheader("Where?")
    lat, lon, map_label, exact = map_point(level, area, town)
    map_df = pd.DataFrame({"lat":[lat], "lon":[lon], "label":[map_label]})
    zoom = 6.6 if level == "Lebanon" else (8.0 if town == "All towns" else 10.0)

    fig_map = px.scatter_map(
        map_df,
        lat="lat",
        lon="lon",
        hover_name="label",
        zoom=zoom,
        height=365,
    )
    fig_map.update_traces(marker={"size":16})
    fig_map.update_layout(
        map_style="open-street-map",
        map_center={"lat":lat, "lon":lon},
        margin=dict(l=0, r=0, t=8, b=0),
        showlegend=False,
    )
    st.plotly_chart(fig_map, use_container_width=True, config={"displayModeBar":False})
    if town != "All towns" and not exact:
        st.caption("Precise town geocoding was unavailable. The map shows the selected area's approximate center.")

with chart1:
    st.subheader("Potential & initiatives")
    potential_df = view_df[view_df["Developable Attraction"] == 1].copy()
    counts = (
        potential_df["Initiative Status"]
        .value_counts()
        .reindex(["Initiative reported", "No initiative reported"], fill_value=0)
        .rename_axis("Status")
        .reset_index(name="Observations")
    )
    if potential_n:
        f1 = px.bar(
            counts,
            x="Status",
            y="Observations",
            text="Observations",
            height=365,
            labels={"Status":"", "Observations":"Observations"},
        )
        f1.update_traces(textposition="outside")
        f1.update_layout(
            template="plotly_white",
            showlegend=False,
            margin=dict(l=15, r=5, t=8, b=15),
        )
        st.plotly_chart(f1, use_container_width=True, config={"displayModeBar":False})
    else:
        st.info("No developable-attraction observations for this selection.")
    st.markdown(
        "<div class='panel-note'>Initiative status is shown only among observations that report "
        "a developable tourism attraction, keeping the denominator explicit.</div>",
        unsafe_allow_html=True,
    )

with chart2:
    st.subheader("Tourism index & hospitality")
    if len(view_df) >= 2:
        f2 = px.scatter(
            view_df,
            x="Hospitality Establishments",
            y="Tourism Index",
            color="Initiative Status",
            hover_name="Town",
            height=365,
            hover_data={
                "Total number of hotels":True,
                "Total number of guest houses":True,
                "Total number of restaurants":True,
                "Total number of cafes":True,
                "Area":False,
            },
            labels={
                "Hospitality Establishments":"Hotels + guest houses + restaurants + cafés",
                "Initiative Status":"Initiative",
            },
        )
        f2.update_layout(
            template="plotly_white",
            margin=dict(l=15, r=5, t=8, b=15),
            legend=dict(
                title=None,
                orientation="h",
                yanchor="bottom",
                y=1.01,
                xanchor="left",
                x=0,
                font=dict(size=10),
            ),
        )
        st.plotly_chart(f2, use_container_width=True, config={"displayModeBar":False})
        corr = view_df["Hospitality Establishments"].corr(view_df["Tourism Index"])
        if pd.notna(corr):
            st.markdown(
                f"<div class='panel-note'>Pearson correlation: <b>{corr:.2f}</b>. "
                "This describes association only, not causation.</div>",
                unsafe_allow_html=True,
            )
    elif len(view_df) == 1:
        row = view_df.iloc[0]
        f2 = go.Figure(
            go.Scatter(
                x=[row["Hospitality Establishments"]],
                y=[row["Tourism Index"]],
                mode="markers+text",
                text=[row["Town"]],
                textposition="top center",
                marker_size=14,
            )
        )
        f2.update_layout(
            template="plotly_white",
            height=365,
            xaxis_title="Hotels + guest houses + restaurants + cafés",
            yaxis_title="Tourism Index",
            margin=dict(l=15, r=5, t=8, b=15),
        )
        st.plotly_chart(f2, use_container_width=True, config={"displayModeBar":False})
        st.markdown(
            "<div class='panel-note'><b>Limited evidence:</b> one observation cannot establish "
            "a relationship. Move up a geographic level for a meaningful comparison.</div>",
            unsafe_allow_html=True,
        )
    else:
        st.info("No observations for this selection.")

# ---------- visible course-linked rationale, no buttons ----------
st.divider()
st.subheader("Why this design")
d1,d2 = st.columns(2, gap="large")
with d1:
    st.markdown("""**Linked geographic drill-down**  
The controls answer *where should I investigate?* without presenting hundreds of places at once. The geographic level determines the available area options, and the area determines the town options. This applies the course concepts of **providing context, reducing clutter and focusing attention** through progressive disclosure. A map preserves spatial context as the selection becomes narrower.""")
with d2:
    st.markdown("""**Coordinated analytical views**  
The bar chart answers *is reported tourism potential accompanied by a recent initiative?* while the scatter plot asks *how does hospitality quantity relate to the Tourism Index?* Both respond to the same geographic selection, allowing comparison without separating related evidence. Tooltips keep detail available without crowding the page.""")

st.subheader("Reading the data responsibly")
st.markdown("""<div class='ethics'>The dashboard is exploratory rather than persuasive. It keeps initiative and no-initiative observations visible, uses the reported data without selectively removing inconvenient cases, and labels small samples rather than visually exaggerating them. Hospitality establishments are a <b>quantity</b> measure only. A developable attraction without a recent initiative is not automatically an investment opportunity, and correlation is not treated as causation. The dataset does not establish visitor demand, profitability, accessibility, attraction quality, project size or initiative value.</div>""", unsafe_allow_html=True)

st.caption("Map note: town locations are requested from OpenStreetMap Nominatim only when a town is selected; if a precise match is unavailable, the dashboard falls back to an approximate area center and says so explicitly.")
