from openai import OpenAI

from config import API_KEY, BASE_URL, CHAT_MODEL


def get_client() -> OpenAI:
    if not API_KEY:
        raise ValueError(
            "未配置 SILICONFLOW_API_KEY。请在项目根目录创建 .env 并填入密钥。"
        )
    return OpenAI(api_key=API_KEY, base_url=BASE_URL)


def chat(messages: list[dict[str, str]]) -> str:
    client = get_client()
    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
        stream=False,
    )
    content = response.choices[0].message.content
    return content or ""
