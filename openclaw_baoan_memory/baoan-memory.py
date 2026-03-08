#!/usr/bin/env python3
"""
BaoAn Memory - BM25-first lifecycle memory for OpenClaw
Fast keyword-based memory with lifecycle controls and Vietnamese retrieval
"""

import sys
import json
import os
import math
import re
import unicodedata
from pathlib import Path

MEMORY_DIR = Path.home() / '.baoan_memory'
MEMORY_FILE = MEMORY_DIR / 'memories.json'
SYNONYM_FILE = MEMORY_DIR / 'synonyms.json'
SLOT_FILE = MEMORY_DIR / 'slots.json'
STATE_FILE = MEMORY_DIR / 'state.json'
DEFAULT_SEARCH_LIMIT = 5
MAX_SEARCH_LIMIT = 5
DEFAULT_CONTEXT_LIMIT = 3
DEFAULT_CONTEXT_TOKENS = 180
DEFAULT_MIN_SCORE = 1.2
FALLBACK_MIN_SCORE = 0.7
MIN_AUTO_LEARN_TOKEN_LEN = 3
SIMILARITY_MERGE_THRESHOLD = 0.85
PHRASE_BOOST = 0.9
CATEGORY_BOOST = 0.45
RECENCY_BOOST_MAX = 0.2
RECENT_QUERY_BOOST = 0.35
MAX_SNIPPET_CHARS = 180
NAMESPACE_BOOST = 0.7
SAME_SESSION_BOOST = 0.25
CROSS_NAMESPACE_PENALTY = 0.35
SUMMARY_MIN_ITEMS = 3
SLOT_DIRECT_BOOST = 1.0
MIN_TOKEN_MATCHES = 1
MMR_LAMBDA = 0.72
TEMPORAL_HALF_LIFE_DAYS = 30
MAX_CONTEXT_CHARS = 420
CONTEXT_MODES = {'balanced', 'facts', 'recent', 'project'}
RECENT_TO_CURATED_THRESHOLD = 0.78
FLUSH_LINE_MAX = 6
ARCHIVE_AFTER_DAYS = 45
PIN_IMPORTANCE_THRESHOLD = 0.92
THRESHOLD_MODES = {
    'strict': 1.5,
    'balanced': 1.2,
    'lenient': 0.7,
}
VI_STOPWORDS = {
    'anh', 'api', 'bai', 'bài', 'ban', 'bạn', 'brave', 'cho', 'co', 'có', 'cua', 'của',
    'da', 'đã', 'de', 'để', 'den', 'đèn', 'dien', 'điện', 'dung', 'dùng', 'ghi', 'giu',
    'giữ', 'giup', 'giúp', 'haravan', 'key', 'kiem', 'kiểm', 'la', 'là', 'lam', 'làm',
    'len', 'lên', 'memory', 'minh', 'mình', 'mot', 'một', 'nay', 'này', 'nguoi', 'người',
    'nhat', 'nhật', 'nho', 'nhớ', 'openclaw', 'search', 'seo', 'tag', 'tags', 'test',
    'them', 'thêm', 'thi', 'thì', 'thoi', 'thôi', 'tra', 'trên', 'tren', 'trong', 'tu',
    'từ', 'user', 'va', 'và', 'van', 'vẫn', 'voi', 'với', 'web'
}
BRAND_ALIASES = {
    'rạng đông': ['rang dong', 'rđ', 'rd', 'sunlike'],
    'kingled': ['kingeco', 'king led', 'kingledvietnam', 'kl'],
    'tiền phong': ['tien phong', 'tp', 'nhựa tiền phong'],
    'panasonic': ['panasoni', 'pana', 'pan', 'halumie'],
    'schneider': ['sch', 'se', 'abb', 'mitsubishi'],
    'bình minh': ['binh minh', 'bm', 'sino', 'wavin'],
    'hoa sen': ['hoasen', 'hs'],
}

SYNONYMS = {}
QUERY_CATEGORY_HINTS = {
    'api': {'api', 'token', 'key', 'access', 'secret', 'oauth', 'credential'},
    'product': {'đèn', 'led', 'ống', 'ppr', 'pvc', 'hdpe', 'aptomat', 'quạt', 'van', 'panel', 'highbay', 'spotlight'},
    'preference': {'thích', 'muốn', 'ưu tiên', 'không', 'ghét', 'warm', 'white', '3000k'},
    'contact': {'số', 'điện', 'thoại', 'phone', 'zalo', 'facebook', 'liên', 'hệ'},
}
RECENCY_HINTS = {'mới', 'moi', 'gần', 'gan', 'vừa', 'vua', 'hôm', 'hom', 'nay', 'recent', 'latest'}
SAVE_POLICIES = {
    'api': {'min_importance': 0.9},
    'product': {'min_importance': 0.7},
    'preference': {'min_importance': 0.6},
    'fact': {'min_importance': 0.5},
    'general': {'min_importance': 0.4},
}
DEFAULT_NAMESPACES = {
    'api': 'rules',
    'product': 'project_context',
    'preference': 'profile',
    'fact': 'working_memory',
    'general': 'working_memory',
    'contact': 'profile',
    'decision': 'decisions',
    'rule': 'rules',
    'lesson': 'lessons',
    'runbook': 'runbooks',
    'project': 'project_context',
    'summary': 'summaries',
}
NAMESPACE_HINTS = {
    'decisions': {'quyết', 'quyet', 'chốt', 'chot', 'thống', 'nhất', 'decision'},
    'lessons': {'bài', 'bai', 'lesson', 'kinh', 'nghiệm', 'rut', 'ra'},
    'rules': {'rule', 'quy', 'định', 'dinh', 'nguyên', 'tắc', 'policy', 'api', 'token', 'key'},
    'runbooks': {'runbook', 'quy', 'trình', 'trinh', 'deploy', 'fix', 'cách', 'buoc', 'bước'},
    'project_context': {'project', 'dự', 'án', 'san', 'pham', 'sản', 'phẩm', 'sku', 'đèn', 'ống'},
    'profile': {'thích', 'muốn', 'profile', 'preference', 'liên', 'hệ', 'số', 'điện', 'thoại'},
    'working_memory': {'đang', 'hiện', 'current', 'tạm', 'task'},
    'summaries': {'tóm', 'tắt', 'summary'},
}
INVALIDATION_MARKERS = ('đổi thành', 'thay vì', 'không còn', 'bây giờ', 'hiện tại', 'update thành')
SLOT_PATTERNS = [
    (re.compile(r'(?i)(?:tôi|user) thích\s+(.+)'), 'preferences', 'preference.like'),
    (re.compile(r'(?i)(?:tôi|user) không thích\s+(.+)'), 'preferences', 'preference.dislike'),
    (re.compile(r'(?i)(?:số điện thoại|phone|zalo)\s*[:\-]?\s*(.+)'), 'profile', 'contact.phone'),
    (re.compile(r'(?i)(?:api key|access token|token)\s*[:\-]?\s*(.+)'), 'environment', 'api.secret'),
    (re.compile(r'(?i)(?:đang làm|current task|đang xử lý)\s+(.+)'), 'project', 'project.current_task'),
    (re.compile(r'(?i)(?:đã chốt|quyết định|thống nhất)\s+(.+)'), 'project', 'project.decision'),
]
FLUSH_HINTS = {
    'decision': {'chốt', 'quyết định', 'thống nhất', 'dùng', 'chọn'},
    'rule': {'api key', 'token', 'quy định', 'bắt buộc', 'phải'},
    'preference': {'thích', 'không thích', 'ưu tiên', 'muốn'},
    'state': {'đang', 'current', 'tiếp theo', 'next', 'task'},
    'learning': {'lưu ý', 'bài học', 'gotcha', 'pattern', 'kinh nghiệm'},
}

def ensure_memory_dir():
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    if not MEMORY_FILE.exists():
        MEMORY_FILE.write_text(json.dumps([], ensure_ascii=False))
    if not SYNONYM_FILE.exists():
        SYNONYM_FILE.write_text(json.dumps({**SYNONYMS, **BRAND_ALIASES}, ensure_ascii=False, indent=2))
    if not SLOT_FILE.exists():
        SLOT_FILE.write_text(json.dumps({}, ensure_ascii=False, indent=2))
    if not STATE_FILE.exists():
        STATE_FILE.write_text(json.dumps({
            'last_flush_at': None,
            'last_promote_at': None,
            'last_archive_at': None,
            'last_precompact_prepare_at': None,
            'counts': {'pinned': 0, 'archived': 0, 'recent': 0, 'curated': 0}
        }, ensure_ascii=False, indent=2))

def load_synonyms():
    ensure_memory_dir()
    try:
        data = json.loads(SYNONYM_FILE.read_text())
        return data
    except:
        return {**SYNONYMS, **BRAND_ALIASES}.copy()

def save_synonyms(synonyms):
    SYNONYM_FILE.write_text(json.dumps(synonyms, ensure_ascii=False, indent=2))

def load_memories():
    ensure_memory_dir()
    try:
        return json.loads(MEMORY_FILE.read_text())
    except:
        return []

def save_memories(memories):
    MEMORY_FILE.write_text(json.dumps(memories, ensure_ascii=False, indent=2))

def load_slots():
    ensure_memory_dir()
    try:
        return json.loads(SLOT_FILE.read_text())
    except:
        return {}

def save_slots(slots):
    SLOT_FILE.write_text(json.dumps(slots, ensure_ascii=False, indent=2))

def load_state():
    ensure_memory_dir()
    try:
        return json.loads(STATE_FILE.read_text())
    except:
        return {
            'last_flush_at': None,
            'last_promote_at': None,
            'last_archive_at': None,
            'last_precompact_prepare_at': None,
            'counts': {'pinned': 0, 'archived': 0, 'recent': 0, 'curated': 0}
        }

def save_state(state):
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2))

def tokenize(text):
    if not text:
        return []
    tokens = re.split(r'[^a-zA-Z0-9À-ỹ]+', text.lower())
    return [t for t in tokens if t]

def normalize_token(token):
    return token.strip().lower()

def strip_accents(text):
    return ''.join(
        char for char in unicodedata.normalize('NFD', text)
        if unicodedata.category(char) != 'Mn'
    ).replace('đ', 'd').replace('Đ', 'D')

def normalize_text(text):
    return ' '.join(tokenize(text))

def normalize_text_ascii(text):
    return strip_accents(normalize_text(text))

def build_query_variants(query):
    normalized = normalize_text(query)
    ascii_query = normalize_text_ascii(query)
    return {
        'original': query,
        'normalized': normalized,
        'ascii': ascii_query,
    }

def is_meaningful_token(token):
    token = normalize_token(token)
    if len(token) < MIN_AUTO_LEARN_TOKEN_LEN:
        return False
    if token.isdigit():
        return False
    if token in VI_STOPWORDS:
        return False
    return True

def contains_phrase(text, phrase):
    normalized_text = f" {normalize_text(text)} "
    normalized_phrase = normalize_text(phrase)
    if not normalized_phrase:
        return False
    if f" {normalized_phrase} " in normalized_text:
        return True

    ascii_text = f" {normalize_text_ascii(text)} "
    ascii_phrase = normalize_text_ascii(phrase)
    return bool(ascii_phrase and f" {ascii_phrase} " in ascii_text)

def estimate_tokens(text):
    return max(1, math.ceil(len(tokenize(text)) * 1.3))

def jaccard_similarity(tokens_a, tokens_b):
    set_a = set(tokens_a)
    set_b = set(tokens_b)
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)

def text_similarity(a, b):
    return jaccard_similarity(tokenize(a), tokenize(b))

def extract_meaningful_phrases(text, min_len=2, max_len=4):
    tokens = tokenize(text)
    phrases = []
    for size in range(min_len, max_len + 1):
        for i in range(len(tokens) - size + 1):
            phrase_tokens = tokens[i:i + size]
            if all(is_meaningful_token(token) for token in phrase_tokens):
                phrases.append(' '.join(phrase_tokens))
    return list(dict.fromkeys(phrases))

def detect_query_categories(query):
    query_tokens = set(tokenize(query))
    categories = set()
    for category, hints in QUERY_CATEGORY_HINTS.items():
        if query_tokens & hints:
            categories.add(category)
    return categories

def detect_query_intents(query):
    intents = set(detect_query_categories(query))
    query_tokens = set(tokenize(query))
    ascii_tokens = set(tokenize(strip_accents(query)))
    if query_tokens & RECENCY_HINTS or ascii_tokens & RECENCY_HINTS:
        intents.add('recent')
    if query_tokens & {'quyết', 'quyet', 'chốt', 'chot', 'thống', 'nhất', 'decision'}:
        intents.add('decision')
    if query_tokens & {'quy', 'định', 'dinh', 'rule', 'policy', 'nguyên', 'tắc'}:
        intents.add('rule')
    if query_tokens & {'đang', 'current', 'task', 'hiện', 'trạng'}:
        intents.add('state')
    return intents

def infer_namespaces(text, category='general'):
    namespaces = []
    mapped = DEFAULT_NAMESPACES.get(normalize_category(category), 'working_memory')
    namespaces.append(mapped)
    tokens = set(tokenize(text))
    for namespace, hints in NAMESPACE_HINTS.items():
        if tokens & hints and namespace not in namespaces:
            namespaces.append(namespace)
    return namespaces or ['working_memory']

def infer_query_namespaces(query, category=None):
    namespaces = infer_namespaces(query, category or 'general')
    query_categories = detect_query_categories(query)
    for qcat in query_categories:
        mapped = DEFAULT_NAMESPACES.get(qcat)
        if mapped and mapped not in namespaces:
            namespaces.append(mapped)
    return namespaces

def classify_query_profile(query, query_intents):
    query_tokens = set(tokenize(query))
    if {'api', 'token', 'key'} & query_tokens or 'rule' in query_intents:
        return 'facts'
    if 'decision' in query_intents:
        return 'facts'
    if 'state' in query_intents or {'đang', 'current', 'task'} & query_tokens:
        return 'project'
    if 'recent' in query_intents:
        return 'recent'
    return 'balanced'

def namespace_gate(mem, query_profile, query_namespaces):
    mem_namespaces = get_memory_namespaces(mem)
    if query_profile == 'facts':
        return bool(set(mem_namespaces) & {'rules', 'decisions', 'profile'})
    if query_profile == 'project':
        return bool(set(mem_namespaces) & {'project_context', 'working_memory', 'summaries'})
    if query_profile == 'recent':
        return True
    return bool(set(mem_namespaces) & set(query_namespaces)) or query_profile == 'balanced'

def map_memory_category(category):
    category = normalize_token(category or 'general')
    if category in {'api', 'credential', 'credentials'}:
        return 'api'
    if category in {'product', 'sku'}:
        return 'product'
    if category in {'preference'}:
        return 'preference'
    if category in {'contact'}:
        return 'contact'
    return 'general'

def category_boost_for_query(query, mem_category):
    query_categories = detect_query_categories(query)
    if not query_categories:
        return 0
    return CATEGORY_BOOST if map_memory_category(mem_category) in query_categories else 0

def phrase_boost_for_query(query, content):
    query_phrases = extract_meaningful_phrases(query)
    matched = [phrase for phrase in query_phrases if contains_phrase(content, phrase)]
    return len(matched) * PHRASE_BOOST, matched

def find_matched_tokens(query_tokens, doc_tokens):
    matched = []
    seen = set()
    normalized_doc_tokens = {normalize_text_ascii(token): token for token in doc_tokens}
    for token in set(query_tokens):
        if token in doc_tokens:
            if token not in seen:
                matched.append(token)
                seen.add(token)
            continue
        normalized = normalize_text_ascii(token)
        if normalized in normalized_doc_tokens:
            resolved = normalized_doc_tokens[normalized]
            if resolved not in seen:
                matched.append(resolved)
                seen.add(resolved)
    return matched

def recency_boost(memories, mem):
    timestamps = [m.get('created_at', 0) for m in memories if m.get('created_at')]
    if not timestamps or not mem.get('created_at'):
        return 0
    oldest = min(timestamps)
    newest = max(timestamps)
    if newest == oldest:
        return RECENCY_BOOST_MAX
    ratio = (mem.get('created_at', oldest) - oldest) / (newest - oldest)
    return round(ratio * RECENCY_BOOST_MAX, 3)

def temporal_decay_multiplier(mem):
    created_at = mem.get('created_at')
    if not created_at:
        return 1.0
    age_days = max(0.0, (current_timestamp() - created_at) / 86400000000)
    decay_lambda = math.log(2) / TEMPORAL_HALF_LIFE_DAYS
    return math.exp(-decay_lambda * age_days)

def recency_intent_boost(query, memories, mem):
    intents = detect_query_intents(query)
    if 'recent' not in intents:
        return 0
    return round(recency_boost(memories, mem) * (RECENT_QUERY_BOOST / max(RECENCY_BOOST_MAX, 0.001)), 3)

def build_snippet(content, query_tokens):
    collapsed = ' '.join(content.split())
    if len(collapsed) <= MAX_SNIPPET_CHARS:
        return collapsed

    lowered = collapsed.lower()
    best_index = -1
    best_token = ''
    for token in query_tokens:
        idx = lowered.find(token.lower())
        if idx != -1 and (best_index == -1 or idx < best_index):
            best_index = idx
            best_token = token

    if best_index == -1:
        head = collapsed[:70].rstrip()
        tail = collapsed[-70:].lstrip()
        return f"{head} ... {tail}"

    start = max(0, best_index - 50)
    end = min(len(collapsed), start + MAX_SNIPPET_CHARS)
    snippet = collapsed[start:end].strip()
    if start > 0:
        snippet = collapsed[:40].rstrip() + ' ... ' + snippet
    if end < len(collapsed):
        snippet = snippet + ' ... ' + collapsed[-40:].lstrip()
    return snippet

def confidence_label(score, threshold_mode, used_fallback):
    min_score = THRESHOLD_MODES.get(threshold_mode, DEFAULT_MIN_SCORE)
    if score >= min_score + 1.5:
        return 'high'
    if score >= min_score or (used_fallback and score >= FALLBACK_MIN_SCORE + 0.7):
        return 'medium'
    return 'low'

def cleanup_memory_fields(mem):
    cleaned = dict(mem)
    cleaned['category'] = normalize_category(cleaned.get('category', 'general'))
    cleaned['memory_kind'] = cleaned.get('memory_kind', 'fact')
    cleaned['namespaces'] = get_memory_namespaces(cleaned)
    cleaned.pop('token_set', None)
    cleaned['tokens'] = tokenize(cleaned.get('content', ''))
    cleaned['brands'] = extract_brands(cleaned.get('content', ''))
    return maybe_pin_memory(cleaned)

def is_noise_memory(mem):
    content = normalize_text(mem.get('content', ''))
    category = normalize_category(mem.get('category', 'general'))
    if category == 'general' and content in {'test memory', 'test memory bug', 'test thêm memory mới'}:
        return True
    if category == 'general' and content == 'ghi chú kiểm tra bộ nhớ bm25':
        return True
    return False

def cleanup_memories():
    memories = load_memories()
    cleaned = []
    removed_ids = []
    for mem in memories:
        normalized = cleanup_memory_fields(mem)
        if is_noise_memory(normalized):
            removed_ids.append(normalized.get('id'))
            continue
        cleaned.append(normalized)
    save_memories(cleaned)
    state = load_state()
    state['counts'] = recompute_state_counts(cleaned)
    save_state(state)
    return {'kept': len(cleaned), 'removed_ids': removed_ids}

def diversify_results(scored, limit):
    if not scored:
        return []
    selected = []
    candidates = scored[:]
    while candidates and len(selected) < limit:
        if not selected:
            selected.append(candidates.pop(0))
            continue
        best_idx = 0
        best_value = None
        for idx, candidate in enumerate(candidates):
            relevance = candidate[0]
            diversity_penalty = max(
                text_similarity(candidate[1].get('content', ''), chosen[1].get('content', ''))
                for chosen in selected
            )
            mmr_score = MMR_LAMBDA * relevance - (1 - MMR_LAMBDA) * diversity_penalty
            if best_value is None or mmr_score > best_value:
                best_value = mmr_score
                best_idx = idx
        selected.append(candidates.pop(best_idx))
    return selected

def normalize_category(category):
    category = normalize_token(category or 'general')
    return category if category in SAVE_POLICIES else 'general'

def ensure_save_policy(category, importance):
    category = normalize_category(category)
    min_importance = SAVE_POLICIES[category]['min_importance']
    return category, max(float(importance), min_importance)

def current_timestamp():
    return int(os.times().elapsed * 1000000)

def update_slots_from_content(content, category='general'):
    slots = load_slots()
    updates = []
    removals = []
    for pattern, slot_category, key in SLOT_PATTERNS:
        match = pattern.search(content)
        if not match:
            continue
        value = match.group(1).strip()
        slots.setdefault(slot_category, {})
        slots[slot_category][key] = {
            'value': value,
            'updated_at': current_timestamp(),
            'source_category': category,
        }
        updates.append({'category': slot_category, 'key': key, 'value': value})

    lowered = content.lower()
    if any(marker in lowered for marker in INVALIDATION_MARKERS):
        if 'không còn' in lowered and 'preference.like' in slots.get('preferences', {}):
            slots['preferences'].pop('preference.like', None)
            removals.append('preferences.preference.like')

    if updates or removals:
        save_slots(slots)
    return {'updates': updates, 'removals': removals}

def search_slots(query):
    slots = load_slots()
    query_tokens = set(tokenize(query))
    results = []
    for slot_category, entries in slots.items():
        for key, item in entries.items():
            haystack = f"{slot_category} {key} {item.get('value', '')}"
            matched_tokens = sorted(query_tokens & set(tokenize(haystack)))
            score = len(matched_tokens)
            if score >= MIN_TOKEN_MATCHES:
                slot_score = score + SLOT_DIRECT_BOOST
                results.append({
                    'slot_category': slot_category,
                    'key': key,
                    'value': item.get('value', ''),
                    'updated_at': item.get('updated_at', 0),
                    'score': round(slot_score, 2),
                    'matched_tokens': matched_tokens,
                })
    results.sort(key=lambda x: (x['score'], x['updated_at']), reverse=True)
    return results

def get_memory_namespaces(mem):
    namespaces = mem.get('namespaces') or []
    if namespaces:
        return namespaces
    return [DEFAULT_NAMESPACES.get(normalize_category(mem.get('category', 'general')), 'working_memory')]

def query_namespace_penalty(query_intents, mem_namespaces):
    if 'decision' in query_intents and 'decisions' not in mem_namespaces:
        return 0.8
    if 'rule' in query_intents and 'rules' not in mem_namespaces:
        return 0.8
    if 'state' in query_intents and 'working_memory' not in mem_namespaces and 'project_context' not in mem_namespaces:
        return 0.4
    return 0

def make_summary(memories, namespace='working_memory'):
    grouped = [m for m in memories if namespace in get_memory_namespaces(m) and m.get('memory_kind') in {'fact', 'recent', 'curated'}]
    grouped = sorted(grouped, key=lambda x: x.get('created_at', 0), reverse=True)[:SUMMARY_MIN_ITEMS]
    if len(grouped) < SUMMARY_MIN_ITEMS:
        return None
    categories = {normalize_category(m.get('category', 'general')) for m in grouped}
    if len(categories) > 1:
        return None
    lines = []
    for mem in reversed(grouped):
        lines.append(mem.get('content', ''))
    content = f"Summary {namespace}: " + ' | '.join(lines)
    return content

def split_flush_lines(content):
    parts = [p.strip(' -\t') for p in re.split(r'[\n\.]+', content) if p.strip()]
    return parts[:FLUSH_LINE_MAX]

def classify_flush_line(line):
    lowered = line.lower()
    for kind, hints in FLUSH_HINTS.items():
        if any(hint in lowered for hint in hints):
            return kind
    return None

def memory_kind_for_line(kind):
    if kind in {'decision', 'rule', 'preference', 'learning'}:
        return 'curated'
    return 'recent'

def category_for_line(kind):
    return {
        'decision': 'fact',
        'rule': 'api',
        'preference': 'preference',
        'state': 'general',
        'learning': 'fact',
    }.get(kind, 'general')

def importance_for_line(kind):
    return {
        'decision': 0.85,
        'rule': 0.95,
        'preference': 0.75,
        'state': 0.7,
        'learning': 0.78,
    }.get(kind, 0.6)

def age_in_days(mem):
    created_at = mem.get('created_at')
    if not created_at:
        return 0
    return max(0.0, (current_timestamp() - created_at) / 86400000000)

def recompute_state_counts(memories=None):
    if memories is None:
        memories = load_memories()
    return {
        'pinned': sum(1 for m in memories if m.get('pinned')),
        'archived': sum(1 for m in memories if m.get('archived')),
        'recent': sum(1 for m in memories if m.get('memory_kind') == 'recent' and not m.get('archived')),
        'curated': sum(1 for m in memories if m.get('memory_kind') == 'curated' and not m.get('archived')),
    }

def maybe_pin_memory(mem):
    if mem.get('importance', 0.0) >= PIN_IMPORTANCE_THRESHOLD or 'rules' in get_memory_namespaces(mem):
        mem['pinned'] = True
    else:
        mem.setdefault('pinned', False)
    mem.setdefault('archived', False)
    return mem

def maybe_create_summary(memories, namespace):
    summary_content = make_summary(memories, namespace)
    if not summary_content:
        return None
    similar, _ = find_similar_memory(memories, summary_content)
    timestamp = current_timestamp()
    if similar:
        similar['content'] = summary_content
        similar['tokens'] = tokenize(summary_content)
        similar['category'] = 'general'
        similar['memory_kind'] = 'summary'
        similar['namespaces'] = ['summaries', namespace]
        similar['created_at'] = max(similar.get('created_at', 0), timestamp)
        return {'status': 'updated', 'id': similar['id']}
    summary = {
        'id': f"sum_{len(memories)}_{timestamp}",
        'content': summary_content,
        'category': 'general',
        'importance': 0.75,
        'tokens': tokenize(summary_content),
        'brands': extract_brands(summary_content),
        'created_at': timestamp,
        'memory_kind': 'summary',
        'namespaces': ['summaries', namespace],
    }
    memories.append(summary)
    return {'status': 'created', 'id': summary['id']}

def find_similar_memory(memories, content):
    candidate_tokens = tokenize(content)
    candidate_ascii = normalize_text_ascii(content)
    best_match = None
    best_score = 0

    for mem in memories:
        existing_tokens = get_doc_tokens(mem)
        score = jaccard_similarity(candidate_tokens, existing_tokens)
        if candidate_ascii and candidate_ascii == normalize_text_ascii(mem.get('content', '')):
            score = 1.0
        if score > best_score:
            best_score = score
            best_match = mem

    if best_score >= SIMILARITY_MERGE_THRESHOLD:
        return best_match, round(best_score, 3)
    return None, round(best_score, 3)

def extract_brands(text):
    """Extract brand names from text"""
    brands = []
    for brand, aliases in BRAND_ALIASES.items():
        if contains_phrase(text, brand):
            brands.append(brand)
        for alias in aliases:
            if contains_phrase(text, alias):
                brands.append(brand)
                break
    return list(set(brands))

def extract_product_type(text):
    """Extract product type keywords"""
    product_types = ['đèn', 'ống', 'ppr', 'pvc', 'hdpe', 'aptomat', 'contactor', 'van', 'dây', 'quạt', 'panel', 'highbay', 'spotlight']
    found = []
    text_lower = text.lower()
    for p in product_types:
        if p in text_lower:
            found.append(p)
    return found

def expand_with_synonyms(tokens):
    expanded = list(tokens)
    synonyms = load_synonyms()
    normalized_keys = {normalize_text_ascii(key): key for key in synonyms}
    normalized_values = {}
    for key, vals in synonyms.items():
        for value in vals:
            normalized_values[normalize_text_ascii(value)] = (key, value)
    for token in tokens:
        token_ascii = normalize_text_ascii(token)
        lookup_key = token if token in synonyms else normalized_keys.get(token_ascii)
        if lookup_key in synonyms:
            for syn in synonyms[lookup_key]:
                if syn not in expanded:
                    expanded.append(syn)
        for key, vals in synonyms.items():
            if token in vals:
                if key not in expanded:
                    expanded.append(key)
                for v in vals:
                    if v not in expanded:
                        expanded.append(v)
        if token_ascii in normalized_values:
            key, matched_value = normalized_values[token_ascii]
            if key not in expanded:
                expanded.append(key)
            if matched_value not in expanded:
                expanded.append(matched_value)
            for value in synonyms.get(key, []):
                if value not in expanded:
                    expanded.append(value)
    return expanded

def should_keep_synonym(base_token, candidate):
    base_token = normalize_token(base_token)
    candidate = normalize_token(candidate)
    if not candidate or candidate == base_token:
        return False
    if not is_meaningful_token(candidate):
        return False
    if base_token in candidate or candidate in base_token:
        return False
    return True

def auto_learn_from_content(content):
    """Automatically learn synonyms from content when adding memory"""
    synonyms = load_synonyms()
    tokens = tokenize(content)
    brands = extract_brands(content)
    product_types = extract_product_type(content)
    
    learned = []
    
    for brand in brands:
        brand_tokens = [t for t in tokens if is_meaningful_token(t)]
        for token in brand_tokens:
            if should_keep_synonym(brand, token):
                if token not in synonyms.get(brand, []):
                    if brand not in synonyms:
                        synonyms[brand] = []
                    synonyms[brand].append(token)
                    learned.append((brand, token))
    
    if product_types:
        for pt in product_types:
            for token in tokens:
                if should_keep_synonym(pt, token):
                    if token not in synonyms.get(pt, []):
                        if pt not in synonyms:
                            synonyms[pt] = []
                        synonyms[pt].append(token)
                        learned.append((pt, token))
    
    if learned:
        save_synonyms(synonyms)
    
    return learned

def auto_learn_from_search(query, results):
    """Learn from search query and results"""
    synonyms = load_synonyms()
    query_tokens = set(tokenize(query))
    
    learned = []
    for result in results:
        result_tokens = set(tokenize(result.get('content', '')))
        
        for q in query_tokens:
            for r in result_tokens:
                if len(q) > 2 and len(r) > 2:
                    if q != r and abs(len(q) - len(r)) <= 3:
                        if q not in synonyms.get(r, []) and r not in synonyms.get(q, []):
                            if q not in synonyms:
                                synonyms[q] = []
                            if r not in synonyms[q]:
                                synonyms[q].append(r)
                                learned.append((q, r))
    
    if learned:
        save_synonyms(synonyms)
    
    return learned

def add_memory(content, category='general', importance=0.5):
    ensure_memory_dir()
    memories = load_memories()
    category, importance = ensure_save_policy(category, importance)
    namespaces = infer_namespaces(content, category)
    slot_changes = update_slots_from_content(content, category)
    similar, similarity_score = find_similar_memory(memories, content)

    if similar:
        similar['content'] = content
        similar['category'] = category
        similar['importance'] = max(similar.get('importance', 0.5), float(importance))
        similar['tokens'] = tokenize(content)
        similar['brands'] = extract_brands(content)
        similar['created_at'] = max(similar.get('created_at', 0), current_timestamp())
        similar['namespaces'] = sorted(set(similar.get('namespaces', []) + namespaces))
        similar['memory_kind'] = similar.get('memory_kind', 'fact')
        maybe_pin_memory(similar)
        save_memories(memories)
        auto_learn_from_content(content)
        summary = None
        for namespace in namespaces:
            summary = maybe_create_summary(memories, namespace) or summary
        save_memories(memories)
        return {
            'status': 'merged',
            'id': similar['id'],
            'similarity': similarity_score,
            'slot_updates': slot_changes,
            'summary': summary,
            'result': f'Merged into existing memory: {content[:50]}...'
        }
    
    memory_id = f"mem_{len(memories)}_{int(os.times().elapsed * 1000000)}"
    tokens = tokenize(content)
    brands = extract_brands(content)
    
    memory = {
        'id': memory_id,
        'content': content,
        'category': category,
        'importance': float(importance),
        'tokens': tokens,
        'brands': brands,
        'created_at': current_timestamp(),
        'memory_kind': 'fact',
        'namespaces': namespaces,
    }
    memory = maybe_pin_memory(memory)
    memories.append(memory)
    summary = None
    for namespace in namespaces:
        summary = maybe_create_summary(memories, namespace) or summary
    save_memories(memories)
    state = load_state()
    state['counts'] = recompute_state_counts(memories)
    save_state(state)
    
    auto_learn_from_content(content)
    
    return {'status': 'success', 'id': memory_id, 'slot_updates': slot_changes, 'summary': summary, 'result': f'Added: {content[:50]}...'}

def flush_before_compaction(content):
    ensure_memory_dir()
    memories = load_memories()
    state = load_state()
    captured = []
    for line in split_flush_lines(content):
        kind = classify_flush_line(line)
        if not kind:
            continue
        category = category_for_line(kind)
        importance = importance_for_line(kind)
        namespaces = infer_namespaces(line, category)
        if kind == 'decision' and 'decisions' not in namespaces:
            namespaces.append('decisions')
        if kind == 'rule' and 'rules' not in namespaces:
            namespaces.append('rules')
        if kind == 'preference' and 'profile' not in namespaces:
            namespaces.append('profile')
        similar, similarity_score = find_similar_memory(memories, line)
        if similar:
            similar['content'] = line
            similar['category'] = category
            similar['importance'] = max(similar.get('importance', 0.5), importance)
            similar['tokens'] = tokenize(line)
            similar['brands'] = extract_brands(line)
            similar['created_at'] = current_timestamp()
            similar['memory_kind'] = memory_kind_for_line(kind)
            similar['namespaces'] = sorted(set(get_memory_namespaces(similar) + namespaces))
            maybe_pin_memory(similar)
            captured.append({'status': 'merged', 'kind': kind, 'id': similar['id'], 'similarity': similarity_score, 'content': line})
        else:
            memory = {
                'id': f"flush_{len(memories)}_{current_timestamp()}",
                'content': line,
                'category': category,
                'importance': importance,
                'tokens': tokenize(line),
                'brands': extract_brands(line),
                'created_at': current_timestamp(),
                'memory_kind': memory_kind_for_line(kind),
                'namespaces': namespaces,
            }
            memory = maybe_pin_memory(memory)
            memories.append(memory)
            captured.append({'status': 'added', 'kind': kind, 'id': memory['id'], 'content': line})
        update_slots_from_content(line, category)
    if captured:
        save_memories(memories)
        state['last_flush_at'] = current_timestamp()
        state['counts'] = recompute_state_counts(memories)
        save_state(state)
    return {'captured': captured, 'count': len(captured)}

def promote_recent_to_curated():
    memories = load_memories()
    state = load_state()
    promoted = []
    for mem in memories:
        if mem.get('memory_kind') != 'recent':
            continue
        importance = mem.get('importance', 0.5)
        namespaces = set(get_memory_namespaces(mem))
        if importance >= RECENT_TO_CURATED_THRESHOLD or namespaces & {'decisions', 'rules', 'profile'}:
            mem['memory_kind'] = 'curated'
            mem['importance'] = max(importance, 0.8)
            maybe_pin_memory(mem)
            promoted.append(mem['id'])
    if promoted:
        save_memories(memories)
        state['last_promote_at'] = current_timestamp()
        state['counts'] = recompute_state_counts(memories)
        save_state(state)
    return {'promoted': promoted, 'count': len(promoted)}

def archive_stale_memories(days=ARCHIVE_AFTER_DAYS):
    memories = load_memories()
    state = load_state()
    archived = []
    for mem in memories:
        if mem.get('pinned'):
            continue
        if mem.get('memory_kind') not in {'fact', 'recent'}:
            continue
        if age_in_days(mem) < days:
            continue
        mem['archived'] = True
        archived.append(mem['id'])
    if archived:
        save_memories(memories)
        state['last_archive_at'] = current_timestamp()
        state['counts'] = recompute_state_counts(memories)
        save_state(state)
    return {'archived': archived, 'count': len(archived), 'days': days}

def prepare_precompact_context(content):
    flush_result = flush_before_compaction(content)
    promote_result = promote_recent_to_curated()
    state = load_state()
    state['last_precompact_prepare_at'] = current_timestamp()
    state['counts'] = recompute_state_counts(load_memories())
    save_state(state)
    return {
        'flush': flush_result,
        'promote': promote_result,
        'context': get_context(6, 140, 'facts')
    }

def get_doc_tokens(doc):
    """Get document tokens, handle both old and new format"""
    if 'tokens' in doc:
        return doc['tokens']
    return []

def score_memory(query, query_tokens, mem, memories, avg_doc_len, n_docs, doc_freq):
    base_score = calculate_bm25_score(query_tokens, mem, avg_doc_len, n_docs, doc_freq)

    brand_boost = 0
    query_brands = extract_brands(query)
    mem_brands = mem.get('brands', [])
    for qb in query_brands:
        if qb in mem_brands:
            brand_boost += 0.5

    importance_boost = mem.get('importance', 0.5) * 0.3
    category_boost = category_boost_for_query(query, mem.get('category', 'general'))
    phrase_score, matched_phrases = phrase_boost_for_query(query, mem.get('content', ''))
    freshness_boost = recency_boost(memories, mem)
    recent_query_boost = recency_intent_boost(query, memories, mem)
    query_intents = detect_query_intents(query)
    query_namespaces = infer_query_namespaces(query, mem.get('category', 'general'))
    mem_namespaces = get_memory_namespaces(mem)
    namespace_boost = NAMESPACE_BOOST if set(query_namespaces) & set(mem_namespaces) else 0
    namespace_penalty = 0 if namespace_boost else CROSS_NAMESPACE_PENALTY
    same_session_boost = SAME_SESSION_BOOST if mem.get('memory_kind') == 'summary' else 0
    intent_penalty = query_namespace_penalty(query_intents, mem_namespaces)
    matched_tokens = find_matched_tokens(query_tokens, get_doc_tokens(mem))
    lexical_gate_penalty = 0.6 if not matched_tokens and not matched_phrases and base_score <= 0 else 0
    temporal_decay = temporal_decay_multiplier(mem)

    total_score = (base_score + brand_boost + importance_boost + category_boost + phrase_score + freshness_boost + recent_query_boost + namespace_boost + same_session_boost - namespace_penalty - intent_penalty - lexical_gate_penalty) * temporal_decay
    details = {
        'bm25': round(base_score, 2),
        'brand_boost': round(brand_boost, 2),
        'importance_boost': round(importance_boost, 2),
        'category_boost': round(category_boost, 2),
        'phrase_boost': round(phrase_score, 2),
        'recency_boost': round(freshness_boost, 2),
        'recent_query_boost': round(recent_query_boost, 2),
        'namespace_boost': round(namespace_boost, 2),
        'same_session_boost': round(same_session_boost, 2),
        'namespace_penalty': round(namespace_penalty, 2),
        'intent_penalty': round(intent_penalty, 2),
        'lexical_gate_penalty': round(lexical_gate_penalty, 2),
        'temporal_decay': round(temporal_decay, 3),
        'matched_tokens': matched_tokens,
        'matched_phrases': matched_phrases,
        'namespaces': mem_namespaces,
    }
    return total_score, details

def search_memory(query, limit=5, category=None, auto_learn=True, threshold_mode='balanced'):
    ensure_memory_dir()
    memories = load_memories()
    
    if not memories:
        return {'results': [], 'total': 0, 'showing': 0}
    
    query_variants = build_query_variants(query)
    query_tokens = tokenize(query)
    query_tokens = expand_with_synonyms(query_tokens)
    query_intents = sorted(detect_query_intents(query))
    query_namespaces = infer_query_namespaces(query, category)
    query_profile = classify_query_profile(query, query_intents)
    
    if not query_tokens:
        return {'results': [], 'total': 0, 'showing': 0}
    
    avg_doc_len = sum(len(get_doc_tokens(m)) for m in memories) / len(memories) if memories else 1
    n_docs = len(memories)
    min_score = THRESHOLD_MODES.get(threshold_mode, DEFAULT_MIN_SCORE)
    
    doc_freq = {}
    for mem in memories:
        doc_tokens = get_doc_tokens(mem)
        for term in doc_tokens:
            doc_freq[term] = doc_freq.get(term, 0) + 1
    
    scored = []
    for mem in memories:
        if category and mem.get('category') != category:
            continue
        if mem.get('archived'):
            continue
        if not namespace_gate(mem, query_profile, query_namespaces):
            continue
        score, details = score_memory(query, query_tokens, mem, memories, avg_doc_len, n_docs, doc_freq)
        if score >= min_score:
            scored.append((score, mem, details))
    
    used_fallback = False
    if not scored:
        used_fallback = True
        for mem in memories:
            if category and mem.get('category') != category:
                continue
            if mem.get('archived'):
                continue
            if not namespace_gate(mem, query_profile, query_namespaces):
                continue

            score, details = score_memory(query, query_tokens, mem, memories, avg_doc_len, n_docs, doc_freq)
            if score >= FALLBACK_MIN_SCORE:
                scored.append((score, mem, details))

    scored.sort(key=lambda x: x[0], reverse=True)
    scored = diversify_results(scored, limit)
    
    results = []
    slot_results = search_slots(query)[:3]
    for score, mem, details in scored[:limit]:
        snippet = build_snippet(mem['content'], details['matched_tokens'] + details['matched_phrases'])
        results.append({
            'id': mem['id'],
            'content': mem['content'],
            'snippet': snippet,
            'category': mem.get('category', 'general'),
            'memory_kind': mem.get('memory_kind', 'fact'),
            'namespaces': mem.get('namespaces', []),
            'pinned': mem.get('pinned', False),
            'importance': mem.get('importance', 0.5),
            'score': round(score, 2),
            'confidence': confidence_label(score, threshold_mode, used_fallback),
            'score_details': details
        })
    
    if auto_learn and results:
        auto_learn_from_search(query, results)
    
    return {
        'results': results,
        'total': len(memories),
        'showing': len(results),
        'limit': limit,
        'query': query_variants,
        'query_intents': query_intents,
        'query_profile': query_profile,
        'query_namespaces': query_namespaces,
        'slots': slot_results,
        'threshold_mode': threshold_mode,
        'min_score': min_score,
        'fallback_used': used_fallback
    }

def calculate_bm25_score(query_tokens, doc, avg_doc_len, n_docs, doc_freq, k1=1.5, b=0.75):
    doc_tokens = get_doc_tokens(doc)
    doc_len = len(doc_tokens)
    
    if not doc_tokens:
        return 0
    
    score = 0
    for term in query_tokens:
        if term in doc_tokens:
            tf = 1
            df = doc_freq.get(term, 1)
            idf = math.log((n_docs - df + 0.5) / (df + 0.5) + 1)
            tf_norm = (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * doc_len / avg_doc_len))
            score += idf * tf_norm
    
    return score

def get_history(limit=10, offset=0):
    memories = load_memories()
    memories = sorted(memories, key=lambda x: x.get('created_at', 0), reverse=True)
    for m in memories:
        m.pop('tokens', None)
        m.pop('brands', None)
    return {
        'results': memories[offset:offset+limit],
        'total': len(memories),
        'showing': len(memories[offset:offset+limit]),
        'offset': offset,
        'limit': limit
    }

def get_context(limit=DEFAULT_CONTEXT_LIMIT, max_tokens=DEFAULT_CONTEXT_TOKENS, mode='balanced'):
    memories = load_memories()
    if mode not in CONTEXT_MODES:
        mode = 'balanced'
    slot_query = {
        'balanced': 'profile preference project decision rule',
        'facts': 'api token key preference decision rule',
        'recent': 'current recent task project',
        'project': 'project current task decision state',
    }[mode]
    slot_items = search_slots(slot_query)[:3]
    memories = sorted(
        memories,
        key=lambda x: (
            x.get('memory_kind') == 'curated',
            mode == 'recent' and x.get('created_at', 0),
            x.get('memory_kind') == 'summary',
            x.get('importance', 0.5),
            x.get('created_at', 0)
        ),
        reverse=True
    )

    def context_gate(mem):
        namespaces = set(get_memory_namespaces(mem))
        kind = mem.get('memory_kind', 'fact')
        if mode == 'facts':
            return bool(namespaces & {'rules', 'decisions', 'profile'}) and kind != 'recent'
        if mode == 'project':
            return bool(namespaces & {'project_context', 'working_memory', 'decisions'})
        if mode == 'recent':
            return kind in {'recent', 'fact', 'summary'}
        return True

    results = []
    used_tokens = 0
    used_chars = 0
    for slot in slot_items:
        slot_text = f"[{slot['slot_category']}/{slot['key']}] {slot['value']}"
        slot_tokens = estimate_tokens(slot_text)
        if used_tokens + slot_tokens > max_tokens or used_chars + len(slot_text) > MAX_CONTEXT_CHARS:
            continue
        results.append({'memory_kind': 'slot', 'content': slot_text, 'score': slot['score']})
        used_tokens += slot_tokens
        used_chars += len(slot_text)
        if len(results) >= limit:
            break
    for mem in memories:
        if len(results) >= limit:
            break
        if not context_gate(mem):
            continue
        if mem.get('archived'):
            continue
        mem_copy = dict(mem)
        mem_copy.pop('tokens', None)
        mem_copy.pop('brands', None)
        mem_tokens = estimate_tokens(mem_copy.get('content', ''))
        if results and (used_tokens + mem_tokens > max_tokens or used_chars + len(mem_copy.get('content', '')) > MAX_CONTEXT_CHARS):
            continue
        results.append(mem_copy)
        used_tokens += mem_tokens
        used_chars += len(mem_copy.get('content', ''))
        if len(results) >= limit:
            break

    return {
        'results': results,
        'total': len(memories),
        'showing': len(results),
        'limit': limit,
        'max_tokens': max_tokens,
        'estimated_tokens': used_tokens,
        'estimated_chars': used_chars,
        'max_chars': MAX_CONTEXT_CHARS,
        'mode': mode
    }

def delete_memory(memory_id):
    memories = load_memories()
    memories = [m for m in memories if m['id'] != memory_id]
    save_memories(memories)
    return {'status': 'success', 'id': memory_id}

def stats():
    memories = load_memories()
    slots = load_slots()
    state = load_state()
    categories = {}
    namespaces = {}
    brands = {}
    total_importance = 0
    for m in memories:
        cat = m.get('category', 'general')
        categories[cat] = categories.get(cat, 0) + 1
        for namespace in m.get('namespaces', []):
            namespaces[namespace] = namespaces.get(namespace, 0) + 1
        for b in m.get('brands', []):
            brands[b] = brands.get(b, 0) + 1
        total_importance += m.get('importance', 0.5)
    
    synonyms = load_synonyms()
    
    return {
        'total': len(memories),
        'categories': categories,
        'namespaces': namespaces,
        'brands': brands,
        'synonyms_count': len(synonyms),
        'slots_count': sum(len(v) for v in slots.values()),
        'avg_importance': round(total_importance / len(memories), 2) if memories else 0,
        'state': state
    }

def list_synonyms():
    synonyms = load_synonyms()
    return {'synonyms': synonyms}

def list_slots():
    return {'slots': load_slots()}

def list_state():
    state = load_state()
    state['counts'] = recompute_state_counts(load_memories())
    save_state(state)
    return {'state': state}

def set_pin(memory_id, pinned=True):
    memories = load_memories()
    updated = False
    for mem in memories:
        if mem.get('id') != memory_id:
            continue
        mem['pinned'] = bool(pinned)
        if pinned:
            mem['archived'] = False
        updated = True
        break
    if updated:
        save_memories(memories)
        state = load_state()
        state['counts'] = recompute_state_counts(memories)
        save_state(state)
    return {'status': 'success' if updated else 'not_found', 'id': memory_id, 'pinned': bool(pinned)}

def unarchive_memory(memory_id):
    memories = load_memories()
    updated = False
    for mem in memories:
        if mem.get('id') != memory_id:
            continue
        mem['archived'] = False
        updated = True
        break
    if updated:
        save_memories(memories)
        state = load_state()
        state['counts'] = recompute_state_counts(memories)
        save_state(state)
    return {'status': 'success' if updated else 'not_found', 'id': memory_id, 'archived': False}

def maintenance_run(archive_days=ARCHIVE_AFTER_DAYS):
    cleanup = cleanup_memories()
    promote = promote_recent_to_curated()
    archive = archive_stale_memories(archive_days)
    memories = load_memories()
    summaries = []
    for namespace in sorted({ns for mem in memories for ns in get_memory_namespaces(mem) if not mem.get('archived')}):
        summary = maybe_create_summary(memories, namespace)
        if summary:
            summaries.append({'namespace': namespace, **summary})
    save_memories(memories)
    state = load_state()
    state['counts'] = recompute_state_counts(memories)
    save_state(state)
    return {
        'cleanup': cleanup,
        'promote': promote,
        'archive': archive,
        'summaries': summaries,
        'state': state,
    }

def main():
    if len(sys.argv) < 2:
        print("Usage: baoan-memory.py <command> [content] [options]")
        print("Commands: add, search, history, context, delete, stats, synonyms, slots, state, cleanup, flush, promote, archive, precompact, pin, unpin, unarchive, maintain")
        print("Options:")
        print("  add: baoan-memory.py add <content> [category] [importance]")
        print("  search: baoan-memory.py search <query> [limit]")
        print("  history: baoan-memory.py history [limit] [offset]")
        print("  context: baoan-memory.py context [limit] [max_tokens] [mode]")
        print("  delete: baoan-memory.py delete <id>")
        print("  stats: baoan-memory.py stats")
        print("  synonyms: baoan-memory.py synonyms")
        print("  slots: baoan-memory.py slots")
        print("  state: baoan-memory.py state")
        print("  cleanup: baoan-memory.py cleanup")
        print("  flush: baoan-memory.py flush <text>")
        print("  promote: baoan-memory.py promote")
        print("  archive: baoan-memory.py archive [days]")
        print("  precompact: baoan-memory.py precompact <text>")
        print("  pin: baoan-memory.py pin <id>")
        print("  unpin: baoan-memory.py unpin <id>")
        print("  unarchive: baoan-memory.py unarchive <id>")
        print("  maintain: baoan-memory.py maintain [archive_days]")
        sys.exit(1)
    
    command = sys.argv[1]
    content = sys.argv[2] if len(sys.argv) > 2 else ""
    
    try:
        if command == "add":
            if not content:
                print(json.dumps({"error": "Content required for add command"}))
                sys.exit(1)
            category = sys.argv[3] if len(sys.argv) > 3 else "general"
            importance = float(sys.argv[4]) if len(sys.argv) > 4 else 0.5
            result = add_memory(content, category, importance)
            print(json.dumps(result, ensure_ascii=False, default=str))
        
        elif command == "search":
            if not content:
                print(json.dumps({"error": "Query required for search command"}))
                sys.exit(1)
            limit = int(sys.argv[3]) if len(sys.argv) > 3 else DEFAULT_SEARCH_LIMIT
            limit = max(1, min(limit, MAX_SEARCH_LIMIT))
            threshold_mode = sys.argv[4] if len(sys.argv) > 4 else 'balanced'
            result = search_memory(content, limit, auto_learn=False, threshold_mode=threshold_mode)
            print(json.dumps(result, ensure_ascii=False, default=str))
        
        elif command == "history":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            offset = int(sys.argv[3]) if len(sys.argv) > 3 else 0
            limit = max(1, min(limit, 50))
            result = get_history(limit, offset)
            print(json.dumps(result, ensure_ascii=False, default=str))
        
        elif command == "context":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_CONTEXT_LIMIT
            max_tokens = int(sys.argv[3]) if len(sys.argv) > 3 else DEFAULT_CONTEXT_TOKENS
            mode = sys.argv[4] if len(sys.argv) > 4 else 'balanced'
            result = get_context(limit, max_tokens, mode)
            print(json.dumps(result, ensure_ascii=False, default=str))
        
        elif command == "delete":
            if not content:
                print(json.dumps({"error": "Memory ID required for delete command"}))
                sys.exit(1)
            result = delete_memory(content)
            print(json.dumps(result, ensure_ascii=False, default=str))
        
        elif command == "stats":
            result = stats()
            print(json.dumps(result, ensure_ascii=False, default=str))
        
        elif command == "synonyms":
            result = list_synonyms()
            print(json.dumps(result, ensure_ascii=False, default=str))

        elif command == "slots":
            result = list_slots()
            print(json.dumps(result, ensure_ascii=False, default=str))

        elif command == "state":
            result = list_state()
            print(json.dumps(result, ensure_ascii=False, default=str))

        elif command == "cleanup":
            result = cleanup_memories()
            print(json.dumps(result, ensure_ascii=False, default=str))

        elif command == "flush":
            if not content:
                print(json.dumps({"error": "Content required for flush command"}))
                sys.exit(1)
            result = flush_before_compaction(content)
            print(json.dumps(result, ensure_ascii=False, default=str))

        elif command == "promote":
            result = promote_recent_to_curated()
            print(json.dumps(result, ensure_ascii=False, default=str))

        elif command == "archive":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else ARCHIVE_AFTER_DAYS
            result = archive_stale_memories(days)
            print(json.dumps(result, ensure_ascii=False, default=str))

        elif command == "precompact":
            if not content:
                print(json.dumps({"error": "Content required for precompact command"}))
                sys.exit(1)
            result = prepare_precompact_context(content)
            print(json.dumps(result, ensure_ascii=False, default=str))

        elif command == "pin":
            if not content:
                print(json.dumps({"error": "Memory ID required for pin command"}))
                sys.exit(1)
            result = set_pin(content, True)
            print(json.dumps(result, ensure_ascii=False, default=str))

        elif command == "unpin":
            if not content:
                print(json.dumps({"error": "Memory ID required for unpin command"}))
                sys.exit(1)
            result = set_pin(content, False)
            print(json.dumps(result, ensure_ascii=False, default=str))

        elif command == "unarchive":
            if not content:
                print(json.dumps({"error": "Memory ID required for unarchive command"}))
                sys.exit(1)
            result = unarchive_memory(content)
            print(json.dumps(result, ensure_ascii=False, default=str))

        elif command == "maintain":
            archive_days = int(sys.argv[2]) if len(sys.argv) > 2 else ARCHIVE_AFTER_DAYS
            result = maintenance_run(archive_days)
            print(json.dumps(result, ensure_ascii=False, default=str))
        
        else:
            print(json.dumps({"error": f"Unknown command: {command}"}))
            sys.exit(1)
    
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
