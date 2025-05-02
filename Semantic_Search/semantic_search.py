import httpx
import json
import re

def extract_filters_with_krutrim(query: str):
    prompt = f'''
                Query: {query}
                You are a helpful assistant that extracts product filters from a user query for a fashion e-commerce site.
                Return the following fields in valid JSON:
                - gender: "men" or "women" or null
                - price_min: integer or null
                - price_max: integer or null
                - category: one of "shoes", "shirts", "t-shirts", "jeans", "trousers", or null

                Examples:
                Input: "show me men shoes between 3000 to 4000"
                Output: {{"gender": "men", "category": "shoes", "price_min": 3000, "price_max": 4000}}

                Input: "cheap women jeans"
                Output: {{"gender": "women", "category": "jeans", "price_min": null, "price_max": null}}

                Input: "lightweight running shoes under 1000 rupees"
                Output: {{"gender": null, "category": "shoes", "price_min": null, "price_max": 1000}}
'''

    try:
        response = httpx.post(
            url="https://cloud.olakrutrim.com/v1/chat/completions",
            headers={"Authorization": "Bearer CbrbxuMumUB64GQIDlOugf"},
            json={
                "model": "DeepSeek-R1",
                "messages": [
                    {"role": "system", "content": "You are a product filter extractor for a fashion shopping assistant."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0,
            },
            verify=False,
            timeout=60.0
        )

        if response.status_code != 200:
            print("❌ API failed:", response.status_code, response.text)
            return {"gender": None, "category": None, "price_min": None, "price_max": None}

        output = response.json()["choices"][0]["message"]["content"]

        # Extract only the JSON block
        match = re.search(r"\{[\s\S]*?\}", output)
        if match:
            return json.loads(match.group(0))
        else:
            print("⚠️ No JSON found in output")
            return {"gender": None, "category": None, "price_min": None, "price_max": None}

    except Exception as e:
        print("LLM parsing failed:", e)
        return {"gender": None, "category": None, "price_min": None, "price_max": None}