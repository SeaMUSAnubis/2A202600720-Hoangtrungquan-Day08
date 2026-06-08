"""
Task 4 — Chunking & Indexing vào Vector Store.

Mục tiêu:
    1. Đọc toàn bộ markdown files từ data/standardized/
    2. Chunk tài liệu thành các đoạn nhỏ có overlap
    3. Embed từng chunk bằng model sentence-transformers
    4. Lưu chunks vào ChromaDB local để dùng cho semantic search ở Task 5
    5. Lưu thêm data/chunks/chunks.json để dùng cho BM25 ở Task 6

Cài đặt:
    pip install langchain-text-splitters sentence-transformers chromadb pyyaml

Gợi ý chạy:
    python src/task4_chunking_indexing.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # yaml chỉ dùng để đọc metadata markdown, thiếu vẫn chạy được
    yaml = None


# =============================================================================
# PATH CONFIGURATION
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STANDARDIZED_DIR = PROJECT_ROOT / "data" / "standardized"
CHUNKS_DIR = PROJECT_ROOT / "data" / "chunks"
CHUNKS_PATH = CHUNKS_DIR / "chunks.json"
CHROMA_DIR = PROJECT_ROOT / "data" / "vectorstore" / "chroma"


# =============================================================================
# CONFIGURATION — Giải thích lựa chọn
# =============================================================================

# Chọn RecursiveCharacterTextSplitter vì dữ liệu gồm cả văn bản pháp luật và bài báo.
# Cách tách này an toàn, giữ đoạn văn gần nhau, không phụ thuộc tài liệu có heading chuẩn hay không.
CHUNK_SIZE = 800

# Overlap 150 giúp giữ ngữ cảnh giữa 2 chunk liền kề.
# Ví dụ: điều luật thường có câu mở đầu ở chunk trước và nội dung xử phạt ở chunk sau.
CHUNK_OVERLAP = 150
CHUNKING_METHOD = "recursive"

# BAAI/bge-m3 là model multilingual, phù hợp tiếng Việt hơn các model tiếng Anh nhẹ.
# Dimension của bge-m3 là 1024.
# Đã đổi sang model nhỏ (90MB) thay vì BAAI/bge-m3 (2.2GB) cho máy yếu
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

# Dùng ChromaDB vì chạy local đơn giản, không cần Docker/server như Weaviate.
# Sau này Task 5 có thể load lại collection này để semantic_search.
VECTOR_STORE = "chromadb"
COLLECTION_NAME = "drug_law_rag_chunks"


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _normalize_text(text: str) -> str:
    """Làm sạch text nhẹ để chunking ổn định hơn."""
    text = text.replace("\ufeff", "")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def _extract_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """
    Đọc YAML frontmatter nếu markdown có dạng:
    ---
    title: ...
    year: ...
    ---
    content...
    """
    if not content.startswith("---"):
        return {}, content

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content

    raw_meta = parts[1].strip()
    body = parts[2].strip()

    if yaml is None:
        return {}, body

    try:
        metadata = yaml.safe_load(raw_meta) or {}
        if not isinstance(metadata, dict):
            metadata = {}
        return metadata, body
    except Exception:
        return {}, body


def _infer_doc_type(md_file: Path) -> str:
    """Suy luận loại tài liệu từ đường dẫn."""
    path_text = str(md_file).lower()
    if "legal" in path_text:
        return "legal"
    if "news" in path_text:
        return "news"
    return "unknown"


def _safe_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    """
    ChromaDB chỉ nhận metadata dạng str/int/float/bool/None.
    Convert list/dict thành JSON string để tránh lỗi insert.
    """
    safe: dict[str, Any] = {}
    for key, value in metadata.items():
        if value is None or isinstance(value, (str, int, float, bool)):
            safe[key] = value
        else:
            safe[key] = json.dumps(value, ensure_ascii=False)
    return safe


# =============================================================================
# IMPLEMENTATION
# =============================================================================

def load_documents() -> list[dict]:
    """
    Đọc toàn bộ markdown files từ data/standardized/.

    Returns:
        List gồm các item dạng:
        {
            "content": str,
            "metadata": {
                "source_file": str,
                "source_path": str,
                "doc_type": "legal" | "news" | "unknown",
                "title": str,
                ...
            }
        }
    """
    if not STANDARDIZED_DIR.exists():
        raise FileNotFoundError(
            f"Không tìm thấy thư mục {STANDARDIZED_DIR}. "
            "Hãy chạy Task 3 để tạo data/standardized/ trước."
        )

    documents: list[dict] = []
    md_files = sorted(STANDARDIZED_DIR.rglob("*.md"))

    for md_file in md_files:
        raw_content = md_file.read_text(encoding="utf-8", errors="ignore")
        frontmatter, body = _extract_frontmatter(raw_content)
        body = _normalize_text(body)

        if not body:
            print(f"⚠ Bỏ qua file rỗng: {md_file}")
            continue

        relative_path = md_file.relative_to(PROJECT_ROOT).as_posix()
        doc_type = frontmatter.get("doc_type") or frontmatter.get("type") or _infer_doc_type(md_file)
        title = frontmatter.get("title") or md_file.stem.replace("-", " ").replace("_", " ")

        metadata = {
            **frontmatter,
            "source_file": md_file.name,
            "source_path": relative_path,
            "doc_type": doc_type,
            "title": title,
        }

        documents.append({
            "content": body,
            "metadata": _safe_metadata(metadata),
        })

    if not documents:
        raise ValueError(
            f"Không tìm thấy file .md hợp lệ trong {STANDARDIZED_DIR}. "
            "Hãy kiểm tra output của Task 3."
        )

    return documents


def chunk_documents(documents: list[dict]) -> list[dict]:
    """
    Chunk documents theo RecursiveCharacterTextSplitter.

    Returns:
        List gồm các item dạng:
        {
            "id": str,
            "content": str,
            "metadata": dict
        }
    """
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n## ", "\n### ", "\n\n", "\n", ". ", "; ", ", ", " ", ""],
    )

    chunks: list[dict] = []

    for doc_index, doc in enumerate(documents):
        text = doc["content"]
        metadata = doc["metadata"]
        splits = splitter.split_text(text)

        source_stem = Path(str(metadata.get("source_file", f"doc_{doc_index}"))).stem

        for chunk_index, chunk_text in enumerate(splits):
            chunk_text = _normalize_text(chunk_text)
            if not chunk_text:
                continue

            chunk_id = f"{source_stem}_{chunk_index:04d}"
            chunk_metadata = {
                **metadata,
                "chunk_id": chunk_id,
                "chunk_index": chunk_index,
                "chunk_size": len(chunk_text),
                "chunking_method": CHUNKING_METHOD,
                "embedding_model": EMBEDDING_MODEL,
            }

            chunks.append({
                "id": chunk_id,
                "content": chunk_text,
                "metadata": _safe_metadata(chunk_metadata),
            })

    if not chunks:
        raise ValueError("Không tạo được chunk nào. Hãy kiểm tra nội dung markdown.")

    # Prevent pytest (which tests with docs[:1]) from overwriting the full chunks.json
    if len(documents) > 1:
        CHUNKS_DIR.mkdir(parents=True, exist_ok=True)
        CHUNKS_PATH.write_text(
            json.dumps(chunks, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"OK Saved chunks to {CHUNKS_PATH}")

    return chunks


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """
    Embed toàn bộ chunks bằng SentenceTransformer.

    Returns:
        Mỗi chunk dict được thêm key 'embedding': list[float]
    """
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(EMBEDDING_MODEL)
    texts = [chunk["content"] for chunk in chunks]

    embeddings = model.encode(
        texts,
        batch_size=16,
        show_progress_bar=True,
        normalize_embeddings=True,
    )

    for chunk, embedding in zip(chunks, embeddings):
        emb_list = embedding.tolist()

        # Check nhẹ để phát hiện chọn sai EMBEDDING_DIM.
        if len(emb_list) != EMBEDDING_DIM:
            print(
                f"⚠ Warning: embedding dim thực tế = {len(emb_list)}, "
                f"khác EMBEDDING_DIM = {EMBEDDING_DIM}."
            )

        chunk["embedding"] = emb_list

    return chunks


def index_to_vectorstore(chunks: list[dict]) -> None:
    """
    Lưu chunks vào ChromaDB local.

    Collection lưu:
        - ids: chunk_id
        - documents: nội dung chunk
        - metadatas: metadata của chunk
        - embeddings: vector đã encode
    """
    if VECTOR_STORE != "chromadb":
        raise ValueError(
            f"File này đang implement ChromaDB. VECTOR_STORE hiện tại = {VECTOR_STORE}. "
            "Hãy đặt VECTOR_STORE = 'chromadb' hoặc tự bổ sung backend khác."
        )

    import chromadb

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    # Xóa collection cũ để tránh duplicate khi chạy lại pipeline.
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={
            "description": "RAG chunks for Vietnamese drug law/news documents",
            "embedding_model": EMBEDDING_MODEL,
            "chunk_size": CHUNK_SIZE,
            "chunk_overlap": CHUNK_OVERLAP,
        },
    )

    ids = [chunk["id"] for chunk in chunks]
    documents = [chunk["content"] for chunk in chunks]
    metadatas = [_safe_metadata(chunk["metadata"]) for chunk in chunks]
    embeddings = [chunk["embedding"] for chunk in chunks]

    # ChromaDB có giới hạn batch tùy version, nên insert theo batch nhỏ.
    batch_size = 128
    for start in range(0, len(chunks), batch_size):
        end = start + batch_size
        collection.add(
            ids=ids[start:end],
            documents=documents[start:end],
            metadatas=metadatas[start:end],
            embeddings=embeddings[start:end],
        )

    print(f"OK ChromaDB path: {CHROMA_DIR}")
    print(f"OK Collection: {COLLECTION_NAME}")
    print(f"OK Indexed chunks: {collection.count()}")


def run_pipeline() -> None:
    """Chạy toàn bộ pipeline: load → chunk → embed → index."""
    print("=" * 60)
    print("Task 4: Chunking & Indexing")
    print(f"  Standardized dir: {STANDARDIZED_DIR}")
    print(f"  Chunking: {CHUNKING_METHOD} (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    print(f"  Embedding: {EMBEDDING_MODEL} (dim={EMBEDDING_DIM})")
    print(f"  Vector Store: {VECTOR_STORE}")
    print("=" * 60)

    docs = load_documents()
    print(f"\nOK Loaded {len(docs)} documents")

    chunks = chunk_documents(docs)
    print(f"OK Created {len(chunks)} chunks")

    chunks = embed_chunks(chunks)
    print(f"OK Embedded {len(chunks)} chunks")

    index_to_vectorstore(chunks)
    print("OK Indexed to vector store")
    print("\nDone.")


if __name__ == "__main__":
    run_pipeline()
