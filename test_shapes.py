"""shapes_visual 데이터 검증용 테스트 스크립트"""
import requests
import json

r = requests.post(
    "http://localhost:5000/upload",
    files={"file": open("test_sample.pptx", "rb")}
)
d = r.json()

print("Success:", d["success"])
print("Slide ratio:", d.get("slide_ratio"))
print("Stats:", json.dumps(d["stats"], ensure_ascii=False, indent=2))
print()

for sl in d["slides"]:
    sv = sl.get("shapes_visual", [])
    sn = sl["slide_number"]
    items_count = len(sl["items"])
    print(f"=== Slide {sn}: {items_count} items, {len(sv)} shapes ===")
    
    for s in sv:
        name = s.get("name", "?")
        print(f"  Shape '{name}': L={s['left_pct']}% T={s['top_pct']}% W={s['width_pct']}% H={s['height_pct']}% type={s['type']}")
        for t in s.get("texts", []):
            orig = t.get("text", "")[:30]
            trans = t.get("translated", "")[:30]
            fs = t.get("font_size", "?")
            untr = t.get("untranslated", False)
            print(f"    [{fs}pt] '{orig}' -> '{trans}' untranslated={untr}")
    print()

print("Output file:", d.get("filename"))
