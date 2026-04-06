import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# First API call with reasoning
# trunk-ignore(bandit/B113)
response = requests.post(
    url="https://openrouter.ai/api/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    },
    data=json.dumps(
        {
            "model": "qwen/qwen3.6-plus:free",
            "messages": [
                {
                    "role": "user",
                    "content": "How many r's are in the word 'strawberry'?",
                }
            ],
            "reasoning": {"enabled": True},
        }
    ),
)

# Extract the assistant message with reasoning_details
response = response.json()
response = response["choices"][0]["message"]
print(response)
