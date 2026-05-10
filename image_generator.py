"""영문 프롬프트를 받아 OpenAI 이미지 모델로 PNG를 생성·저장한다."""
import os
import base64
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1")
_W = int(os.getenv("IMAGE_WIDTH", "1024"))
_H = int(os.getenv("IMAGE_HEIGHT", "1536"))
_QUALITY = os.getenv("IMAGE_QUALITY", "high")

def generate_image(prompt: str, out_path: Path, max_retries: int = 3) -> Path:
    """이미지 생성 (타임아웃 180초, 실패 시 최대 3회 재시도)"""
    out_path.parent.mkdir(parents=True, exist_ok=True)

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            print(f"  🎨 이미지 생성 시도 {attempt}/{max_retries}...")
            resp = _client.with_options(timeout=180.0).images.generate(
                model=_MODEL,
                prompt=prompt,
                size=f"{_W}x{_H}",
                quality=_QUALITY,
                n=1,
            )
            b64 = resp.data[0].b64_json
            out_path.write_bytes(base64.b64decode(b64))
            print(f"  ✅ 이미지 생성 성공 (시도 {attempt}회)")
            return out_path
        except Exception as e:
            last_error = e
            print(f"  ⚠️ 시도 {attempt} 실패: {type(e).__name__}: {str(e)[:100]}")
            if attempt < max_retries:
                import time
                wait = 5 * attempt  # 5초, 10초, 15초 점진적 대기
                print(f"  ⏳ {wait}초 후 재시도...")
                time.sleep(wait)

    raise RuntimeError(f"이미지 생성 {max_retries}회 모두 실패: {last_error}")


if __name__ == "__main__":
    import sys
    p = sys.argv[1] if len(sys.argv) > 1 else "a serene moss garden, soft morning light"
    out = Path("test_image.png")
    generate_image(p, out)
    print(f"saved -> {out.resolve()}")
