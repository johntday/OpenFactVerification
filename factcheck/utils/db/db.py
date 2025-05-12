import psycopg2
from datetime import datetime

DATABASE_URL = "postgresql://n8n:ImrfgtZHkK7Y9lnEvbSd@localhost:5432/n8ndb"

def format_tweet(row):
    return {
        'id': row[0],
        'user_screen_name': row[1],
        'full_text': row[2],
        'created_at': f"{row[3].month}/{row[3].day}/{row[3].year} {row[3].minute}:{row[3].second} CST",
    }


def fetch() -> list[dict[str, str]] | None:
    results = []
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        cur.execute("""select id, user_screen_name, full_text, to_timestamp(created_at_unix) AT TIME ZONE 'America/Chicago'
        from twitter_tweets 
        where status = 'fact' 
        order by created_at_unix desc 
        limit 10""")

        rows = cur.fetchall()
        for row in rows:
            results.append(format_tweet(row))

        return results
    except Exception as e:
        print(f"Error saving tweet to database: {e}")
        return results
    finally:
        try:
            if cur:
                cur.close()
        except Exception as e:
            pass
        try:
            if conn:
                conn.close()
        except Exception as e:
            pass


def update(id: str, response_fact: str):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        cur.execute(
            """UPDATE twitter_tweets
            SET response_fact = %s,
            status = 'done'
            where id = %s"""
            , (
                response_fact,
                id
            ))
    except Exception as e:
        print(f"Error saving tweet to database: {e}")
    finally:
        try:
            if cur:
                cur.close()
        except Exception as e:
            pass
        try:
            if conn:
                conn.close()
        except Exception as e:
            pass






if __name__ == "__main__":
    fetch()

