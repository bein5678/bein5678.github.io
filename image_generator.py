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

def generate_image(prompt: str, out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    resp = _client.images.generate(
        model=_MODEL,
        prompt=prompt,
        size=f"{_W}x{_H}",
        quality=_QUALITY,
        n=1,
    )
    b64 = resp.data[0].b64_json
    out_path.write_bytes(base64.b64decode(b64))
    return out_path

if __name__ == "__main__":
    import sys
    p = sys.argv[1] if len(sys.argv) > 1 else "a serene moss garden, soft morning light"
    out = Path("test_image.png")
    generate_image(p, out)
    print(f"saved -> {out.resolve()}")
