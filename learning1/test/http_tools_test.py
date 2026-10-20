from urllib.request import urlopen
import json

url = 'http://127.0.0.1:8000/http_data.json'

def fetch_tool_data(url:str) -> dict:
    with urlopen(url,timeout=5) as response:
        status_code = response.status
        body_byte = response.read()
        print(response.headers,status_code)

    body_text = body_byte.decode('utf-8') # 把字节流转换为json字符串
    data = json.loads(body_text)#把 JSON 字符串转换为 Python 字典

    print(type(body_byte))
    print(type(body_text))
    print(type(data))
    return data

result = fetch_tool_data(url)
print(result)