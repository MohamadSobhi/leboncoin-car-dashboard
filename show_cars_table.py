import pandas as pd
import streamlit as st

CSV_FILE = "leboncoin_cars_ranked_comprehensive.csv"

st.set_page_config(
    page_title="Leboncoin Car Ranking",
    page_icon="🚗",
    layout="wide"
)

st.title("🚗 Leboncoin Car Decision Table")
st.caption("Used-car ranking and decision support for France")


@st.cache_data
def load_data(csv_file):
    df = pd.read_csv(csv_file)

    numeric_cols = [
        "ai_total_score_0_to_100",
        "ai_reliability_score_0_to_25",
        "ai_buyer_suitability_score_0_to_20",
        "ai_price_value_score_0_to_15",
        "ai_zfe_critair_score_0_to_10",
        "ai_running_cost_score_0_to_10",
        "ai_resale_score_0_to_10",
        "ai_parts_score_0_to_10",
        "ai_price_eur",
        "ai_year",
        "ai_mileage_km",
        "ai_critair",
        "ai_confidence_0_to_1",
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def display_name(col):
    """
    Remove ai_ and original_ prefixes only for display.
    Internal column names stay unchanged.
    """
    if col == "open_ad":
        return "url"

    clean = col

    if clean.startswith("ai_"):
        clean = clean[3:]

    if clean.startswith("original_"):
        clean = clean[9:]

    return clean


def put_url_last(columns):
    """
    Make sure url/open_ad/source_url is always at the end.
    """
    url_cols = [c for c in ["open_ad", "source_url", "url"] if c in columns]
    normal_cols = [c for c in columns if c not in url_cols]

    # Prefer open_ad if available, otherwise source_url/url
    if "open_ad" in url_cols:
        return normal_cols + ["open_ad"]
    elif "source_url" in url_cols:
        return normal_cols + ["source_url"]
    elif "url" in url_cols:
        return normal_cols + ["url"]

    return normal_cols


try:
    df = load_data(CSV_FILE)
except FileNotFoundError:
    st.error(f"CSV file not found: {CSV_FILE}")
    st.stop()


# Sort by score
if "ai_total_score_0_to_100" in df.columns:
    df = df.sort_values("ai_total_score_0_to_100", ascending=False)

# Add clickable ad URL column
if "source_url" in df.columns:
    df["open_ad"] = df["source_url"]
elif "url" in df.columns:
    df["open_ad"] = df["url"]


# -----------------------------
# Sidebar filters
# -----------------------------
st.sidebar.header("Filters")

search_text = st.sidebar.text_input("Search car name / brand / model")

if "ai_recommendation" in df.columns:
    recommendations = sorted(df["ai_recommendation"].dropna().unique().tolist())
else:
    recommendations = []

selected_recommendations = st.sidebar.multiselect(
    "Recommendation",
    recommendations,
    default=recommendations
)

if "ai_fuel_type" in df.columns:
    fuel_options = sorted(df["ai_fuel_type"].dropna().unique().tolist())
else:
    fuel_options = []

selected_fuels = st.sidebar.multiselect(
    "Fuel type",
    fuel_options,
    default=fuel_options
)

if "ai_total_score_0_to_100" in df.columns:
    score_range = st.sidebar.slider(
        "Total score",
        min_value=0,
        max_value=100,
        value=(
            int(df["ai_total_score_0_to_100"].fillna(0).min()),
            int(df["ai_total_score_0_to_100"].fillna(100).max())
        )
    )
else:
    score_range = (0, 100)

if "ai_price_eur" in df.columns:
    max_price_value = int(df["ai_price_eur"].fillna(10000).max())
    price_range = st.sidebar.slider(
        "Price (€)",
        min_value=0,
        max_value=max(1000, max_price_value),
        value=(
            int(df["ai_price_eur"].fillna(0).min()),
            max_price_value
        )
    )
else:
    price_range = (0, 999999)

if "ai_year" in df.columns:
    min_year_value = int(df["ai_year"].fillna(2000).min())
    max_year_value = int(df["ai_year"].fillna(2026).max())

    year_range = st.sidebar.slider(
        "Year",
        min_value=min_year_value,
        max_value=max_year_value,
        value=(min_year_value, max_year_value)
    )
else:
    year_range = (1900, 2100)

if "ai_mileage_km" in df.columns:
    max_mileage_value = int(df["ai_mileage_km"].fillna(300000).max())

    mileage_range = st.sidebar.slider(
        "Mileage km",
        min_value=0,
        max_value=max(1000, max_mileage_value),
        value=(
            int(df["ai_mileage_km"].fillna(0).min()),
            max_mileage_value
        )
    )
else:
    mileage_range = (0, 999999)


# -----------------------------
# Apply filters
# -----------------------------
filtered_df = df.copy()

if search_text:
    search_cols = [
        "ai_car_name",
        "ai_brand",
        "ai_model",
        "original_title",
        "ai_short_reason"
    ]

    existing_search_cols = [col for col in search_cols if col in filtered_df.columns]

    if existing_search_cols:
        mask = pd.Series(False, index=filtered_df.index)

        for col in existing_search_cols:
            mask = mask | filtered_df[col].fillna("").astype(str).str.contains(
                search_text,
                case=False,
                na=False
            )

        filtered_df = filtered_df[mask]

if selected_recommendations and "ai_recommendation" in filtered_df.columns:
    filtered_df = filtered_df[
        filtered_df["ai_recommendation"].isin(selected_recommendations)
    ]

if selected_fuels and "ai_fuel_type" in filtered_df.columns:
    filtered_df = filtered_df[
        filtered_df["ai_fuel_type"].isin(selected_fuels)
    ]

if "ai_total_score_0_to_100" in filtered_df.columns:
    filtered_df = filtered_df[
        filtered_df["ai_total_score_0_to_100"].between(score_range[0], score_range[1])
    ]

if "ai_price_eur" in filtered_df.columns:
    filtered_df = filtered_df[
        filtered_df["ai_price_eur"].between(price_range[0], price_range[1])
    ]

if "ai_year" in filtered_df.columns:
    filtered_df = filtered_df[
        filtered_df["ai_year"].between(year_range[0], year_range[1])
    ]

if "ai_mileage_km" in filtered_df.columns:
    filtered_df = filtered_df[
        filtered_df["ai_mileage_km"].between(mileage_range[0], mileage_range[1])
    ]


# -----------------------------
# Metrics
# -----------------------------
col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Cars shown", len(filtered_df))

if "ai_total_score_0_to_100" in filtered_df.columns and len(filtered_df) > 0:
    col2.metric("Best score", int(filtered_df["ai_total_score_0_to_100"].max()))
else:
    col2.metric("Best score", "-")

if "ai_price_eur" in filtered_df.columns and len(filtered_df) > 0:
    col3.metric("Lowest price", f"{int(filtered_df['ai_price_eur'].min()):,} €")
else:
    col3.metric("Lowest price", "-")

if "ai_year" in filtered_df.columns and len(filtered_df) > 0:
    col4.metric("Newest year", int(filtered_df["ai_year"].max()))
else:
    col4.metric("Newest year", "-")

if "ai_mileage_km" in filtered_df.columns and len(filtered_df) > 0:
    col5.metric("Lowest mileage", f"{int(filtered_df['ai_mileage_km'].min()):,} km")
else:
    col5.metric("Lowest mileage", "-")


# -----------------------------
# Columns to display
# -----------------------------
default_columns = [
    "ai_car_name",
    "ai_total_score_0_to_100",
    "ai_recommendation",
    "ai_price_eur",
    "ai_year",
    "ai_mileage_km",
    "ai_fuel_type",
    "ai_transmission",
    "ai_critair",
    "ai_reliability_score_0_to_25",
    "ai_buyer_suitability_score_0_to_20",
    "ai_price_value_score_0_to_15",
    "ai_running_cost_score_0_to_10",
    "ai_resale_ease_score_1_to_5",
    "ai_spare_parts_availability_score_1_to_10",
    "ai_short_reason",
    "ai_questions_to_ask_seller",
    "open_ad"
]

existing_default_columns = [
    col for col in default_columns if col in filtered_df.columns
]

existing_default_columns = put_url_last(existing_default_columns)

with st.expander("Choose columns to display"):
    selected_columns = st.multiselect(
        "Columns",
        filtered_df.columns.tolist(),
        default=existing_default_columns,
        format_func=display_name
    )

selected_columns = put_url_last(selected_columns)

if not selected_columns:
    selected_columns = existing_default_columns


# -----------------------------
# Main table
# -----------------------------
st.subheader("Ranked cars")

display_df = filtered_df[selected_columns].copy()

column_config = {}

for col in display_df.columns:
    column_config[col] = display_name(col)

if "open_ad" in display_df.columns:
    column_config["open_ad"] = st.column_config.LinkColumn(
        "url",
        display_text="Open ad"
    )

if "source_url" in display_df.columns:
    column_config["source_url"] = st.column_config.LinkColumn(
        "url",
        display_text="Open ad"
    )

if "url" in display_df.columns:
    column_config["url"] = st.column_config.LinkColumn(
        "url",
        display_text="Open ad"
    )

if "ai_total_score_0_to_100" in display_df.columns:
    column_config["ai_total_score_0_to_100"] = st.column_config.ProgressColumn(
        "total_score_0_to_100",
        min_value=0,
        max_value=100
    )

if "ai_confidence_0_to_1" in display_df.columns:
    column_config["ai_confidence_0_to_1"] = st.column_config.ProgressColumn(
        "confidence_0_to_1",
        min_value=0,
        max_value=1
    )

st.dataframe(
    display_df,
    use_container_width=True,
    height=650,
    column_config=column_config
)


# -----------------------------
# Download filtered CSV
# Clean column names in downloaded file too
# -----------------------------
download_df = filtered_df[selected_columns].copy()
download_df = download_df.rename(columns={col: display_name(col) for col in download_df.columns})

csv_data = download_df.to_csv(index=False, encoding="utf-8-sig")

st.download_button(
    label="Download filtered CSV",
    data=csv_data,
    file_name="filtered_ranked_cars_clean_columns.csv",
    mime="text/csv"
)


# -----------------------------
# Detail viewer
# -----------------------------
st.subheader("Car detail viewer")

if len(filtered_df) > 0:
    car_names = filtered_df.get(
        "ai_car_name",
        pd.Series(filtered_df.index.astype(str), index=filtered_df.index)
    ).fillna("Unknown car").astype(str)

    selected_index = st.selectbox(
        "Select a car",
        options=filtered_df.index.tolist(),
        format_func=lambda i: (
            f"{car_names.loc[i]} | "
            f"score: {filtered_df.loc[i].get('ai_total_score_0_to_100', '-')}"
        )
    )

    car = filtered_df.loc[selected_index]

    st.markdown(f"### {car.get('ai_car_name', 'Unknown car')}")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Score", car.get("ai_total_score_0_to_100", "-"))
    c2.metric("Recommendation", car.get("ai_recommendation", "-"))
    c3.metric("Price", f"{car.get('ai_price_eur', '-')} €")
    c4.metric("Mileage", f"{car.get('ai_mileage_km', '-')} km")

    st.write("**Reason:**")
    st.write(car.get("ai_short_reason", ""))

    st.write("**Known risks:**")
    st.write(car.get("ai_known_risks", ""))

    st.write("**Questions to ask seller:**")
    st.write(car.get("ai_questions_to_ask_seller", ""))

    url = car.get("source_url", car.get("url", None))

    if pd.notna(url):
        st.link_button("Open Leboncoin ad", url)

    with st.expander("Original description"):
        st.write(car.get("original_detail_description", ""))

    with st.expander("Raw text"):
        st.write(car.get("original_raw_text", ""))