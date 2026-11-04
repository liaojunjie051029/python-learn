from langgraph.store.memory import InMemoryStore

store = InMemoryStore()
user_id = "U1001"
namespace = (user_id, "memories")#namespace 是存储分类，不是具体记忆内容：
memory_id = "preferred_channel"
memory_dict = {
    "preferred_channel": "sms"
}
store.put(namespace, memory_id, memory_dict)

memories = store.search(namespace)

for item in memories:
    print(item.value)