import json
from urllib.request import urlopen


url = "http://127.0.0.1:8000/http_data.json"

with urlopen(url, timeout=5) as response:
    status_code = response.status
    body_bytes = response.read()
    print("响应头：", body_bytes)


body_text = body_bytes.decode("utf-8") # 把字节流转换为字符串
print("响应数据类型：", type(body_text),body_text)
data = json.loads(body_text)#把 JSON 字符串转换为 Python 字典

print("HTTP 状态码：", status_code)
print("响应数据：", type(data), data)
print("消息：", data["data"]["message"])