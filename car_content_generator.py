"""차량 관련 9개 아이템 생성 (Kimi K2 사용) - prompt_generator와 동일 설정 사용"""
import json
import os
import re
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

_USED_FILE = Path.home() / "gallery" / "used_items.json"

_client = OpenAI(
    api_key=os.getenv("MOONSHOT_API_KEY"),
    base_url=os.getenv("MOONSHOT_BASE_URL", "https://api.moonshot.ai/v1"),
)
_MODEL = os.getenv("MOONSHOT_MODEL", "kimi-k2-0711-preview")


def _load_used():
    if _USED_FILE.exists():
        try:
            return json.loads(_USED_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _save_used(items):
    _USED_FILE.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


def reset_used():
    """사용된 아이템 목록 초기화"""
    _save_used([])


def generate_car_items(count: int = 9) -> list:
    """차량 관련 의인화 캐릭터 N개 생성"""
    used = _load_used()
    used_str = ", ".join(used) if used else "(없음)"

    system_prompt = (
        "너는 차량 관련 콘텐츠 크리에이터야. 차량용품, 세차 꿀팁, 운전꿀팁, 주행꿀팁, "
        "연비꿀팁, 차량버튼/조작법, 금지 행동 등에서 의인화 가능한 사물/행동을 추출해.\n\n"
        "규칙:\n"
        "1. 거짓 정보 절대 금지. 실제 자동차 상식만 사용.\n"
        "2. 대사는 10초 안에 읽을 수 있는 짧은 길이.\n"
        "3. 대사 형식: \"나는 '(사물명)'인데! 제발 ~~해줘!\" 같은 짜증/꾸짖는 톤.\n"
        "4. 꿀팁은 \"[사물명] ❌ 잘못된 행동 ➡️ ⭕ 올바른 행동 (이유)\" 형식.\n"
        "5. 이미지 프롬프트는 영어로, Pixar 3D 애니메이션 스타일, 의인화된 캐릭터, "
        "짜증난/화난 표정, 구체적인 포즈(팔로 X자, 팔짱, 손가락질 등), "
        "9:16 세로 구도, 적절한 배경, 자연광, 시네마틱 라이팅 포함해 상세히 작성. "
        "절대 짧게 쓰지 마.\n\n"
        "출력은 오직 유효한 JSON 배열만. 마크다운/설명/주석 금지."
    )

    user_prompt = (
        f"차량 관련 의인화 캐릭터 {count}개를 JSON 배열로 만들어줘.\n"
        f"이미 사용된 캐릭터(중복 금지): {used_str}\n\n"
        "각 항목 형식 예시:\n"
        "{\n"
        '  "character": "주유구손잡이",\n'
        '  "character_en": "fuel pump nozzle handle",\n'
        '  "dialogue": "나는 \'주유구손잡이\'인데! 제발 천천히 당겨줘!",\n'
        '  "tip": "[주유 손잡이] ❌ 최고 속도로 당기기 ➡️ ⭕ 1단으로 천천히 (유증기 증발 최소화)",\n'
        '  "image_prompt": "Pixar 3D animation style, anthropomorphized fuel pump nozzle character with angry face, crossed arms forming an X shape, frustrated expression, standing at a sunny gas station, realistic lighting, cinematic composition, 9:16 vertical aspect ratio, vibrant colors, detailed textures, shallow depth of field"\n'
        "}"
    )

    resp = _client.chat.completions.create(
        model=_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=1,
        max_tokens=16000,
    )

    text = (resp.choices[0].message.content or "").strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    # 응답이 잘린 경우 마지막 완전한 객체까지만 사용
    try:
        items = json.loads(text)
    except json.JSONDecodeError:
        # 마지막 닫힌 } 위치 찾아서 그 뒤 잘라내기
        last_brace = text.rfind("}")
        if last_brace > 0:
            truncated = text[: last_brace + 1]
            # 배열 닫기 추가
            if not truncated.rstrip().endswith("]"):
                truncated = truncated.rstrip().rstrip(",") + "]"
            items = json.loads(truncated)
        else:
            raise


    new_used = used + [it["character"] for it in items]
    _save_used(new_used)

    return items


if __name__ == "__main__":
    items = generate_car_items(9)
    print(json.dumps(items, ensure_ascii=False, indent=2))
