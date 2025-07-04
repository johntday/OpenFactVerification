import json
import os
import psycopg2
import requests
from openai import OpenAI
import pytz
from factcheck import FactCheck
import argparse

from factcheck.utils.data_class import FactCheckOutput
from factcheck.utils.llmclient import CLIENTS
from factcheck.utils.multimodal import modal_normalization
from factcheck.utils.utils import load_yaml
import json
from datetime import datetime
from dotenv import load_dotenv
import redis

load_dotenv()
NTFY_TOKEN = os.getenv('NTFY_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')
REDIS_URL = os.getenv("REDIS_URL")
if not DATABASE_URL or not REDIS_URL or not NTFY_TOKEN:
    print("Config value error. Check '.env' file")
    exit(1)
SYSTEM_PROMPT = """
You will receive a statement and a list of claims. Those claims will already have references and source quotes. Your task is to
evaluate all of this together and provide a comprehensive conclusion. You will provide a score from 0 - 100 how truthfull you
think this statement is and a description of why you think so.
"""


r = redis.from_url(REDIS_URL)


def post_fact(data: dict) -> None:
    if not data or not data['id'] or not data['content']:
        raise ValueError(f"Required values: id={data['id']}, content={data['content']}")

    try:
        r.set(data['id'], data['content'])
        return None
    except Exception as e:
        print(f"ERROR posting to redis: {e}")
        return None

def format_unix_timestamp(unix_timestamp) -> str:
    return datetime.utcfromtimestamp(unix_timestamp).strftime('%Y-%m-%d %H:%M')

def format_tweet(row):
    return {
        'id': row[0],
        'user_screen_name': row[1],
        'full_text': row[2],
        'created_at': row[3],
    }

def get_cst_timestamp() -> str:
    timezone = pytz.timezone('America/Chicago')
    current_time = datetime.now(timezone)
    formatted_timestamp = current_time.strftime("%Y-%m-%d %H:%M:%S %Z%z")
    return formatted_timestamp

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
        return results

def update(id: str, response_fact: str, status: str, tweet: str) -> None:
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        cur.execute(
            """UPDATE twitter_tweets
            SET response_fact = %s,
            status = %s,
            tweet = %s
            where id = %s"""
            , (
                response_fact,
                status,
                tweet,
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


def tweet_summary(result,
                  model="gpt-4.1-mini",
                  temperature=0.2
                  ) -> str | None:
    SYSTEM_PROMPT = ("You will receive a statement and a list of claims. Those claims will already have references, source quotes, "
                     "and a factuality score. Your task is to evaluate all of this together and provide an engaging brief summary of about 70 words or "
                     "less.")

    def valid_claims() -> list:
        claims = []
        for claim in result["claim_detail"]:
            if not claim["checkworthy"]:
                continue
            new_claim = {
                'claim_id': claim["id"],
                'claim_text': claim["claim"],
                'claim_factuality_score': claim["factuality"],
                'claim_evidences': [x for x in claim["evidences"] if x['relationship'] in ['REFUTES', 'SUPPORTS']],
            }
            claims.append(new_claim)

        return claims

    user_content = {
        'statement': result["raw_text"],
        'factuality_score': result["summary"]["factuality"],
        'claims': valid_claims(),
    }

    if not user_content['claims']:
        return 'No check-worthy claims were found'

    messages = [
        {'role': 'system', 'content': SYSTEM_PROMPT},
        {'role': 'user', 'content': json.dumps(user_content)},
    ]
    client = OpenAI()
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
    )
    return response.choices[0].message.content


def ntfy():
    requests.post(f"https://ntfy.sh/{NTFY_TOKEN}",
                  data="my_fact_verification.py",
                  headers={
                      "Title": "ERROR",
                      "Priority": "urgent",
                      "Tags": "skull"
                  })


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

    print("START")

    fetch_results = fetch('fact')

    for row in fetch_results:
        print(f"[{get_cst_timestamp()}]  {row['id']}  {row['user_screen_name']}")
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

            summary = tweet_summary(result=result)

            result['metadata'] = {
                'id': row['id'],
                'created_at': row['created_at'],
                'user_screen_name': row['user_screen_name'],
                'tweet': summary,
            }

            result_str = json.dumps(result)

            update(
                id=row['id'],
                response_fact=result_str,
                status='post',
                tweet=summary,
            )

            post_fact({
                'id': row['id'],
                'content': result_str,
            })

        except Exception as e:
            print(f"Error: {e}")
            ntfy()
            continue


if __name__ == "__main__":
    main()
