import os

import psycopg2
from datetime import datetime

DATABASE_NAME = os.getenv("DATABASE_NAME")
DATABASE_USER = os.getenv("DATABASE_USER")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_HOST = os.getenv("DATABASE_HOST")
DATABASE_PORT = os.getenv("DATABASE_PORT")

def format_tweet(row):
    return {
        'id': row[0],
        'user_screen_name': row[1],
        'full_text': row[2],
        'created_at': f"{row[3].month}/{row[3].day}/{row[3].year} {row[3].minute}:{row[3].second} CST",
    }


def fetch(status: str) -> list[dict[str, str]] | None:
    results = []
    try:
        #conn = psycopg2.connect(DATABASE_URL)
        conn = psycopg2.connect(
                database=DATABASE_NAME,
                user=DATABASE_USER,
                password=DATABASE_PASSWORD,
                host=DATABASE_HOST,
                port=DATABASE_PORT,
        )
        cur = conn.cursor()

        cur.execute(f"""select id, user_screen_name, full_text, to_timestamp(created_at_unix) AT TIME ZONE 'America/Chicago'
        from twitter_tweets 
        where status = '{status}'
        order by created_at_unix desc 
        limit 10""")

        rows = cur.fetchall()
        for row in rows:
            results.append(format_tweet(row))

        # conn.commit()
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


def update(id: str, response_fact: str, status: str) -> None:
    try:
        #conn = psycopg2.connect(DATABASE_URL)
        conn = psycopg2.connect(
                database=DATABASE_NAME,
                user=DATABASE_USER,
                password=DATABASE_PASSWORD,
                host=DATABASE_HOST,
                port=DATABASE_PORT,
        )
        cur = conn.cursor()

        cur.execute(
            """UPDATE twitter_tweets
            SET response_fact = %s,
            status = %s
            where id = %s"""
            , (
                response_fact,
                status,
                id,
            ))

        conn.commit()
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

