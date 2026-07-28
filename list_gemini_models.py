import os
import json
import requests

# Simple .env loader
def load_dotenv(path='.env'):
    if not os.path.exists(path):
        return
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line=line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k,v=line.split('=',1)
            os.environ.setdefault(k.strip(), v.strip())

load_dotenv()

key = os.environ.get('GEMINI_API_KEY')
if not key:
    print('GEMINI_API_KEY not set in environment or .env')
    raise SystemExit(1)

url = 'https://generativelanguage.googleapis.com/v1/models'
print('Calling', url)
try:
    r = requests.get(url, params={'key': key}, timeout=15)
    print('Status:', r.status_code)
    try:
        print(json.dumps(r.json(), indent=2, ensure_ascii=False))
    except Exception:
        print('Response text:', r.text)
except Exception as e:
    print('Request error:', e)
    raise
