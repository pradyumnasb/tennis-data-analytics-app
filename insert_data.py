import os
print("🚀 Script started...")

import requests
import psycopg2
from dotenv import load_dotenv

# -------------------------
# Load environment variables
# -------------------------
load_dotenv()

API_KEY = os.getenv("SPORTRADAR_API_KEY")

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

print("DB_HOST:", DB_HOST)
print("DB_NAME:", DB_NAME)

try:
    # -------------------------
    # Connect to Neon PostgreSQL
    # -------------------------
    conn = psycopg2.connect(
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        sslmode="require"
    )

    print("✅ Connected to Neon!")

    cursor = conn.cursor()

    # ======================================================
    # 1️⃣ Fetch Competitions
    # ======================================================
    print("\n📡 Fetching competitions...")

    competitions_url = f"https://api.sportradar.com/tennis/trial/v3/en/competitions.json?api_key={API_KEY}"
    competitions_response = requests.get(competitions_url)

    print("Status Code:", competitions_response.status_code)

    if competitions_response.status_code != 200:
        print(competitions_response.text)
        raise Exception("❌ Failed to fetch competitions")

    competitions_data = competitions_response.json()

    print("Total competitions from API:", len(competitions_data.get("competitions", [])))

    count = 0

    for comp in competitions_data.get("competitions", []):
        count += 1

        category = comp.get("category", {})
        category_id = category.get("id")
        category_name = category.get("name", "Unknown")

        if category_id:
            cursor.execute("""
                INSERT INTO Categories (category_id, category_name)
                VALUES (%s, %s)
                ON CONFLICT (category_id) DO NOTHING;
            """, (category_id, category_name))

        cursor.execute("""
            INSERT INTO Competitions
            (competition_id, competition_name, type, gender, parent_id, category_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (competition_id) DO NOTHING;
        """, (
            comp.get("id"),
            comp.get("name", "Unknown"),
            comp.get("type", "Unknown"),
            comp.get("gender", "unknown"),
            comp.get("parent_id"),
            category_id
        ))

        if count % 100 == 0:
            print(f"✅ Inserted {count} competitions...")
            conn.commit()

    print(f"🎯 Total competitions inserted: {count}")

    # ======================================================
    # 2️⃣ Fetch Complexes
    # ======================================================
    print("\n📡 Fetching complexes...")

    complexes_url = f"https://api.sportradar.com/tennis/trial/v3/en/complexes.json?api_key={API_KEY}"
    complexes_response = requests.get(complexes_url)

    print("Status Code:", complexes_response.status_code)

    if complexes_response.status_code != 200:
        print(complexes_response.text)
        raise Exception("❌ Failed to fetch complexes")

    complexes_data = complexes_response.json()

    compx_count = 0
    venue_count = 0

    for compx in complexes_data.get("complexes", []):
        compx_count += 1

        cursor.execute("""
            INSERT INTO Complexes (complex_id, complex_name)
            VALUES (%s, %s)
            ON CONFLICT (complex_id) DO NOTHING;
        """, (
            compx.get("id"),
            compx.get("name", "Unknown")
        ))

        for venue in compx.get("venues", []):
            venue_count += 1

            cursor.execute("""
                INSERT INTO Venues
                (venue_id, venue_name, city_name, country_name, country_code, timezone, complex_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (venue_id) DO NOTHING;
            """, (
                venue.get("id"),
                venue.get("name", "Unknown"),
                venue.get("city_name", "Unknown"),
                venue.get("country_name", "Unknown"),
                venue.get("country_code", "UNK"),
                venue.get("timezone", "Unknown"),
                compx.get("id")
            ))

        if compx_count % 50 == 0:
            print(f"🏟️ Complexes: {compx_count}, Venues: {venue_count}")
            conn.commit()

    # ======================================================
    # 3️⃣ Fetch Rankings
    # ======================================================
    print("\n📡 Fetching rankings...")

    rankings_url = f"https://api.sportradar.com/tennis/trial/v3/en/rankings.json?api_key={API_KEY}"
    rankings_response = requests.get(rankings_url)

    print("Status Code:", rankings_response.status_code)

    if rankings_response.status_code != 200:
        print(rankings_response.text)
        raise Exception("❌ Failed to fetch rankings")

    rankings_data = rankings_response.json()

    rank_count = 0

    for ranking in rankings_data.get("rankings", []):
        for comp_rank in ranking.get("competitor_rankings", []):
            rank_count += 1

            competitor = comp_rank.get("competitor", {})
            competitor_id = competitor.get("id")

            cursor.execute("""
                INSERT INTO Competitors
                (competitor_id, name, country, country_code, abbreviation)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (competitor_id) DO NOTHING;
            """, (
                competitor_id,
                competitor.get("name", "Unknown"),
                competitor.get("country", "Unknown"),
                competitor.get("country_code", "UNK"),
                competitor.get("abbreviation", "UNK")
            ))

            cursor.execute("""
                INSERT INTO Competitor_Rankings
                (rank, movement, points, competitions_played, competitor_id)
                VALUES (%s, %s, %s, %s, %s);
            """, (
                comp_rank.get("rank", 0),
                comp_rank.get("movement", 0),
                comp_rank.get("points", 0),
                comp_rank.get("competitions_played", 0),
                competitor_id
            ))

        if rank_count % 100 == 0:
            print(f"📊 Inserted {rank_count} rankings...")
            conn.commit()

    # -------------------------
    # Final commit
    # -------------------------
    conn.commit()

    cursor.close()
    conn.close()

    print("\n🎉 ALL DATA INSERTED SUCCESSFULLY!")

except Exception as e:
    print("❌ ERROR:", e)