import asyncio


async def call_order_tool(order_id: str) -> dict:
    print("开始调用订单工具：", order_id)

    # 模拟网络或外部工具等待
    await asyncio.sleep(2)

    return {
        "success": True,
        "data": {
            "order_id": order_id,
            "status": "已发货"
        },
        "error": None
    }


async def main() -> None:
    tool_result = await call_order_tool("UNKNOWN")

    print("工具调用结果：", tool_result)


asyncio.run(main())