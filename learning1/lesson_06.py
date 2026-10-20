attempt = 1
max_retry_count = 4
tool_success = False

while attempt <= max_retry_count and not tool_success:
    print("第", attempt, "次调用 get_order_status")

    # 模拟：第二次调用成功
    if attempt == 4:
        tool_success = True
        print("工具调用成功")
    else:
        print("工具调用失败，准备重试")

    attempt += 1

if tool_success:
    print("Agent：已拿到订单状态")
else:
    print("Agent：多次调用失败")