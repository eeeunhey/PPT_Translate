"""템플릿 스타일 추출 검증용 테스트"""
import requests
import json

r = requests.post(
    "http://localhost:5000/upload",
    files={"file": open("test_sample.pptx", "rb")}
)
d = r.json()

print("Success:", d["success"])
print("=" * 60)

for sl in d["slides"]:
    sn = sl["slide_number"]
    bg = sl.get("background", "?")
    sv = sl.get("shapes_visual", [])
    
    print(f"\n슬라이드 {sn}")
    print(f"  배경색: {bg}")
    print(f"  Shape 수: {len(sv)}")
    
    for s in sv:
        name = s.get("name", "?")
        fill = s.get("fill_color", "없음")
        line = s.get("line", {})
        text_color = s.get("text_color", "?")
        
        print(f"\n  Shape: {name} ({s['type']})")
        print(f"    위치: L={s['left_pct']}% T={s['top_pct']}%")
        print(f"    크기: W={s['width_pct']}% H={s['height_pct']}%")
        print(f"    채우기: {fill}")
        print(f"    텍스트색: {text_color}")
        if line:
            print(f"    테두리: {line.get('width', '?')}pt {line.get('color', '?')}")
        
        # 첫 번째 텍스트만 출력
        texts = s.get("texts", [])
        if texts:
            t = texts[0]
            orig = t.get("text", "")[:30]
            trans = t.get("translated", "")[:30]
            print(f"    텍스트 예시: '{orig}' -> '{trans}'")

print("\n" + "=" * 60)
print("Stats:", json.dumps(d["stats"], ensure_ascii=False, indent=2))
