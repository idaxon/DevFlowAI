import os
import requests
from dotenv import load_dotenv

load_dotenv()

groq_key = os.getenv("GROQ_API_KEY", "")
for m in ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"]:
    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
        json={
            "model": m,
            "messages": [{"role": "user", "content": "Respond strictly with JSON: {\"status\": \"ok\", \"model\": \"" + m + "\"}"}],
            "response_format": {"type": "json_object"}
        },
        timeout=10
    )
    print(f"Model [{m}] -> HTTP {r.status_code}")
    if r.status_code == 200:
        print("Response:", r.json()["choices"][0]["message"]["content"])
