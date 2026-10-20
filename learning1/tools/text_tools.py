def search_faq(question: str) -> dict:
    return {
        "success": True,
        "data": [
         question + "的答案是：这是一个示例答案。"
        ],
        "error": None
    }