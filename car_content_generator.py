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
        "5. 이미지 프롬프트는 영어로 작성. 반드시 다음 키워드를 모두 포함:\n"
        "   - 'Pixar Cars movie style, glossy 3D animation, polished surfaces'\n"
        "   - 'anthropomorphized character with expressive cartoon face, big round eyes, exaggerated emotions'\n"
        "   - 'highly detailed, ultra-realistic textures, subsurface scattering, ray-traced reflections'\n"
        "   - 'cinematic studio lighting, dramatic rim light, soft shadows, vibrant saturated colors'\n"
        "   - 'shot on Arri Alexa, shallow depth of field, bokeh background, 8K resolution, octane render'\n"
        "   - '9:16 vertical composition, centered character, dynamic pose'\n"
        "   캐릭터의 짜증난/화난/당황한 표정과 구체적인 포즈(팔로 X자, 팔짱, 손가락질, "
        "   이마 짚기 등)를 자세히 묘사.\n"
        "   배경은 반드시 한국 실제 풍경으로 사실적으로 묘사 — 예: Korean street with "
        "   hangul signboards, GS25/CU convenience store, Korean gas station (S-Oil, "
        "   SK Energy, GS Caltex), Seoul apartment complex, Korean underground parking lot, "
        "   Korean countryside road with rice fields, Hyundai/Kia cars in background, "
        "   Korean traffic signs in hangul. 주변 사물(전봇대, 가로수, 도로 표지판, "
        "   행인, 한국 차량 등)도 사실적으로 포함. 절대 짧게 쓰지 마. 최소 60단어 이상.\n\n"

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
        '  "image_prompt": "Pixar Cars movie style, glossy 3D animation, polished metallic surfaces, anthropomorphized fuel pump nozzle character with expressive cartoon face, big round angry eyes, furrowed brows, mouth open shouting, crossed arms forming an X shape, frustrated body language, standing at a realistic Korean GS Caltex gas station with hangul signboards, chrome pumps, Hyundai Sonata and Kia K5 parked nearby, Korean street visible in background with apartment buildings and convenience store, asphalt road with lane markings, telephone poles and traffic signs in hangul, highly detailed ultra-realistic textures, subsurface scattering on plastic parts, ray-traced reflections, cinematic studio lighting with dramatic rim light, soft shadows, vibrant saturated colors, shot on Arri Alexa, shallow depth of field, bokeh background, 8K resolution, octane render, 9:16 vertical composition, centered character, dynamic pose"\n'

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
