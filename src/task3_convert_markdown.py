import json
from pathlib import Path
from markitdown import MarkItDown

# Xác định đường dẫn thư mục dựa trên vị trí file script này
LANDING_DIR = Path(__file__).parent.parent / "data" / "landing"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "standardized"


def convert_legal_docs():
    """Convert PDF/DOCX files trong data/landing/legal/ sang markdown."""
    legal_dir = LANDING_DIR / "legal"
    output_dir = OUTPUT_DIR / "legal"
    
    # Kiểm tra thư mục đầu vào có tồn tại không
    if not legal_dir.exists():
        print(f" Thư mục không tồn tại: {legal_dir}")
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    md = MarkItDown()

    for filepath in legal_dir.iterdir():
        if filepath.is_file() and filepath.suffix.lower() in (".pdf", ".docx", ".doc"):
            print(f"Converting: {filepath.name}")
            try:
                # Sử dụng MarkItDown để convert
                result = md.convert(str(filepath))
                output_path = output_dir / f"{filepath.stem}.md"
                
                # Ghi nội dung vào file markdown mới
                output_path.write_text(result.text_content, encoding="utf-8")
                print(f"  ✓ Saved: {output_path.name}")
            except Exception as e:
                print(f"  Error converting {filepath.name}: {e}")


def convert_news_articles():
    """Convert JSON crawled articles trong data/landing/news/ sang markdown."""
    news_dir = LANDING_DIR / "news"
    output_dir = OUTPUT_DIR / "news"
    
    if not news_dir.exists():
        print(f" Thư mục không tồn tại: {news_dir}")
        return

    output_dir.mkdir(parents=True, exist_ok=True)

    for filepath in news_dir.iterdir():
        if filepath.is_file() and filepath.suffix.lower() == ".json":
            print(f"Converting: {filepath.name}")
            try:
                # Đọc file JSON
                data = json.loads(filepath.read_text(encoding="utf-8"))
                output_path = output_dir / f"{filepath.stem}.md"
                
                # Tạo metadata header theo chuẩn Markdown
                header = f"# {data.get('title', 'Unknown')}\n\n"
                header += f"**Source:** {data.get('url', 'N/A')}\n"
                header += f"**Crawled:** {data.get('date_crawled', 'N/A')}\n\n---\n\n"
                
                # Gộp header và nội dung chính
                content = header + data.get("content_markdown", "")
                
                # Lưu file .md
                output_path.write_text(content, encoding="utf-8")
                print(f"  ✓ Saved: {output_path.name}")
            except Exception as e:
                print(f" Error converting {filepath.name}: {e}")


def convert_all():
    """Convert toàn bộ files."""
    print("=" * 50)
    print("Task 3: Convert to Markdown (MarkItDown)")
    print("=" * 50)

    print("\n--- Legal Documents ---")
    convert_legal_docs()

    print("\n--- News Articles ---")
    convert_news_articles()

    print("\n" + "=" * 50)
    print(f"✓ Hoàn thành! Toàn bộ file lưu tại: {OUTPUT_DIR}")
    print("=" * 50)


if __name__ == "__main__":
    convert_all()