import asyncio
import json
from factcheck import FactCheck
from factcheck.utils.db import db
from factcheck.utils.multimodal import modal_normalization

CHECK_INTERVAL = 60 * 5

async def main():
    # while True:
        for row in db.fetch('fact'):
            print(f"??? {row['id']}: {row['user_screen_name']}")
            try:
                # factcheck = FactCheck(
                #     default_model=args.model, client=args.client, api_config=api_config, prompt=args.prompt, retriever=args.retriever
                # )

                # content = modal_normalization(modal="string", input=xxx)
                # res = factcheck.check_text(content)
                # print(json.dumps(res, indent=4))





                factcheck_instance = FactCheck()
                results = factcheck_instance.check_text(
                    raw_text=row['full_text']
                )

                results['metadata'] = {
                    'id': row['id'],
                    'created_at': row['created_at'],
                    'user_screen_name': row['user_screen_name'],
                }

                results_str = json.dumps(results)

                print( results_str )

                db.update(
                    id=row['id'],
                    response_fact=results_str,
                    status='fact:done',
                )

            except Exception as e:
                print(f"Error: {e}")
                continue

        # await asyncio.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())

# 1921687467423404428
# 1921673381511877037