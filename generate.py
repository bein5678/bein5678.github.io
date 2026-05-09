"""CLI: python generate.py "한국어 키워드" 로 전체 파이프라인 테스트."""
import sys
from pathlib import Path
from prompt_generator import generate_prompt
from image_generator import generate_image
from site_publisher import publish

def main():
    kw = " ".join(sys.argv[1:]).strip() or "이끼 위에 핀 작은 들꽃, 아침 햇살"
    print(f"[1/3] prompt for: {kw}")
    prompt = generate_prompt(kw)
    print(prompt[:200], "…\n")
    tmp = Path("/tmp/hermes_image.png")
    print("[2/3] generating image…")
    generate_image(prompt, tmp)
    print(f"saved -> {tmp}\n")
    print("[3/3] publishing to site…")
    url = publish(kw, prompt, tmp)
    print(f"DONE -> {url}")

if __name__ == "__main__":
    main()
