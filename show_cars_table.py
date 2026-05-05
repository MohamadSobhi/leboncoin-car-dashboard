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


# -----------------------------
# Load data
# -----------------------------
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
        "ai_horsepower_hp",
        "ai_doors",
        "original_year",
        "original_price_eur",
        "original_mileage_km",
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def display_name(col):
    """
    Clean column names only for display.
    Internal CSV column names stay unchanged.

    Examples:
    ai_car_name -> car_name
    ai_total_score_0_to_100 -> total_score_0_to_100
    original_year -> year
    original_fuel -> fuel
    original_transmission -> transmission
    open_ad -> url
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
    Put URL/open-ad column at the end.
    """
    url_cols = [c for c in ["open_ad", "source_url", "url"] if c in columns]
    normal_cols = [c for c in columns if c not in url_cols]

    if "open_ad" in url_cols:
        return normal_cols + ["open_ad"]
    elif "source_url" in url_cols:
        return normal_cols + ["source_url"]
    elif "url" in url_cols:
        return normal_cols + ["url"]

    return normal_cols


def get_first_existing_column(df, possible_columns):
    for col in possible_columns:
        if col in df.columns:
            return col
    return None


try:
    df = load_data(CSV_FILE)
except FileNotFoundError:
    st.error(f"CSV file not found: {CSV_FILE}")
    st.stop()


# -----------------------------
# Choose preferred source columns
# -----------------------------
year_col = get_first_existing_column(df, ["original_year", "ai_year", "year"])
fuel_col = get_first_existing_column(df, ["original_fuel", "ai_fuel_type", "fuel"])
transmission_col = get_first_existing_column(
    df,
    ["original_transmission", "ai_transmission", "transmission"]
)
price_col = get_first_existing_column(df, ["ai_price_eur", "original_price_eur", "price_eur"])
mileage_col = get_first_existing_column(df, ["ai_mileage_km", "original_mileage_km", "mileage_km"])
score_col = get_first_existing_column(df, ["ai_total_score_0_to_100"])
recommendation_col = get_first_existing_column(df, ["ai_recommendation"])
car_name_col = get_first_existing_column(df, ["ai_car_name", "original_title", "title"])


# -----------------------------
# Sort by score
# -----------------------------
if score_col:
    df = df.sort_values(score_col, ascending=False)


# -----------------------------
# Add clickable URL column
# -----------------------------
if "source_url" in df.columns:
    df["open_ad"] = df["source_url"]
elif "url" in df.columns:
    df["open_ad"] = df["url"]
elif "original_url" in df.columns:
    df["open_ad"] = df["original_url"]


# -----------------------------
# Sidebar filters
# -----------------------------
st.sidebar.header("Filters")

search_text = st.sidebar.text_input("Search car name / brand / model")

if recommendation_col:
    recommendations = sorted(df[recommendation_col].dropna().unique().tolist())
else:
    recommendations = []

selected_recommendations = st.sidebar.multiselect(
    "Recommendation",
    recommendations,
    default=recommendations
)

if fuel_col:
    fuel_options = sorted(df[fuel_col].dropna().astype(str).unique().tolist())
else:
    fuel_options = []

selected_fuels = st.sidebar.multiselect(
    "Fuel type",
    fuel_options,
    default=fuel_options
)

if score_col:
    score_range = st.sidebar.slider(
        "Total score",
        min_value=0,
        max_value=100,
        value=(
            int(df[score_col].fillna(0).min()),
            int(df[score_col].fillna(100).max())
        )
    )
else:
    score_range = (0, 100)

if price_col:
    max_price_value = int(df[price_col].fillna(10000).max())

    price_range = st.sidebar.slider(
        "Price (€)",
        min_value=0,
        max_value=max(1000, max_price_value),
        value=(
            int(df[price_col].fillna(0).min()),
            max_price_value
        )
    )
else:
    price_range = (0, 999999)

if year_col:
    df[year_col] = pd.to_numeric(df[year_col], errors="coerce")

    min_year_value = int(df[year_col].fillna(2000).min())
    max_year_value = int(df[year_col].fillna(2026).max())

    year_range = st.sidebar.slider(
        "Year",
        min_value=min_year_value,
        max_value=max_year_value,
        value=(min_year_value, max_year_value)
    )
else:
    year_range = (1900, 2100)

if mileage_col:
    max_mileage_value = int(df[mileage_col].fillna(300000).max())

    mileage_range = st.sidebar.slider(
        "Mileage km",
        min_value=0,
        max_value=max(1000, max_mileage_value),
        value=(
            int(df[mileage_col].fillna(0).min()),
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
        "title",
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

if selected_recommendations and recommendation_col:
    filtered_df = filtered_df[
        filtered_df[recommendation_col].isin(selected_recommendations)
    ]

if selected_fuels and fuel_col:
    filtered_df = filtered_df[
        filtered_df[fuel_col].astype(str).isin(selected_fuels)
    ]

if score_col:
    filtered_df = filtered_df[
        filtered_df[score_col].between(score_range[0], score_range[1])
    ]

if price_col:
    filtered_df = filtered_df[
        filtered_df[price_col].between(price_range[0], price_range[1])
    ]

if year_col:
    filtered_df[year_col] = pd.to_numeric(filtered_df[year_col], errors="coerce")
    filtered_df = filtered_df[
        filtered_df[year_col].between(year_range[0], year_range[1])
    ]

if mileage_col:
    filtered_df = filtered_df[
        filtered_df[mileage_col].between(mileage_range[0], mileage_range[1])
    ]


# -----------------------------
# Summary metrics
# -----------------------------
col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Cars shown", len(filtered_df))

if score_col and len(filtered_df) > 0:
    col2.metric("Best score", int(filtered_df[score_col].max()))
else:
    col2.metric("Best score", "-")

if price_col and len(filtered_df) > 0:
    col3.metric("Lowest price", f"{int(filtered_df[price_col].min()):,} €")
else:
    col3.metric("Lowest price", "-")

if year_col and len(filtered_df) > 0:
    col4.metric("Newest year", int(filtered_df[year_col].max()))
else:
    col4.metric("Newest year", "-")

if mileage_col and len(filtered_df) > 0:
    col5.metric("Lowest mileage", f"{int(filtered_df[mileage_col].min()):,} km")
else:
    col5.metric("Lowest mileage", "-")


# -----------------------------
# Default columns to display
# -----------------------------
default_columns = [
    "ai_car_name",
    "ai_total_score_0_to_100",
    "ai_recommendation",
    "ai_price_eur",

    # Use original values here
    "original_year",
    "ai_mileage_km",
    "original_fuel",
    "original_transmission",

    "ai_critair",
    "ai_reliability_score_0_to_25",
    "ai_buyer_suitability_score_0_to_20",
    "ai_price_value_score_0_to_15",
    "ai_zfe_critair_score_0_to_10",
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


# -----------------------------
# Column selector
# -----------------------------
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

if score_col and score_col in display_df.columns:
    column_config[score_col] = st.column_config.ProgressColumn(
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
# With cleaned column names
# -----------------------------
download_df = filtered_df[selected_columns].copy()
download_df = download_df.rename(
    columns={col: display_name(col) for col in download_df.columns}
)

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
    if car_name_col:
        car_names = filtered_df[car_name_col].fillna("Unknown car").astype(str)
    else:
        car_names = pd.Series(
            filtered_df.index.astype(str),
            index=filtered_df.index
        )

    selected_index = st.selectbox(
        "Select a car",
        options=filtered_df.index.tolist(),
        format_func=lambda i: (
            f"{car_names.loc[i]} | "
            f"score: {filtered_df.loc[i].get(score_col, '-') if score_col else '-'}"
        )
    )

    car = filtered_df.loc[selected_index]

    st.markdown(f"### {car.get(car_name_col, 'Unknown car') if car_name_col else 'Unknown car'}")

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("Score", car.get(score_col, "-") if score_col else "-")
    c2.metric("Recommendation", car.get(recommendation_col, "-") if recommendation_col else "-")
    c3.metric("Price", f"{car.get(price_col, '-')} €" if price_col else "-")
    c4.metric("Year", car.get(year_col, "-") if year_col else "-")
    c5.metric("Mileage", f"{car.get(mileage_col, '-')} km" if mileage_col else "-")

    st.write("**Fuel:**")
    st.write(car.get(fuel_col, "-") if fuel_col else "-")

    st.write("**Transmission:**")
    st.write(car.get(transmission_col, "-") if transmission_col else "-")

    st.write("**Reason:**")
    st.write(car.get("ai_short_reason", ""))

    st.write("**Known risks:**")
    st.write(car.get("ai_known_risks", ""))

    st.write("**Questions to ask seller:**")
    st.write(car.get("ai_questions_to_ask_seller", ""))

    url = car.get("source_url", car.get("url", car.get("original_url", None)))

    if pd.notna(url):
        st.link_button("Open Leboncoin ad", url)

    with st.expander("Original description"):
        st.write(car.get("original_detail_description", ""))

    with st.expander("Raw text"):
        st.write(car.get("original_raw_text", ""))