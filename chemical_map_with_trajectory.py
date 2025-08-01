import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from io import BytesIO

# ─── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="Chemical Business Mapping", layout="wide")

# ─── Global CSS to enlarge sidebar labels ─────────────────────────────────────
st.markdown(
    """
    <style>
      [data-testid="stSidebar"] label {
        font-size: 18px !important;
        font-weight: 500 !important;
      }
    </style>
    """,
    unsafe_allow_html=True
)

# ─── Load data ────────────────────────────────────────────────────────────────
# For GitHub deployment, place your CSV file in the same directory as this script
@st.cache_data
def load_data():
    try:
        # Try to load from the same directory as the script
        return pd.read_csv('2024_us.csv', low_memory=False)
    except FileNotFoundError:
        st.error("Data file '2024_us.csv' not found. Please ensure the file is in the same directory as this script.")
        st.stop()

us_data_df = load_data()

# ─── Sidebar filters ──────────────────────────────────────────────────────────
st.sidebar.header("Filters")
if st.sidebar.button("Reset Filters"):
    for key in ['state','zip','city','industry','fac','chem']:
        st.session_state.pop(key, None)

selected_state = st.sidebar.selectbox("State", ['All'] + sorted(us_data_df['STATE'].dropna().unique()), key='state')
filtered = us_data_df if selected_state=='All' else us_data_df[us_data_df['STATE']==selected_state]

selected_zip = st.sidebar.selectbox("Zip Code", ['All'] + sorted(filtered['ZIP CODE'].dropna().astype(str).unique()), key='zip')
filtered = filtered if selected_zip=='All' else filtered[filtered['ZIP CODE'].astype(str)==selected_zip]

selected_city = st.sidebar.selectbox("City", ['All'] + sorted(filtered['CITY'].dropna().unique()), key='city')
filtered = filtered if selected_city=='All' else filtered[filtered['CITY']==selected_city]

selected_industry = st.sidebar.selectbox(
    "Industry Sector",
    ['All'] + sorted(filtered['INDUSTRY SECTOR'].dropna().unique()),
    key='industry'
)
filtered = filtered if selected_industry=='All' else filtered[filtered['INDUSTRY SECTOR']==selected_industry]

selected_fac = st.sidebar.selectbox("Facility Name", ['All'] + sorted(filtered['FACILITY NAME'].dropna().unique()), key='fac')
filtered = filtered if selected_fac=='All' else filtered[filtered['FACILITY NAME']==selected_fac]

selected_chem = st.sidebar.selectbox("Chemical", ['All'] + sorted(filtered['CHEMICAL'].dropna().unique()), key='chem')
filtered = filtered if selected_chem=='All' else filtered[filtered['CHEMICAL']==selected_chem]

st.sidebar.markdown("---")
if 'show_map' not in st.session_state:
    st.session_state.show_map = False

# Generate Map button
if st.sidebar.button("Generate Map"):
    st.session_state.show_map = True

# Once map is generated, show download buttons in sidebar
if st.session_state.show_map:
    # prepare downloads
    buf_all = BytesIO()
    filtered.drop_duplicates(subset=['LATITUDE','LONGITUDE']).to_excel(buf_all, index=False)
    buf_all.seek(0)
    st.sidebar.download_button(
        "Download All Filtered Companies",
        buf_all,
        file_name="filtered_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

st.title("Chemical Business Mapping")

# ─── Render map and trajectory ────────────────────────────────────────────────
if st.session_state.show_map:
    summary_df = filtered.drop_duplicates(subset=['LATITUDE','LONGITUDE'])

    # Show metrics
    if selected_chem=='All' and selected_fac=='All':
        c1, c2 = st.columns(2)
        c1.metric("Total Facilities", len(summary_df))
        county_col = next((c for c in summary_df.columns if 'COUNTY' in c.upper()), None)
        if county_col:
            top3 = summary_df[county_col].value_counts().head(3)
            c2.markdown("**Top 3 Counties:** " + " | ".join(f"{cty}: {cnt}" for cty, cnt in top3.items()))

    # Base map & facility markers
    m = folium.Map(location=[37.09, -95.71], zoom_start=4)
    mc = MarkerCluster().add_to(m)
    for _, row in summary_df.iterrows():
        folium.Marker(
            [row['LATITUDE'], row['LONGITUDE']],
            icon=folium.Icon(color='red'),
            popup=folium.Popup(
                f"<b>{row['FACILITY NAME']}</b><br>"
                f"{row['STREET ADDRESS']}<br>"
                f"{row['CITY']}, {row['STATE']} {row['ZIP CODE']}",
                max_width=300
            )
        ).add_to(mc)

    st.markdown("---")
    
    # Render map
    st.components.v1.html(m._repr_html_(), height=700)

else:
    st.info("Select filters and click **Generate Map** to begin.")
