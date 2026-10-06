import os
import requests
from dotenv import load_dotenv

load_dotenv()

print("========================================")
print("     DEVFLOW AI - .ENV VERIFICATION     ")
print("========================================")

# 1. GROQ
print("\n[1] Testing Groq API...")
groq_key = os.getenv("GROQ_API_KEY", "")
groq_model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
if groq_key:
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
            json={
                "model": groq_model,
                "messages": [{"role": "user", "content": "Respond strictly with JSON: {\"status\": \"groq_connected\"}"}],
                "response_format": {"type": "json_object"}
            },
            timeout=15
        )
        if r.status_code == 200:
            print(f" -> GROQ STATUS: SUCCESS (200 OK) [Model: {groq_model}]")
            print(" -> GROQ RESPONSE:", r.json()["choices"][0]["message"]["content"].strip())
        else:
            print(f" -> GROQ STATUS: FAILED ({r.status_code}) -", r.text[:200])
    except Exception as e:
        print(" -> GROQ ERROR:", e)

# 2. GITHUB
print("\n[2] Testing GitHub Access Token...")
gh_token = os.getenv("GITHUB_TOKEN", "")
if gh_token:
    try:
        r = requests.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {gh_token}", "Accept": "application/vnd.github+json"},
            timeout=10
        )
        if r.status_code == 200:
            user_data = r.json()
            print(" -> GITHUB STATUS: SUCCESS (200 OK)")
            print(f" -> Authenticated GitHub Account: @{user_data.get('login')} ({user_data.get('name')})")
        else:
            print(f" -> GITHUB STATUS: FAILED ({r.status_code}) -", r.text[:200])
    except Exception as e:
        print(" -> GITHUB ERROR:", e)

print("\n========================================")
