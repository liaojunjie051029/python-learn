class Tool:
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    def summary(self) -> str:
        return f"{self.name}: {self.description}"


order_tool = Tool(
    name="get_order_status",
    description="查询订单状态"
)

cancel_tool = Tool(
    name="cancel_order",
    description="取消订单"
)

faq_tool = Tool(
    name="search_faq",
    description="查询客服知识库"
)

print("工具名称：", order_tool.name)
print("工具描述：", order_tool.description)
print("工具摘要：", order_tool.summary())

print("工具名称：", cancel_tool.name)
print("工具描述：", cancel_tool.description)
print("工具摘要：", cancel_tool.summary())

print("工具名称：", faq_tool.name)
print("工具描述：", faq_tool.description)
print("工具摘要：", faq_tool.summary())