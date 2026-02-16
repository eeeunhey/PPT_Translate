"""Quick test script for the PPT translation API"""
import requests
import json
import os

# Upload and translate the test PPT
with open('e:/ppten/test_sample.pptx', 'rb') as f:
    response = requests.post('http://localhost:5000/upload', files={'file': ('test_sample.pptx', f)})

data = response.json()
print("Success:", data.get('success'))
print("Stats:", json.dumps(data.get('stats', {}), indent=2, ensure_ascii=False))
print()

# Show translation items
if data.get('slides'):
    for slide in data['slides']:
        sn = slide["slide_number"]
        print(f"--- Slide {sn} ---")
        for item in slide['items']:
            orig = item["original"]
            trans = item["translated"]
            ttype = item["translation_type"]
            print(f"  Original: {orig}")
            print(f"  Translated: {trans}")
            print(f"  Type: {ttype}")
            if item.get('word_breakdown'):
                for wb in item['word_breakdown']:
                    ko = wb["korean"]
                    en = wb["english"]
                    role = wb["role"]
                    print(f"    {ko} -> {en} ({role})")
            print()

# Check if translated file exists
if data.get('filename'):
    fname = data["filename"]
    print(f"Output file: {fname}")
    output_path = os.path.join('e:/ppten/outputs', fname)
    print(f"File exists: {os.path.exists(output_path)}")
    if os.path.exists(output_path):
        fsize = os.path.getsize(output_path)
        print(f"File size: {fsize} bytes")
