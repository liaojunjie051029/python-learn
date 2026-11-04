from pprint import pprint

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI


@tool
def search_faq(question: str) -> str:
    """查询客服知识库中的常见问题。"""
    return "退款规则：未发货订单可以申请退款。"

@tool
def get_order_status(order_id: str) -> str:
    """查询订单当前状态。"""
    return f"订单 {order_id} 当前状态：已发货。"


model = ChatOpenAI(
    model="gpt-5-nano",
    api_key="sk-demo",
)

model_with_tools = model.bind_tools([search_faq, get_order_status])#这一行做三件事：
# 1. 读取 search_faq 的名称；
# 2. 读取描述和参数 Schema；
# 3. 创建一个绑定了工具配置的新模型对象

print("原模型:", type(model).__name__)
print("绑定后:", type(model_with_tools).__name__)
print("工具对象类型:", type(search_faq).__name__)
print("绑定对象类型:", type(model_with_tools).__name__)
print("原模型和绑定模型是否相同:", model is model_with_tools)

pprint(model_with_tools.kwargs["tools"])