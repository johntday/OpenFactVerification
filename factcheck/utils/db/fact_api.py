import os
import requests
import json

FACT_API_KEY = os.getenv("FACT_API_KEY")
FACT_API_ENDPOINT = os.getenv("FACT_API_ENDPOINT")

def post_fact(data: dict):
    headers = {'x-api-key': FACT_API_KEY, 'Content-Type': 'application/json'}

    if not data or not data['id'] or not data['content']:
        raise ValueError(f"Required values: id={data['id']}, content={data['content']}")

    try:
        response = requests.post(FACT_API_ENDPOINT, json=data, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        return response
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None


if __name__ == "__main__":
    data = {
        'id': 'test',
        'content': 'hello',
    }
    response = post_fact(data)
    if response:
        print(json.dumps(response.json(), indent=4))

    response = requests.get(
        f'{FACT_API_ENDPOINT}/{data["id"]}',
        headers={'x-api-key': FACT_API_KEY, 'Content-Type': 'application/json'},
    )
    if response:
        print(json.dumps(response.json(), indent=4))
