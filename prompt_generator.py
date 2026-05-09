"""한국어 키워드를 받아 Kimi K2로 영문 이미지 프롬프트를 생성한다."""
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

_client = OpenAI(
    api_key=os.getenv("MOONSHOT_API_KEY"),
    base_url=os.getenv("MOONSHOT_BASE_URL", "https://api.moonshot.ai/v1"),
)
_MODEL = os.getenv("MOONSHOT_MODEL", "kimi-k2-0711-preview")

SYSTEM_PROMPT = (
    "You are an expert prompt engineer for text-to-image models. "
    "Given a short Korean keyword or sentence, produce ONE detailed English prompt "
    "(80-160 words) describing subject, composition, lighting, mood, color palette, "
    "camera/lens, and art style. No markdown, no quotes, plain prose only."
)

def generate_prompt(korean_keyword: str) -> str:
    resp = _client.chat.completions.create(
        model=_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": korean_keyword},
        ],
        temperature=1,
        max_tokens=2000,
    )
    content = resp.choices[0].message.content or ""
    return content.strip()


if __name__ == "__main__":
    import sys
    kw = " ".join(sys.argv[1:]) or "고양이가 우주를 떠다니는 모습"
    print(generate_prompt(kw))

