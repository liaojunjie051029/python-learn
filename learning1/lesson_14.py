from dataclasses import dataclass


@dataclass
class Tool:
    name: str
    description: str
    enabled: bool = True

    def summary(self) -> str:
        return f"{self.name}: {self.description}"


order_tool = Tool(
    name="get_order_status",
    description="查询订单状态"
)

cancel_tool = Tool(
    name="cancel_order",
    description="取消订单",
    enabled=False
)

faq_tool = Tool(
    name="search_faq",
    description="查询客服知识库"
)

print("订单工具：", order_tool)
print("订单工具摘要：", order_tool.summary())
print("取消工具是否启用：", cancel_tool.enabled)
print("FAQ工具：", faq_tool)
print("FAQ工具摘要：", faq_tool.summary())