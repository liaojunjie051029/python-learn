import asyncio


async def call_tool(tool_name: str, delay: float) -> dict:
    print("开始调用：", tool_name)

    await asyncio.sleep(delay)

    return {
        "success": True,
        "data": {
            "tool": tool_name
        },
        "error": None
    }


async def main() -> None:
    results = await asyncio.gather(
        call_tool("get_order_status", 2),
        call_tool("search_faq", 1),
        call_tool("get_shipping_info", 3)
    )

    for result in results:
        print("工具结果：", result)


asyncio.run(main())