import json

agent_state = {
    "conversation_id": "1",
     "current_tool":{
         "name":"get_order_status",
         "description":"查询订单状态"
     },
     "retry_count":3,
     "tool_enabled":True,
     "last_message":"你好，我叫小助手，你可以使用我的功能来查询订单状态。",
}

a = "aaaaaaaaaaaaaa"
with open("agent_state_test.json", "w",encoding="utf-8") as f:
    json.dump(a, f, ensure_ascii=False,indent=2)

with open("agent_state_test.json", "r",encoding="utf-8") as f:
    loaded_state = json.load(f)

# print(loaded_state,type(loaded_state["retry_count"]),type(loaded_state["tool_enabled"]))