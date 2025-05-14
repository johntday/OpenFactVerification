import json
import os

from factcheck import FactCheck
from factcheck.utils.db import db
import argparse
from factcheck.utils.llmclient import CLIENTS
from factcheck.utils.multimodal import modal_normalization
from factcheck.utils.utils import load_yaml
from dotenv import load_dotenv

load_dotenv()


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

    for row in db.fetch('fact'):
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

            db.update(
                id=row['id'],
                response_fact=json.dumps(result),
                status='post',
            )

        except Exception as e:
            print(f"Error: {e}")
            continue


if __name__ == "__main__":
    main()
