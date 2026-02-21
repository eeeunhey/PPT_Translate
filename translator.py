"""
번역 엔진 모듈 (안정화 버전 v3 - 자동 Fallback)
- 1순위: Google Translate (무료, 품질 좋음)
- 2순위: MyMemory (Google 차단 시 자동 전환)
- 배치 번역 + 재시도 로직 + 미번역 감지
"""

import re
import time
import logging
from deep_translator import GoogleTranslator, MyMemoryTranslator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 번역 엔진 상태
_engine_state = {
    "current": "google",       # 현재 사용 중인 엔진
    "google_failures": 0,      # Google 연속 실패 횟수
    "fallback_threshold": 3,   # 이 횟수 이상 실패하면 MyMemory로 전환
}


def contains_korean(text: str) -> bool:
    """텍스트에 한글이 포함되어 있는지 확인"""
    if not text or not text.strip():
        return False
    return bool(re.search(r'[가-힣]', text))


def split_korean_words(text: str) -> list:
    """한글 텍스트를 공백 기준으로 단어 분리"""
    words = text.strip().split()
    return [w for w in words if w.strip()]



def _create_translator(source='ko', target='en'):
    """현재 엔진에 맞는 번역기 인스턴스 생성"""
    if _engine_state["current"] == "google":
        return GoogleTranslator(source=source, target=target)
    else:
        return MyMemoryTranslator(source=source, target=target)


def _switch_to_fallback():
    """Google → MyMemory로 전환"""
    if _engine_state["current"] == "google":
        _engine_state["current"] = "mymemory"
        logger.warning("⚠️ Google Translate 차단 감지 → MyMemory로 자동 전환합니다.")


def _safe_translate(text: str, max_retries: int = 3) -> str:
    """
    단일 텍스트 번역 (재시도 + 자동 Fallback).
    Google 실패 시 MyMemory로 자동 전환.
    """
    if not text or not text.strip():
        return text
    
    for attempt in range(max_retries):
        try:
            translator = _create_translator()
            result = translator.translate(text)
            if result and result.strip():
                # 성공 시 Google 실패 카운터 리셋
                if _engine_state["current"] == "google":
                    _engine_state["google_failures"] = 0
                return result
        except Exception as e:
            logger.warning(f"번역 재시도 {attempt+1}/{max_retries} [{_engine_state['current']}]: '{text[:30]}...' 에러: {e}")
            
            # Google 실패 카운터 증가
            if _engine_state["current"] == "google":
                _engine_state["google_failures"] += 1
                if _engine_state["google_failures"] >= _engine_state["fallback_threshold"]:
                    _switch_to_fallback()
                    # MyMemory로 바로 재시도
                    try:
                        translator = _create_translator()
                        result = translator.translate(text)
                        if result and result.strip():
                            return result
                    except Exception as e2:
                        logger.warning(f"MyMemory도 실패: {e2}")
            
            wait_time = (attempt + 1) * 1.5
            time.sleep(wait_time)
    
    logger.error(f"번역 최종 실패 [{_engine_state['current']}]: '{text[:50]}'")
    return text  # 원문 반환 (미번역으로 표시됨)


def translate_texts_batch(texts: list, source_lang='auto', target_lang='en', progress_callback=None) -> list:
    """
    여러 텍스트를 효율적으로 번역.
    
    Args:
        texts: [{"id": "s0_sh0_p0_r0", "text": "한글 텍스트"}, ...]
        source_lang: 소스 언어 코드 ('auto'=자동감지, 'ko', 'ja', 'zh-CN', etc.)
        target_lang: 타겟 언어 코드 ('en', 'ja', 'ko', 'zh-CN', 'es', 'fr', etc.)
        progress_callback: fn(current, total, elapsed_sec) - 진행 콜백
    
    Returns:
        [{"id": ..., "original": ..., "translated": ..., "word_breakdown": [...], 
          "translation_type": ..., "untranslated": bool}, ...]
    """
    if not texts:
        return []
    
    start_time = time.time()
    results = []
    
    # 1단계: 한글 포함 텍스트만 필터 (번역 대상)
    korean_items = []
    non_korean_items = []
    
    for item in texts:
        text = item["text"]
        if contains_korean(text):
            korean_items.append(item)
        else:
            non_korean_items.append(item)
    
    # 비한글 텍스트는 바로 결과에 추가
    for item in non_korean_items:
        results.append({
            "id": item["id"],
            "original": item["text"],
            "translated": item["text"],
            "word_breakdown": [],
            "translation_type": "원문 유지 (한글 없음)",
            "untranslated": False
        })
    
    if not korean_items:
        return results
    
    total = len(korean_items)
    
    # 2단계: 배치 번역 (작은 청크 + 재시도)
    sentence_translations = _batch_translate_safe(
        [item["text"] for item in korean_items]
    )
    
    if progress_callback:
        progress_callback(total * 0.5, total, time.time() - start_time)
    
    # 3단계: 단어별 번역도 배치로 처리
    all_unique_words = set()
    word_lists = {}
    
    for item in korean_items:
        words = split_korean_words(item["text"])
        word_lists[item["id"]] = words
        for w in words:
            if contains_korean(w):
                all_unique_words.add(w)
    
    unique_word_list = list(all_unique_words)
    word_translations = {}
    
    if unique_word_list:
        translated_words = _batch_translate_safe(unique_word_list)
        for i, word in enumerate(unique_word_list):
            word_translations[word] = translated_words[i] if i < len(translated_words) else word
    
    if progress_callback:
        progress_callback(total * 0.9, total, time.time() - start_time)
    
    # 4단계: 결과 조합 + 미번역 감지
    untranslated_count = 0
    
    for idx, item in enumerate(korean_items):
        text = item["text"]
        translated = sentence_translations[idx] if idx < len(sentence_translations) else text
        
        if not translated:
            translated = text
        
        # 미번역 감지: 원문과 번역문이 동일하면 미번역
        is_untranslated = (
            translated.strip() == text.strip() or 
            contains_korean(translated)  # 번역 결과에 한글이 남아있으면 미번역
        )
        
        if is_untranslated:
            untranslated_count += 1
        
        # 단어별 분해
        words = word_lists[item["id"]]
        word_breakdown = []
        
        for word in words:
            if contains_korean(word):
                word_en = word_translations.get(word, word)
                word_breakdown.append({
                    "korean": word,
                    "english": word_en,
                    "role": _guess_word_role(word)
                })
            else:
                word_breakdown.append({
                    "korean": word,
                    "english": word,
                    "role": "기호/숫자"
                })
        
        # 직역/의역 판단
        literal_parts = " ".join([wb["english"] for wb in word_breakdown])
        translation_type = _judge_translation_type(literal_parts, translated)
        
        if is_untranslated:
            translation_type = "⚠️ 미번역 (번역 실패)"
        
        results.append({
            "id": item["id"],
            "original": text,
            "translated": translated,
            "word_breakdown": word_breakdown,
            "translation_type": translation_type,
            "untranslated": is_untranslated
        })
    
    if progress_callback:
        progress_callback(total, total, time.time() - start_time)
    
    logger.info(f"번역 완료: {total}개 중 {total - untranslated_count}개 성공, {untranslated_count}개 미번역")
    
    return results


def _batch_translate_safe(texts: list, chunk_size: int = 5) -> list:
    """
    여러 텍스트를 구분자로 묶어 번역. 실패 시 개별 번역으로 폴백.
    
    chunk_size를 5으로 줄여 rate limit 회피.
    """
    all_results = []
    
    for i in range(0, len(texts), chunk_size):
        chunk = texts[i:i + chunk_size]
        
        try:
            # \n 구분자로 합쳐서 한 번에 번역
            combined = "\n".join(chunk)
            translator = _create_translator()
            result = translator.translate(combined)
            
            if result:
                split_results = result.split("\n")
                
                # 원본 개수와 결과 개수 맞추기
                while len(split_results) < len(chunk):
                    split_results.append(chunk[len(split_results)])
                
                all_results.extend(split_results[:len(chunk)])
                logger.info(f"배치 번역 성공: {len(chunk)}개 ({i+1}~{i+len(chunk)})")
            else:
                logger.warning(f"배치 번역 빈 결과 → 개별 번역 폴백")
                all_results.extend(_fallback_individual(chunk))
            
        except Exception as e:
            logger.warning(f"배치 번역 실패 → 개별 번역 폴백: {e}")
            all_results.extend(_fallback_individual(chunk))
        
        # 청크 간 대기 (rate limit 방지)
        if i + chunk_size < len(texts):
            delay = 1.5 if _engine_state["current"] == "google" else 2.0  # rate limit 방지 대기
            time.sleep(delay)
    
    return all_results


def _fallback_individual(texts: list) -> list:
    """배치 실패 시 개별 번역 (재시도 포함)"""
    results = []
    for text in texts:
        translated = _safe_translate(text)
        results.append(translated)
        time.sleep(1.0)  # 개별 번역 간 대기 (rate limit 방지)
    return results


def _guess_word_role(word: str) -> str:
    """한글 단어의 대략적인 품사/역할을 추정"""
    particles = {
        '은': '주제 보조사', '는': '주제 보조사',
        '이': '주격 조사', '가': '주격 조사',
        '을': '목적격 조사', '를': '목적격 조사',
        '에': '부사격 조사', '에서': '부사격 조사',
        '의': '관형격 조사', '와': '접속 조사', '과': '접속 조사',
        '로': '부사격 조사', '으로': '부사격 조사',
        '도': '보조사', '만': '보조사', '까지': '보조사',
        '부터': '보조사', '마다': '보조사',
    }
    
    if word.endswith(('다', '하다', '되다', '이다')):
        return '동사/형용사'
    if word.endswith(('ㄴ', '는', '을', 'ㄹ')):
        return '관형형'
    if word.endswith(('게', '히', '로', '리')):
        return '부사'
    
    for particle, role in particles.items():
        if word.endswith(particle) and len(word) > len(particle):
            return f'명사 + {role}'
    
    if len(word) <= 2:
        return '명사/조사'
    return '명사/구'


def _judge_translation_type(literal: str, actual: str) -> str:
    """직역인지 의역인지 판단"""
    if not literal or not actual:
        return "판단 불가"
    
    literal_words = set(literal.lower().split())
    actual_words = set(actual.lower().split())
    
    if not literal_words:
        return "판단 불가"
    
    overlap = len(literal_words & actual_words)
    ratio = overlap / max(len(literal_words), 1)
    
    if ratio > 0.6:
        return "직역 (Literal)"
    elif ratio > 0.3:
        return "혼합 (Mixed)"
    else:
        return "의역 (Liberal)"
