import requests
import json
import time
url = 'http://110.40.157.36:8001/api/llm/data_chat1'
# url = 'http://127.0.0.1:8001/api/llm/data_chat1'
data = {
    "question": "画出收盘价趋势图",
    "query_info": {
        "extract_rules": [],
        "search_type": "",
        "search_text": "",
        "page": 1,
        "pagesize": 10000,
        "id": "e222b61c62be4d09908a5bc94aebf22d"
    }
}
t1 = time.time()
res = requests.post(url, json=data)
t2 = time.time()
print(t2 - t1)
print(res, res.text)
print(json.loads(res.text))
