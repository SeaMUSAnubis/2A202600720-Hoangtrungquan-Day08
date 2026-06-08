"""
Task 9 — Retrieval Pipeline Hoàn Chỉnh.

Kết hợp semantic search + lexical search + reranking + PageIndex fallback
thành một pipeline thống nhất.

Logic:
    1. Chạy semantic_search + lexical_search song song
    2. Merge kết quả (RRF hoặc weighted fusion)
    3. Rerank
    4. Nếu top result score < threshold → fallback sang PageIndex
    5. Return top_k results
"""

from .task5_semantic_search import semantic_search
from .task6_lexical_search import lexical_search
from .task7_reranking import rerank, rerank_rrf
from .task8_pageindex_vectorless import pageindex_search


# =============================================================================
# CONFIGURATION
# =============================================================================

SCORE_THRESHOLD = 0.3   # Nếu best score < threshold → fallback PageIndex
DEFAULT_TOP_K = 5
RERANK_METHOD = "cross_encoder"  # "cross_encoder" | "mmr" | "rrf"


def retrieve(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    score_threshold: float = SCORE_THRESHOLD,
    use_reranking: bool = True,
    use_semantic: bool = True,
    use_lexical: bool = True,
) -> list[dict]:
    """
    Retrieval pipeline hoàn chỉnh với fallback logic.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả cuối cùng
        score_threshold: Ngưỡng điểm tối thiểu cho hybrid results
        use_reranking: Có áp dụng reranking hay không
        use_semantic: Bật tắt Semantic Search
        use_lexical: Bật tắt Lexical Search (BM25)

    Returns:
        List of {
            'content': str,
            'score': float,
            'metadata': dict,
            'source': str  # 'hybrid' hoặc 'pageindex'
        }
    """
    # Step 1: Song song chạy semantic + lexical
    dense_results = []
    sparse_results = []
    
    if use_semantic:
        dense_results = semantic_search(query, top_k=top_k * 2)
        
    if use_lexical:
        sparse_results = lexical_search(query, top_k=top_k * 2)
    
    # Step 2: Merge bằng RRF (giả lập nếu chưa implement RRF, hoặc gọi rerank_rrf)
    # Vì task7 chưa có RRF hoàn chỉnh mà chỉ có mock cross_encoder, 
    # ta sẽ ghép 2 list rồi deduplicate để truyền vào rerank.
    seen = set()
    merged = []
    for item in dense_results + sparse_results:
        if item["content"] not in seen:
            item["source"] = "hybrid"
            merged.append(item)
            seen.add(item["content"])
            
    # Step 3: Rerank
    if use_reranking and merged:
        final_results = rerank(query, merged, top_k=top_k, method=RERANK_METHOD)
    else:
        final_results = merged[:top_k]
        
    # Step 4: Check threshold → fallback
    if not final_results or final_results[0]["score"] < score_threshold:
        print(f"  ⚠ Hybrid score ({final_results[0]['score'] if final_results else 0:.3f}) "
              f"< threshold ({score_threshold}). Fallback → PageIndex")
        try:
            fallback = pageindex_search(query, top_k=top_k)
            return fallback
        except Exception:
            pass # Fallback fails if pageindex not installed
            
    return final_results[:top_k]


if __name__ == "__main__":
    test_queries = [
        "Hình phạt cho tội tàng trữ trái phép chất ma tuý",
        "Nghệ sĩ nào bị bắt vì sử dụng ma tuý năm 2024",
        "Luật phòng chống ma tuý 2021 quy định gì về cai nghiện",
    ]

    for q in test_queries:
        print(f"\nQuery: {q}")
        print("-" * 60)
        results = retrieve(q, top_k=3)
        for i, r in enumerate(results, 1):
            print(f"  {i}. [{r['score']:.3f}] [{r['source']}] {r['content'][:80]}...")
