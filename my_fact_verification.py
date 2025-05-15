import json
import os
import psycopg2
from factcheck import FactCheck
import argparse
from factcheck.utils.llmclient import CLIENTS
from factcheck.utils.multimodal import modal_normalization
from factcheck.utils.utils import load_yaml
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

def format_unix_timestamp(unix_timestamp) -> str:
    return datetime.utcfromtimestamp(unix_timestamp).strftime('%Y-%m-%d %H:%M')

def format_tweet(row):
    return {
        'id': row[0],
        'user_screen_name': row[1],
        'full_text': row[2],
        'created_at': format_unix_timestamp(row[3]),
    }

def fetch(status: str):
    results = []
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        cur.execute(f"""select id, user_screen_name, full_text, created_at_unix
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
        print(f"Error with fetch: status={status}: {e}")
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
        conn = psycopg2.connect(DATABASE_URL)
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
        print(f"Error with update: id={id}, response_fact={response_fact[:25]}, status={status}:  {e}")
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="gpt-4.1")
    parser.add_argument("--client", type=str, default='gpt', choices=CLIENTS.keys())
    parser.add_argument("--prompt", type=str, default="chatgpt_prompt")
    parser.add_argument("--retriever", type=str, default="serper")
    parser.add_argument("--modal", type=str, default="string")
    parser.add_argument("--input", type=str, default="")
    parser.add_argument("--api_config", type=str, default="factcheck/config/api_config.yaml")
    args = parser.parse_args()

    print(f'FACT_API_ENDPOINT={os.environ["FACT_API_ENDPOINT"]}')
    print(f'FACT_API_KEY={os.environ["FACT_API_KEY"]}')
    print(f'DATABASE_URL={os.environ["DATABASE_URL"]}')
    print()

    fetch_results = fetch('fact')

    for row in fetch_results:
        print(f"??? {row['id']}: {row['user_screen_name']}")
        try:
            try:
                api_config = load_yaml(args.api_config)
            except Exception as e:
                print(f"Error loading api config: {e}")
                api_config = {}

            factcheck = FactCheck(
                default_model=args.model, client=args.client, api_config=api_config, prompt=args.prompt, retriever=args.retriever
            )

            content = modal_normalization(args.modal, row['full_text'])
            result = factcheck.check_text(content)

            result['metadata'] = {
                'id': row['id'],
                'created_at': row['created_at'],
                'user_screen_name': row['user_screen_name'],
            }

            # print(json.dumps(result, indent=4))

            update(
                id=row['id'],
                response_fact=json.dumps(result),
                status='post',
            )

        except Exception as e:
            print(f"Error: {e}")
            continue


if __name__ == "__main__":
    main()
