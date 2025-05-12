import psycopg2

DATABASE_URL = "postgresql://n8n:ImrfgtZHkK7Y9lnEvbSd@localhost:5432/n8ndb"

def format_tweet(row):
    return {
        'id': row[0],
        'user_screen_name': row[1],
        'full_text': row[2],
        'created_at': row[3],
    }


def fetch():
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

if __name__ == "__main__":
    fetch()

# def save_to_database(tweets):
#     try:
#         # Write tweets to postgres database
#         conn = psycopg2.connect(DATABASE_URL)
#         cur = conn.cursor()
#
#         if os.getenv('EXCLUDE_RT') == '1':
#             tweets_to_store = [format_tweet(tweet) for tweet in tweets if not tweet.full_text.startswith('RT')]
#         else:
#             tweets_to_store = [format_tweet(tweet) for tweet in tweets]
#
#         for tweet in tweets_to_store:
#             if tweet['full_text'].endswith("…") or len(clean_text(tweet['full_text']).strip()) < 10:
#                 continue
#
#             answer = openai_utils.call_openai(
#                 prompt=tweet['full_text'],
#             )
#             if not answer or not answer.answer or answer.answer == False:
#                 continue
#
#             cur.execute("""
#                 INSERT INTO twitter_tweets (
#                     """ + TABLE_COLUMNS_STR + """
#                 ) VALUES (%s, %s, %s, %s, %s)
#                 ON CONFLICT (id) DO NOTHING
#             """, (
#                 tweet['id'],
#                 tweet['created_at_unix'],
#                 clean_text(tweet['full_text']),
#                 tweet['user_screen_name'],
#                 tweet['tweet_url']
#                 # tweet['created_at']
#             ))
#         conn.commit()
#     except Exception as e:
#         print(f"Error saving tweet to database: {e}")
#     finally:
#         try:
#             if cur:
#                 cur.close()
#         except Exception as e:
#             pass
#         try:
#             if conn:
#                 conn.close()
#         except Exception as e:
#             pass
