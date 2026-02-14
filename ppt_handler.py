"""
PPT 핸들러 모듈 (v3 - 템플릿 디자인 반영)
- PPTX 파일에서 텍스트 추출 (슬라이드/Shape/Run 단위)
- Shape 위치/크기/스타일 정보 추출 (배경색, 채우기색, 테두리)
- 원본 서식을 100% 보존하면서 번역된 텍스트로 교체
- 표(Table) 텍스트 처리 포함
"""

import os
import re
from pptx import Presentation
from pptx.util import Pt, Emu, Inches
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.dml.color import RGBColor


def contains_korean(text: str) -> bool:
    """텍스트에 한글이 포함되어 있는지 확인"""
    if not text:
        return False
    return bool(re.search(r'[가-힣]', text))


def _emu_to_percent(value, total):
    """EMU 단위를 퍼센트로 변환"""
    if total == 0:
        return 0
    return round((value / total) * 100, 2)


def _rgb_to_hex(rgb_color):
    """RGBColor를 hex 문자열로 변환"""
    try:
        if hasattr(rgb_color, 'rgb'):
            rgb = rgb_color.rgb
            return f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}'
        elif isinstance(rgb_color, RGBColor):
            return f'#{rgb_color[0]:02x}{rgb_color[1]:02x}{rgb_color[2]:02x}'
    except:
        pass
    return None


def _get_slide_background(slide):
    """슬라이드 배경색 추출"""
    try:
        # 슬라이드 배경
        bg = slide.background
        fill = bg.fill
        
        if fill.type == 1:  # MSO_FILL_TYPE.SOLID
            if hasattr(fill, 'fore_color'):
                hex_color = _rgb_to_hex(fill.fore_color)
                if hex_color:
                    return hex_color
    except:
        pass
    
    # 기본값: 흰색
    return '#ffffff'


def _get_shape_fill(shape):
    """Shape 채우기색 추출"""
    try:
        if hasattr(shape, 'fill'):
            fill = shape.fill
            if fill.type == 1:  # SOLID
                if hasattr(fill, 'fore_color'):
                    hex_color = _rgb_to_hex(fill.fore_color)
                    if hex_color:
                        return hex_color
    except:
        pass
    return None


def _get_shape_line(shape):
    """Shape 테두리 정보 추출"""
    try:
        if hasattr(shape, 'line'):
            line = shape.line
            if line and hasattr(line, 'color'):
                hex_color = _rgb_to_hex(line.color)
                width_pt = None
                if hasattr(line, 'width') and line.width:
                    width_pt = round(line.width.pt, 1)
                
                if hex_color:
                    return {
                        'color': hex_color,
                        'width': width_pt or 1
                    }
    except:
        pass
    return None


def _get_text_color(shape):
    """텍스트 색상 추출 (첫번째 run 기준)"""
    try:
        if shape.has_text_frame:
            for para in shape.text_frame.paragraphs:
                for run in para.runs:
                    if hasattr(run.font, 'color') and run.font.color:
                        hex_color = _rgb_to_hex(run.font.color)
                        if hex_color:
                            return hex_color
                    break
                break
    except:
        pass
    return '#000000'


def extract_texts(pptx_path: str) -> dict:
    """
    PPTX 파일에서 모든 텍스트를 추출.
    슬라이드 미리보기를 위한 Shape 위치/크기/스타일 정보도 함께 추출.
    """
    prs = Presentation(pptx_path)
    
    # 슬라이드 크기 (EMU 단위)
    slide_width = prs.slide_width or Inches(10)
    slide_height = prs.slide_height or Inches(7.5)
    
    result = {
        "slides": [],
        "total_texts": 0,
        "korean_texts": 0,
        "slide_width": slide_width,
        "slide_height": slide_height,
        "slide_ratio": round(slide_width / slide_height, 3) if slide_height else 1.333
    }
    
    for slide_idx, slide in enumerate(prs.slides):
        slide_data = {
            "slide_number": slide_idx + 1,
            "elements": [],
            "shapes_visual": [],
            "background": _get_slide_background(slide)
        }
        
        for shape_idx, shape in enumerate(slide.shapes):
            # Shape 위치/크기/스타일 (미리보기용)
            shape_visual = {
                "name": shape.name if hasattr(shape, 'name') else f"Shape {shape_idx}",
                "left_pct": _emu_to_percent(shape.left, slide_width) if shape.left is not None else 0,
                "top_pct": _emu_to_percent(shape.top, slide_height) if shape.top is not None else 0,
                "width_pct": _emu_to_percent(shape.width, slide_width) if shape.width is not None else 10,
                "height_pct": _emu_to_percent(shape.height, slide_height) if shape.height is not None else 5,
                "texts": [],
                "type": "text_box",
                "fill_color": _get_shape_fill(shape),
                "line": _get_shape_line(shape),
                "text_color": _get_text_color(shape)
            }
            
            # 텍스트 프레임이 있는 Shape 처리
            if shape.has_text_frame:
                element = _extract_text_frame(
                    shape, slide_idx, shape_idx, "text_box"
                )
                if element["texts"]:
                    slide_data["elements"].append(element)
                    result["total_texts"] += len(element["texts"])
                    result["korean_texts"] += sum(
                        1 for t in element["texts"] if t["has_korean"]
                    )
                    # 미리보기용: 각 텍스트를 shape에 연결
                    for t in element["texts"]:
                        shape_visual["texts"].append({
                            "id": t["id"],
                            "text": t["text"],
                            "has_korean": t["has_korean"],
                            "font_size": _get_font_size(shape, t["paragraph_index"], t["run_index"]),
                            "bold": _get_bold(shape, t["paragraph_index"], t["run_index"])
                        })
            
            # 표(Table) 처리
            if shape.has_table:
                shape_visual["type"] = "table"
                table = shape.table
                shape_visual["rows"] = len(table.rows)
                shape_visual["cols"] = len(table.columns)
                
                for row_idx, row in enumerate(table.rows):
                    for col_idx, cell in enumerate(row.cells):
                        element = _extract_cell_texts(
                            cell, shape, slide_idx, shape_idx,
                            row_idx, col_idx
                        )
                        if element["texts"]:
                            slide_data["elements"].append(element)
                            result["total_texts"] += len(element["texts"])
                            result["korean_texts"] += sum(
                                1 for t in element["texts"] if t["has_korean"]
                            )
                            for t in element["texts"]:
                                shape_visual["texts"].append({
                                    "id": t["id"],
                                    "text": t["text"],
                                    "has_korean": t["has_korean"],
                                    "font_size": 10,
                                    "bold": False,
                                    "cell": f"{row_idx},{col_idx}"
                                })
            
            # 그룹 Shape 처리
            if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
                _extract_group_shapes(
                    shape, slide_idx, shape_idx, slide_data, result
                )
            
            # 텍스트가 있는 shape만 미리보기에 추가
            if shape_visual["texts"]:
                slide_data["shapes_visual"].append(shape_visual)
        
        result["slides"].append(slide_data)
    
    return result


def _get_font_size(shape, para_idx, run_idx):
    """Run의 폰트 크기를 pt 단위로 추출"""
    try:
        para = shape.text_frame.paragraphs[para_idx]
        run = para.runs[run_idx]
        if run.font.size:
            return round(run.font.size.pt)
        return 14
    except Exception:
        return 14


def _get_bold(shape, para_idx, run_idx):
    """Run의 Bold 여부 추출"""
    try:
        para = shape.text_frame.paragraphs[para_idx]
        run = para.runs[run_idx]
        return bool(run.font.bold)
    except Exception:
        return False


def _extract_text_frame(shape, slide_idx, shape_idx, shape_type):
    """텍스트 프레임에서 텍스트 추출"""
    element = {
        "shape_name": shape.name if hasattr(shape, 'name') else f"Shape {shape_idx}",
        "shape_type": shape_type,
        "texts": []
    }
    
    for para_idx, paragraph in enumerate(shape.text_frame.paragraphs):
        for run_idx, run in enumerate(paragraph.runs):
            text = run.text
            if text and text.strip():
                text_id = f"s{slide_idx}_sh{shape_idx}_p{para_idx}_r{run_idx}"
                element["texts"].append({
                    "id": text_id,
                    "text": text,
                    "paragraph_index": para_idx,
                    "run_index": run_idx,
                    "has_korean": contains_korean(text)
                })
    
    return element


def _extract_cell_texts(cell, shape, slide_idx, shape_idx, row_idx, col_idx):
    """표 셀에서 텍스트 추출"""
    element = {
        "shape_name": f"{shape.name} [행{row_idx+1}, 열{col_idx+1}]",
        "shape_type": "table_cell",
        "texts": []
    }
    
    for para_idx, paragraph in enumerate(cell.text_frame.paragraphs):
        for run_idx, run in enumerate(paragraph.runs):
            text = run.text
            if text and text.strip():
                text_id = f"s{slide_idx}_sh{shape_idx}_t{row_idx}_{col_idx}_p{para_idx}_r{run_idx}"
                element["texts"].append({
                    "id": text_id,
                    "text": text,
                    "paragraph_index": para_idx,
                    "run_index": run_idx,
                    "has_korean": contains_korean(text)
                })
    
    return element


def _extract_group_shapes(group_shape, slide_idx, shape_idx, slide_data, result):
    """그룹 Shape 내부의 텍스트 추출 (재귀)"""
    try:
        for sub_idx, sub_shape in enumerate(group_shape.shapes):
            if sub_shape.has_text_frame:
                element = _extract_text_frame(
                    sub_shape, slide_idx, 
                    int(f"{shape_idx}{sub_idx}"),
                    "group_text"
                )
                if element["texts"]:
                    slide_data["elements"].append(element)
                    result["total_texts"] += len(element["texts"])
                    result["korean_texts"] += sum(
                        1 for t in element["texts"] if t["has_korean"]
                    )
    except Exception:
        pass


def create_translated_pptx(
    original_path: str,
    translations: dict,
    output_path: str
) -> str:
    """
    원본 PPTX를 복사하고, 한글 텍스트를 번역된 영어로 교체.
    Run 단위로 교체하므로 폰트, 크기, 색상 등 모든 서식 보존.
    """
    prs = Presentation(original_path)
    
    for slide_idx, slide in enumerate(prs.slides):
        for shape_idx, shape in enumerate(slide.shapes):
            # 텍스트 프레임
            if shape.has_text_frame:
                _replace_text_in_frame(
                    shape.text_frame, slide_idx, shape_idx, translations
                )
            
            # 표(Table)
            if shape.has_table:
                table = shape.table
                for row_idx, row in enumerate(table.rows):
                    for col_idx, cell in enumerate(row.cells):
                        _replace_text_in_cell(
                            cell, slide_idx, shape_idx,
                            row_idx, col_idx, translations
                        )
            
            # 그룹 Shape
            if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
                _replace_text_in_group(
                    shape, slide_idx, shape_idx, translations
                )
    
    # 출력 디렉토리 생성
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    prs.save(output_path)
    return output_path


def _replace_text_in_frame(text_frame, slide_idx, shape_idx, translations):
    """텍스트 프레임 내 Run의 텍스트를 번역으로 교체 + 길이 기반 폰트 조정"""
    # 텍스트 박스 자동 맞춤 설정
    try:
        if hasattr(text_frame, 'word_wrap'):
            text_frame.word_wrap = True
    except:
        pass
    
    for para_idx, paragraph in enumerate(text_frame.paragraphs):
        for run_idx, run in enumerate(paragraph.runs):
            text_id = f"s{slide_idx}_sh{shape_idx}_p{para_idx}_r{run_idx}"
            if text_id in translations:
                translated = translations[text_id]
                if translated and translated != run.text:
                    original_text = run.text
                    original_len = len(original_text)
                    translated_len = len(translated)
                    
                    # 텍스트 교체
                    run.text = translated
                    _adjust_font_for_english(run)
                    
                    # 번역문이 원본보다 30% 이상 길면 폰트 축소
                    if original_len > 0 and translated_len > original_len * 1.3:
                        try:
                            current_size = run.font.size
                            if current_size:
                                # 길이 증가율에 따라 폰트 축소 (최대 20% 축소)
                                ratio = original_len / translated_len
                                new_size = int(current_size * max(ratio, 0.8))
                                run.font.size = new_size
                        except:
                            pass



def _replace_text_in_cell(cell, slide_idx, shape_idx, row_idx, col_idx, translations):
    """표 셀의 텍스트를 번역으로 교체 + 길이 기반 폰트 조정"""
    # 셀 텍스트 박스 자동 줄바꿈 설정
    try:
        if hasattr(cell.text_frame, 'word_wrap'):
            cell.text_frame.word_wrap = True
    except:
        pass
    
    for para_idx, paragraph in enumerate(cell.text_frame.paragraphs):
        for run_idx, run in enumerate(paragraph.runs):
            text_id = f"s{slide_idx}_sh{shape_idx}_t{row_idx}_{col_idx}_p{para_idx}_r{run_idx}"
            if text_id in translations:
                translated = translations[text_id]
                if translated and translated != run.text:
                    original_text = run.text
                    original_len = len(original_text)
                    translated_len = len(translated)
                    
                    # 텍스트 교체
                    run.text = translated
                    _adjust_font_for_english(run)
                    
                    # 표 셀은 공간이 제한적이므로 20% 이상 길면 폰트 축소
                    if original_len > 0 and translated_len > original_len * 1.2:
                        try:
                            current_size = run.font.size
                            if current_size:
                                # 길이 증가율에 따라 폰트 축소 (최대 25% 축소)
                                ratio = original_len / translated_len
                                new_size = int(current_size * max(ratio, 0.75))
                                run.font.size = new_size
                        except:
                            pass



def _replace_text_in_group(group_shape, slide_idx, shape_idx, translations):
    """그룹 Shape 내 텍스트 교체"""
    try:
        for sub_idx, sub_shape in enumerate(group_shape.shapes):
            if sub_shape.has_text_frame:
                _replace_text_in_frame(
                    sub_shape.text_frame, slide_idx,
                    int(f"{shape_idx}{sub_idx}"),
                    translations
                )
    except Exception:
        pass


def _adjust_font_for_english(run):
    """한글 전용 폰트를 영문 호환 폰트로 조정."""
    korean_only_fonts = {
        '맑은 고딕', '굴림', '돋움', '바탕', '궁서',
        '나눔고딕', '나눔바른고딕', '나눔명조', 
        'HY헤드라인M', 'HY울릉도B',
    }
    
    if run.font.name and run.font.name in korean_only_fonts:
        run.font.name = 'Malgun Gothic'
