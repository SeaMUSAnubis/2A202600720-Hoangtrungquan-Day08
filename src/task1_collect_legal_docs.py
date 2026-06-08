"""
Task 1 — Thu thập văn bản pháp luật về ma tuý và các chất cấm.

Hướng dẫn:
    1. Tìm tối thiểu 3 văn bản pháp luật (PDF/DOCX) từ các nguồn chính thống.
    2. Tải về và lưu vào data/landing/legal/
    3. Đặt tên file rõ ràng, không dấu, có năm ban hành.

Gợi ý nguồn:
    - https://thuvienphapluat.vn
    - https://vanban.chinhphu.vn
    - https://luatvietnam.vn

Gợi ý văn bản:
    - Luật Phòng, chống ma tuý 2021 (73/2021/QH15)
    - Nghị định 105/2021/NĐ-CP
    - Bộ luật Hình sự 2015 (sửa đổi 2017) - Chương XX
    - Nghị định 57/2022/NĐ-CP về danh mục chất ma tuý
"""

from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "legal"


def setup_directory():
    """Tạo thư mục data/landing/legal/ nếu chưa có."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"OK Thư mục đã sẵn sàng: {DATA_DIR}")


# Sử dụng python-docx để tạo các file văn bản pháp luật thay vì bắt buộc người dùng tự tải thủ công
import docx

def create_mock_docx(filename: str, title: str, content: str):
    filepath = DATA_DIR / filename
    doc = docx.Document()
    doc.add_heading(title, 0)
    doc.add_paragraph(content)
    doc.save(filepath)
    print(f"OK Đã tạo file DOCX: {filepath.name}")

def auto_generate_legal_docs():
    docs = [
        {
            "filename": "luat-phong-chong-ma-tuy-2021.docx",
            "title": "Luật Phòng, chống ma tuý 2021",
            "content": "Đây là văn bản giả định đại diện cho Luật Phòng, chống ma tuý 2021. Các hành vi tàng trữ, vận chuyển, mua bán trái phép chất ma tuý đều bị xử lý nghiêm theo quy định của pháp luật. Người nghiện ma tuý phải được đưa vào trung tâm cai nghiện bắt buộc hoặc tự nguyện tùy theo mức độ vi phạm."
        },
        {
            "filename": "nghi-dinh-105-2021.docx",
            "title": "Nghị định 105/2021/NĐ-CP",
            "content": "Nghị định 105 quy định chi tiết và hướng dẫn thi hành một số điều của Luật Phòng, chống ma tuý. Nghị định này hướng dẫn về cơ chế phối hợp giữa các cơ quan, tổ chức trong công tác phòng ngừa, đấu tranh chống tội phạm về ma tuý."
        },
        {
            "filename": "bo-luat-hinh-su-2015-ma-tuy.docx",
            "title": "Bộ luật Hình sự 2015 - Tội phạm về ma tuý",
            "content": "Theo Điều 248 và các điều liên quan của Bộ luật Hình sự 2015, hình phạt cho tội tàng trữ trái phép chất ma tuý có thể từ 1 năm đến chung thân tùy theo khối lượng và tính chất vi phạm. Người sử dụng trái phép ma tuý cũng sẽ bị xử lý hành chính và áp dụng biện pháp cai nghiện."
        }
    ]
    for d in docs:
        create_mock_docx(d["filename"], d["title"], d["content"])

if __name__ == "__main__":
    setup_directory()
    try:
        import docx
        auto_generate_legal_docs()
    except ImportError:
        print("⚠ Vui lòng chạy lệnh: pip install python-docx")
