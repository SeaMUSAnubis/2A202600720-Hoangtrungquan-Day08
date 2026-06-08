"""
Task 5 — Semantic Search Module.

Viết module tìm kiếm ngữ nghĩa (dense retrieval) trên vector store.

Yêu cầu:
    - Input: query string + top_k
    - Output: danh sách chunks có score, sorted descending
    - Phải tương thích với embedding model và vector store ở Task 4
"""


def semantic_search(query: str, top_k: int = 10, use_hyde: bool = False) -> list[dict]:
    """
    Tìm kiếm ngữ nghĩa sử dụng vector similarity, có hỗ trợ HyDE (Bonus).

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa
        use_hyde: Sử dụng Hypothetical Document Embeddings để tăng độ chính xác

    Returns:
        List of {
            'content': str,      # Nội dung chunk
            'score': float,      # Cosine similarity score
            'metadata': dict     # source, doc_type, chunk_index
        }
        Sorted by score descending.
    """
    import os
    import chromadb
    from sentence_transformers import SentenceTransformer
    from pathlib import Path
    from dotenv import load_dotenv

    load_dotenv() # Tải các biến môi trường từ .env

    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    VECTOR_STORE = "chromadb"
    COLLECTION_NAME = "drug_law_rag_chunks"
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    CHROMA_DIR = PROJECT_ROOT / "data" / "vectorstore" / "chroma"
    
    search_text = query

    if use_hyde:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            prompt = f"Please write a short, informative paragraph to answer the following question. Make it sound like a factual document:\nQuestion: {query}"
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=150
            )
            hypothetical_doc = response.choices[0].message.content
            print(f"\n[HyDE] Generated Hypothetical Document:\n{hypothetical_doc}\n")
            search_text = hypothetical_doc
        except Exception as e:
            print(f"Lỗi khi chạy HyDE: {e}. Fallback về query gốc.")
            search_text = query

    model = SentenceTransformer(EMBEDDING_MODEL)
    query_embedding = model.encode(search_text, normalize_embeddings=True).tolist()

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_collection(name=COLLECTION_NAME)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )

    out = []
    if not results["ids"] or not results["ids"][0]:
        return out

    documents = results["documents"][0]
    distances = results["distances"][0]
    metadatas = results["metadatas"][0]

    for doc, dist, meta in zip(documents, distances, metadatas):
        score = 1.0 - (dist ** 2) / 2 if dist is not None else 0.0
        out.append({
            "content": doc,
            "score": float(score),
            "metadata": meta
        })

    out.sort(key=lambda x: x["score"], reverse=True)
    return out


if __name__ == "__main__":
    # Test
    results = semantic_search("hình phạt cho tội tàng trữ ma tuý", top_k=5)
    for r in results:
        print(f"[{r['score']:.3f}] {r['content'][:100]}...")
