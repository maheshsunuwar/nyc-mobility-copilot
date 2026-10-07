import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
DB_CONFIG = {
    "host": os.getenv("HOST", 'localhostt'),
    "port": os.getenv("PORT", 5432),
    "dbname": os.getenv("DBNAME", "mobility_warehouse"),
    "user": os.getenv("DBUSER", "agent_reader"),
    "password": os.getenv("PASSWORD", "agent_readerdev_pw"),
}

# Question/SQL pairs that teach the model your project's vocabulary and
# table relationships -- extend this list as you find new failure patterns
FEW_SHOT_EXAMPLES = [
    {
        "question": "How many yellow cab trips were there in January 2026?",
        "sql": "SELECT total_trips FROM monthly_summary WHERE taxi_type = 'yellow' AND year = 2026 AND month = 1;",
    },
    {
        "question": "Which pickup zone had the most trips at 2pm?",
        "sql": "SELECT pickup_location_id, trip_count FROM stg_trips_by_hour_zone WHERE pickup_hour = 14 ORDER BY trip_count DESC LIMIT 1;",
    },
    {
        "question": "Which hour is the busiest for taxi pickups overall?",
        "sql": "SELECT pickup_hour, SUM(trip_count) AS total FROM stg_trips_by_hour_zone GROUP BY pickup_hour ORDER BY total DESC LIMIT 1;",
    },
    {
        "question": "Historically, what hour has the cheapest average fare?",
        "sql": "SELECT pickup_hour, AVG(avg_fare) AS avg_fare FROM stg_trips_by_hour_zone GROUP BY pickup_hour ORDER BY avg_fare ASC LIMIT 1;",
    },
]

def get_live_schema() -> str:
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("""
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_name IN ('stg_trips_by_hour_zone', 'monthly_summary')
        ORDER BY table_name, ordinal_position;
    """)

    rows = cur.fetchall()
    cur.close()
    conn.close()

    schema_text = ""
    current_table = None
    for table, column, dtype in rows:
        if table != current_table:
            schema_text += f"\nTable: {table}\n"
            current_table = table
        schema_text += f" - {column} ({dtype})\n"

    return schema_text
