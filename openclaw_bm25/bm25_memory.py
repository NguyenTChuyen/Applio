#!/usr/bin/env python3
"""
BM25S Memory - Auto-learning Synonyms for Vietnamese Product Search
Fast keyword-based memory with automatic synonym discovery
"""

import sys
import json
import os
import math
import re
import unicodedata
from pathlib import Path

MEMORY_DIR = Path.home() / '.bm25_memory'
MEMORY_FILE = MEMORY_DIR / 'memories.json'
SYNONYM_FILE = MEMORY_DIR / 'synonyms.json'
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

def ensure_memory_dir():
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    if not MEMORY_FILE.exists():
        MEMORY_FILE.write_text(json.dumps([], ensure_ascii=False))
    if not SYNONYM_FILE.exists():
        SYNONYM_FILE.write_text(json.dumps({**SYNONYMS, **BRAND_ALIASES}, ensure_ascii=False, indent=2))

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
    return intents

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
    normalized_doc_tokens = {normalize_text_ascii(token): token for token in doc_tokens}
    for token in set(query_tokens):
        if token in doc_tokens:
            matched.append(token)
            continue
        normalized = normalize_text_ascii(token)
        if normalized in normalized_doc_tokens:
            matched.append(normalized_doc_tokens[normalized])
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
        return collapsed[:MAX_SNIPPET_CHARS].rstrip() + '...'

    start = max(0, best_index - 50)
    end = min(len(collapsed), start + MAX_SNIPPET_CHARS)
    snippet = collapsed[start:end].strip()
    if start > 0:
        snippet = '...' + snippet
    if end < len(collapsed):
        snippet = snippet + '...'
    return snippet

def confidence_label(score, threshold_mode, used_fallback):
    min_score = THRESHOLD_MODES.get(threshold_mode, DEFAULT_MIN_SCORE)
    if score >= min_score + 1.5:
        return 'high'
    if score >= min_score or (used_fallback and score >= FALLBACK_MIN_SCORE + 0.7):
        return 'medium'
    return 'low'

def normalize_category(category):
    category = normalize_token(category or 'general')
    return category if category in SAVE_POLICIES else 'general'

def ensure_save_policy(category, importance):
    category = normalize_category(category)
    min_importance = SAVE_POLICIES[category]['min_importance']
    return category, max(float(importance), min_importance)

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
    similar, similarity_score = find_similar_memory(memories, content)

    if similar:
        similar['content'] = content
        similar['category'] = category
        similar['importance'] = max(similar.get('importance', 0.5), float(importance))
        similar['tokens'] = tokenize(content)
        similar['brands'] = extract_brands(content)
        similar['created_at'] = max(similar.get('created_at', 0), int(os.times().elapsed * 1000000))
        save_memories(memories)
        auto_learn_from_content(content)
        return {
            'status': 'merged',
            'id': similar['id'],
            'similarity': similarity_score,
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
        'created_at': int(os.times().elapsed * 1000000)
    }
    memories.append(memory)
    save_memories(memories)
    
    auto_learn_from_content(content)
    
    return {'status': 'success', 'id': memory_id, 'result': f'Added: {content[:50]}...'}

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

    total_score = base_score + brand_boost + importance_boost + category_boost + phrase_score + freshness_boost + recent_query_boost
    details = {
        'bm25': round(base_score, 2),
        'brand_boost': round(brand_boost, 2),
        'importance_boost': round(importance_boost, 2),
        'category_boost': round(category_boost, 2),
        'phrase_boost': round(phrase_score, 2),
        'recency_boost': round(freshness_boost, 2),
        'recent_query_boost': round(recent_query_boost, 2),
        'matched_tokens': find_matched_tokens(query_tokens, get_doc_tokens(mem)),
        'matched_phrases': matched_phrases,
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
        score, details = score_memory(query, query_tokens, mem, memories, avg_doc_len, n_docs, doc_freq)
        if score >= min_score:
            scored.append((score, mem, details))
    
    used_fallback = False
    if not scored:
        used_fallback = True
        for mem in memories:
            if category and mem.get('category') != category:
                continue

            score, details = score_memory(query, query_tokens, mem, memories, avg_doc_len, n_docs, doc_freq)
            if score >= FALLBACK_MIN_SCORE:
                scored.append((score, mem, details))

    scored.sort(key=lambda x: x[0], reverse=True)
    
    results = []
    for score, mem, details in scored[:limit]:
        snippet = build_snippet(mem['content'], details['matched_tokens'] + details['matched_phrases'])
        results.append({
            'id': mem['id'],
            'content': mem['content'],
            'snippet': snippet,
            'category': mem.get('category', 'general'),
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

def get_context(limit=DEFAULT_CONTEXT_LIMIT, max_tokens=DEFAULT_CONTEXT_TOKENS):
    memories = load_memories()
    memories = sorted(
        memories,
        key=lambda x: (x.get('importance', 0.5), x.get('created_at', 0)),
        reverse=True
    )

    results = []
    used_tokens = 0
    for mem in memories:
        mem_copy = dict(mem)
        mem_copy.pop('tokens', None)
        mem_copy.pop('brands', None)
        mem_tokens = estimate_tokens(mem_copy.get('content', ''))
        if results and used_tokens + mem_tokens > max_tokens:
            continue
        results.append(mem_copy)
        used_tokens += mem_tokens
        if len(results) >= limit:
            break

    return {
        'results': results,
        'total': len(memories),
        'showing': len(results),
        'limit': limit,
        'max_tokens': max_tokens,
        'estimated_tokens': used_tokens
    }

def delete_memory(memory_id):
    memories = load_memories()
    memories = [m for m in memories if m['id'] != memory_id]
    save_memories(memories)
    return {'status': 'success', 'id': memory_id}

def stats():
    memories = load_memories()
    categories = {}
    brands = {}
    total_importance = 0
    for m in memories:
        cat = m.get('category', 'general')
        categories[cat] = categories.get(cat, 0) + 1
        for b in m.get('brands', []):
            brands[b] = brands.get(b, 0) + 1
        total_importance += m.get('importance', 0.5)
    
    synonyms = load_synonyms()
    
    return {
        'total': len(memories),
        'categories': categories,
        'brands': brands,
        'synonyms_count': len(synonyms),
        'avg_importance': round(total_importance / len(memories), 2) if memories else 0
    }

def list_synonyms():
    synonyms = load_synonyms()
    return {'synonyms': synonyms}

def main():
    if len(sys.argv) < 2:
        print("Usage: bm25_memory.py <command> [content] [options]")
        print("Commands: add, search, history, context, delete, stats, synonyms")
        print("Options:")
        print("  add: bm25_memory.py add <content> [category] [importance]")
        print("  search: bm25_memory.py search <query> [limit]")
        print("  history: bm25_memory.py history [limit] [offset]")
        print("  context: bm25_memory.py context [limit]")
        print("  delete: bm25_memory.py delete <id>")
        print("  stats: bm25_memory.py stats")
        print("  synonyms: bm25_memory.py synonyms")
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
            result = get_context(limit, max_tokens)
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
