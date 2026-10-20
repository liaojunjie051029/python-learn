import os

from openai import OpenAI

def main() -> None:
    try:
        api_key = os.environ.get("OPENAI_API_KEY")
        base_url = os.environ.get("LLM_BASE_URL")
        model = os.environ.get("LLM_MODEL")
        # print(f"Using model: {model}")
        # print(f"Using API key: {api_key}")
        # print(f"Using base URL: {base_url}")

        if not api_key:
            raise RuntimeError("OPENAI_API_KEY environment variable is not set")

        if not model:
            raise RuntimeError("OPENAI_MODEL environment variable is not set")

        client_options = {
            "api_key": api_key,
        }

        if base_url:
            client_options["base_url"] = base_url

        client = OpenAI(**client_options)

        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is the meaning of life?"},
        ]

        response = client.chat.completions.create(
            model=model,
            messages=messages,
        )

        answer = response.choices[0].message.content or ""
        print(answer)

    except (Exception,RuntimeError) as e:
        print(f"Error: {e}")
        return


if __name__ == "__main__":
    main()