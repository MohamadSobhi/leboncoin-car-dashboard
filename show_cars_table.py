import html
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components


CSV_FILE = "leboncoin_combined_results.csv"


st.set_page_config(
    page_title="Leboncoin Car Ranking",
    page_icon="🚗",
    layout="wide"
)

st.title("🚗 Leboncoin Car Decision Table")
st.caption("Ranked used-car results from Leboncoin")


# -----------------------------
# Load data
# -----------------------------
@st.cache_data
def load_data(csv_file):
    df = pd.read_csv(csv_file)

    numeric_cols = [
        "recommendation_score",
        "price_score",
        "horsepower_score",
        "year_score",
        "mileage_score",
        "location_score",
        "seller_score",
        "price_eur",
        "year",
        "mileage_km",
        "horsepower",
        "doors",
        "critair_estimated",
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "recommendation_score" in df.columns:
        df = df.sort_values(
            by=["recommendation_score", "price_score", "year", "mileage_km"],
            ascending=[False, False, False, True],
            na_position="last"
        )

    return df


def format_number(value):
    if pd.isna(value):
        return "-"

    try:
        return f"{int(value):,}".replace(",", " ")
    except Exception:
        return str(value)


def format_price(value):
    if pd.isna(value):
        return "-"

    try:
        return f"{int(value):,} €".replace(",", " ")
    except Exception:
        return str(value)


def format_score(value):
    if pd.isna(value):
        return "-"

    try:
        return str(int(value))
    except Exception:
        return str(value)


def make_clickable_car_name(name, url):
    if pd.isna(name):
        name = "Unknown car"

    name = html.escape(str(name))

    if pd.isna(url) or str(url).strip() == "":
        return name

    url = html.escape(str(url))
    return f'<a href="{url}" target="_blank">{name}</a>'


def build_html_table(df):
    table_cols = [
        "car_name",
        "recommendation_score",
        "price_eur",
        "year",
        "mileage_km",
        "fuel",
        "transmission",
        "seller_type",
        "location",
        "horsepower",
        "doors",
        "critair_estimated",
        "price_score",
        "horsepower_score",
        "year_score",
        "mileage_score",
        "location_score",
        "seller_score",
    ]

    table_cols = [c for c in table_cols if c in df.columns]

    display_df = df[table_cols].copy()

    if "car_name" in display_df.columns and "url" in df.columns:
        display_df["car_name"] = [
            make_clickable_car_name(name, url)
            for name, url in zip(df["car_name"], df["url"])
        ]

    rename_cols = {
        "car_name": "Car name",
        "recommendation_score": "Score",
        "price_eur": "Price",
        "year": "Year",
        "mileage_km": "Mileage",
        "fuel": "Fuel",
        "transmission": "Transmission",
        "seller_type": "Seller",
        "location": "Location",
        "horsepower": "HP",
        "doors": "Doors",
        "critair_estimated": "Crit’Air",
        "price_score": "Price score",
        "horsepower_score": "HP score",
        "year_score": "Year score",
        "mileage_score": "Mileage score",
        "location_score": "Location score",
        "seller_score": "Seller score",
    }

    display_df = display_df.rename(columns=rename_cols)

    if "Price" in display_df.columns:
        display_df["Price"] = display_df["Price"].apply(format_price)

    if "Mileage" in display_df.columns:
        display_df["Mileage"] = display_df["Mileage"].apply(
            lambda x: "-" if pd.isna(x) else f"{int(x):,} km".replace(",", " ")
        )

    for col in [
        "Score",
        "Year",
        "HP",
        "Doors",
        "Crit’Air",
        "Price score",
        "HP score",
        "Year score",
        "Mileage score",
        "Location score",
        "Seller score",
    ]:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(format_score)

    html_table = display_df.to_html(
        escape=False,
        index=False,
        classes="car-table"
    )

    css = """
    <style>
    body {
        background-color: #0e1117;
        color: #fafafa;
        font-family: Arial, sans-serif;
        margin: 0;
        padding: 0;
    }

    .table-container {
        width: 100%;
        overflow-x: auto;
        overflow-y: auto;
    }

    .car-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 14px;
        color: #fafafa;
    }

    .car-table th {
        background-color: #262730;
        color: #fafafa;
        padding: 10px;
        border-bottom: 2px solid #444;
        text-align: left;
        position: sticky;
        top: 0;
        z-index: 1;
        white-space: nowrap;
    }

    .car-table td {
        padding: 9px;
        border-bottom: 1px solid #333;
        vertical-align: top;
        white-space: nowrap;
    }

    .car-table tr:hover {
        background-color: #1f2430;
    }

    .car-table a {
        color: #4da3ff;
        font-weight: 600;
        text-decoration: none;
    }

    .car-table a:hover {
        text-decoration: underline;
    }
    </style>
    """

    return css + f"""
    <div class="table-container">
        {html_table}
    </div>
    """


# -----------------------------
# Read CSV
# -----------------------------
try:
    df = load_data(CSV_FILE)
except FileNotFoundError:
    st.error(f"CSV file not found: {CSV_FILE}")
    st.stop()


# -----------------------------
# Sidebar filters
# -----------------------------
st.sidebar.header("Filters")

search_text = st.sidebar.text_input("Search car / city / fuel / seller")


if "fuel" in df.columns:
    fuel_options = sorted(df["fuel"].dropna().astype(str).unique().tolist())
else:
    fuel_options = []

selected_fuels = st.sidebar.multiselect(
    "Fuel type",
    fuel_options,
    default=fuel_options
)


if "transmission" in df.columns:
    transmission_options = sorted(df["transmission"].dropna().astype(str).unique().tolist())
else:
    transmission_options = []

selected_transmissions = st.sidebar.multiselect(
    "Transmission",
    transmission_options,
    default=transmission_options
)


if "seller_type" in df.columns:
    seller_options = sorted(df["seller_type"].dropna().astype(str).unique().tolist())
else:
    seller_options = []

selected_sellers = st.sidebar.multiselect(
    "Seller type",
    seller_options,
    default=seller_options
)


if "recommendation_score" in df.columns:
    min_score = int(df["recommendation_score"].fillna(0).min())
    max_score = int(df["recommendation_score"].fillna(100).max())

    score_range = st.sidebar.slider(
        "Recommendation score",
        min_value=0,
        max_value=100,
        value=(min_score, max_score)
    )
else:
    score_range = (0, 100)


if "price_eur" in df.columns:
    min_price = int(df["price_eur"].fillna(0).min())
    max_price = int(df["price_eur"].fillna(10000).max())

    price_range = st.sidebar.slider(
        "Price (€)",
        min_value=0,
        max_value=max(1000, max_price),
        value=(min_price, max_price)
    )
else:
    price_range = (0, 999999)


if "year" in df.columns:
    min_year = int(df["year"].fillna(2000).min())
    max_year = int(df["year"].fillna(2026).max())

    year_range = st.sidebar.slider(
        "Year",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year)
    )
else:
    year_range = (1900, 2100)


if "mileage_km" in df.columns:
    min_mileage = int(df["mileage_km"].fillna(0).min())
    max_mileage = int(df["mileage_km"].fillna(300000).max())

    mileage_range = st.sidebar.slider(
        "Mileage km",
        min_value=0,
        max_value=max(1000, max_mileage),
        value=(min_mileage, max_mileage)
    )
else:
    mileage_range = (0, 999999)


if "horsepower" in df.columns:
    min_hp = int(df["horsepower"].fillna(0).min())
    max_hp = int(df["horsepower"].fillna(300).max())

    horsepower_range = st.sidebar.slider(
        "Horsepower",
        min_value=0,
        max_value=max(50, max_hp),
        value=(min_hp, max_hp)
    )
else:
    horsepower_range = (0, 999999)


# -----------------------------
# Apply filters
# -----------------------------
filtered_df = df.copy()

if search_text:
    search_cols = [
        "car_name",
        "fuel",
        "transmission",
        "seller_type",
        "location",
        "raw_text",
    ]

    existing_search_cols = [c for c in search_cols if c in filtered_df.columns]

    mask = pd.Series(False, index=filtered_df.index)

    for col in existing_search_cols:
        mask = mask | filtered_df[col].fillna("").astype(str).str.contains(
            search_text,
            case=False,
            na=False
        )

    filtered_df = filtered_df[mask]


if selected_fuels and "fuel" in filtered_df.columns:
    filtered_df = filtered_df[
        filtered_df["fuel"].astype(str).isin(selected_fuels)
    ]


if selected_transmissions and "transmission" in filtered_df.columns:
    filtered_df = filtered_df[
        filtered_df["transmission"].astype(str).isin(selected_transmissions)
    ]


if selected_sellers and "seller_type" in filtered_df.columns:
    filtered_df = filtered_df[
        filtered_df["seller_type"].astype(str).isin(selected_sellers)
    ]


if "recommendation_score" in filtered_df.columns:
    filtered_df = filtered_df[
        filtered_df["recommendation_score"].between(score_range[0], score_range[1])
    ]


if "price_eur" in filtered_df.columns:
    filtered_df = filtered_df[
        filtered_df["price_eur"].between(price_range[0], price_range[1])
    ]


if "year" in filtered_df.columns:
    filtered_df = filtered_df[
        filtered_df["year"].between(year_range[0], year_range[1])
    ]


if "mileage_km" in filtered_df.columns:
    filtered_df = filtered_df[
        filtered_df["mileage_km"].between(mileage_range[0], mileage_range[1])
    ]


if "horsepower" in filtered_df.columns:
    filtered_df = filtered_df[
        filtered_df["horsepower"].between(horsepower_range[0], horsepower_range[1])
    ]


# -----------------------------
# Summary metrics
# -----------------------------
col1, col2, col3, col4, col5, col6 = st.columns(6)

col1.metric("Cars shown", len(filtered_df))

if "recommendation_score" in filtered_df.columns and len(filtered_df) > 0:
    col2.metric("Best score", int(filtered_df["recommendation_score"].max()))
else:
    col2.metric("Best score", "-")

if "price_eur" in filtered_df.columns and len(filtered_df) > 0:
    col3.metric("Lowest price", format_price(filtered_df["price_eur"].min()))
else:
    col3.metric("Lowest price", "-")

if "year" in filtered_df.columns and len(filtered_df) > 0:
    col4.metric("Newest year", int(filtered_df["year"].max()))
else:
    col4.metric("Newest year", "-")

if "mileage_km" in filtered_df.columns and len(filtered_df) > 0:
    col5.metric(
        "Lowest mileage",
        f"{format_number(filtered_df['mileage_km'].min())} km"
    )
else:
    col5.metric("Lowest mileage", "-")

if "horsepower" in filtered_df.columns and len(filtered_df) > 0:
    col6.metric("Max horsepower", int(filtered_df["horsepower"].max()))
else:
    col6.metric("Max horsepower", "-")


# -----------------------------
# Ranked table
# -----------------------------
st.subheader("Ranked cars")

if len(filtered_df) == 0:
    st.warning("No cars match your filters.")
else:
    html_table = build_html_table(filtered_df)
    components.html(html_table, height=700, scrolling=True)


# -----------------------------
# Download filtered CSV
# -----------------------------
download_df = filtered_df.copy()

csv_data = download_df.to_csv(index=False, encoding="utf-8-sig")

st.download_button(
    label="Download filtered CSV",
    data=csv_data,
    file_name="filtered_ranked_cars.csv",
    mime="text/csv"
)


# -----------------------------
# Detail viewer
# -----------------------------
st.subheader("Car detail viewer")

if len(filtered_df) > 0:
    car_names = filtered_df["car_name"].fillna("Unknown car").astype(str)

    selected_index = st.selectbox(
        "Select a car",
        options=filtered_df.index.tolist(),
        format_func=lambda i: (
            f"{car_names.loc[i]} | "
            f"score: {format_score(filtered_df.loc[i].get('recommendation_score', '-'))}"
        )
    )

    car = filtered_df.loc[selected_index]

    car_title = car.get("car_name", "Unknown car")
    car_url = car.get("url", None)

    if pd.notna(car_url):
        st.markdown(f"### [{car_title}]({car_url})")
    else:
        st.markdown(f"### {car_title}")

    c1, c2, c3, c4, c5, c6, c7 = st.columns(7)

    c1.metric("Score", format_score(car.get("recommendation_score", "-")))
    c2.metric("Price", format_price(car.get("price_eur", "-")))
    c3.metric("Year", format_score(car.get("year", "-")))
    c4.metric("Mileage", f"{format_number(car.get('mileage_km', '-'))} km")
    c5.metric("Horsepower", format_score(car.get("horsepower", "-")))
    c6.metric("Doors", format_score(car.get("doors", "-")))
    c7.metric("Crit’Air", format_score(car.get("critair_estimated", "-")))

    st.write("**Fuel:**")
    st.write(car.get("fuel", "-"))

    st.write("**Transmission:**")
    st.write(car.get("transmission", "-"))

    st.write("**Seller type:**")
    st.write(car.get("seller_type", "-"))

    st.write("**Location:**")
    st.write(car.get("location", "-"))

    if pd.notna(car_url):
        st.link_button("Open Leboncoin ad", car_url)

    with st.expander("Score details"):
        st.write(f"Price score: {format_score(car.get('price_score', '-'))}")
        st.write(f"Horsepower score: {format_score(car.get('horsepower_score', '-'))}")
        st.write(f"Year score: {format_score(car.get('year_score', '-'))}")
        st.write(f"Mileage score: {format_score(car.get('mileage_score', '-'))}")
        st.write(f"Location score: {format_score(car.get('location_score', '-'))}")
        st.write(f"Seller score: {format_score(car.get('seller_score', '-'))}")

    with st.expander("Raw text"):
        st.write(car.get("raw_text", ""))

    with st.expander("Screen-reader text"):
        st.write(car.get("sr_text", ""))