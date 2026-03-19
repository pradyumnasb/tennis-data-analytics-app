import streamlit as st
import pandas as pd
import psycopg2
import os

# -------------------------
# Database Connection
# -------------------------
def get_connection():
    return psycopg2.connect(
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        sslmode="require"   # 🔥 REQUIRED for Neon
    )

conn = get_connection()

st.title("🎾 Tennis Data Analytics Dashboard")

menu = st.sidebar.selectbox(
    "Select Option",
    ["Dashboard", "Competitions", "Venues", "Competitor Rankings"]
)

# -------------------------
# Dashboard
# -------------------------
if menu == "Dashboard":

    competitors = pd.read_sql("SELECT COUNT(*) as total FROM competitors", conn)
    competitions = pd.read_sql("SELECT COUNT(*) as total FROM competitions", conn)
    venues = pd.read_sql("SELECT COUNT(*) as total FROM venues", conn)

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Competitors", competitors.iloc[0]["total"])
    col2.metric("Total Competitions", competitions.iloc[0]["total"])
    col3.metric("Total Venues", venues.iloc[0]["total"])


# -------------------------
# Competitions
# -------------------------
elif menu == "Competitions":

    query = """
    SELECT cat.category_name, COUNT(c.competition_id) AS total_competitions
    FROM competitions c
    JOIN categories cat
    ON c.category_id = cat.category_id
    GROUP BY cat.category_name
    ORDER BY total_competitions DESC
    """

    df = pd.read_sql(query, conn)

    st.dataframe(df)
    st.bar_chart(df.set_index("category_name"))


# -------------------------
# Venues
# -------------------------
elif menu == "Venues":

    query = """
    SELECT c.complex_name, COUNT(v.venue_id) AS total_venues
    FROM complexes c
    JOIN venues v
    ON c.complex_id = v.complex_id
    GROUP BY c.complex_name
    ORDER BY total_venues DESC
    """

    df = pd.read_sql(query, conn)

    st.dataframe(df)
    st.bar_chart(df.set_index("complex_name"))


# -------------------------
# Rankings
# -------------------------
elif menu == "Competitor Rankings":

    query = """
    SELECT comp.name, r.rank, r.points
    FROM competitor_rankings r
    JOIN competitors comp
    ON r.competitor_id = comp.competitor_id
    ORDER BY r.rank
    LIMIT 10
    """

    df = pd.read_sql(query, conn)

    st.table(df)

    name = st.text_input("Search Player")

    if name:

        search_query = f"""
        SELECT comp.name, r.rank, r.points
        FROM competitor_rankings r
        JOIN competitors comp
        ON r.competitor_id = comp.competitor_id
        WHERE comp.name ILIKE '%{name}%'
        """

        result = pd.read_sql(search_query, conn)

        st.dataframe(result)