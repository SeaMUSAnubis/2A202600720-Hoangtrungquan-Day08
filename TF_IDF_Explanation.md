# Giải thích Cơ chế Lexical Search: TF-IDF vs BM25

## 1. Cơ chế Lexical Search là gì?
Lexical Search (tìm kiếm từ vựng) là phương pháp tìm kiếm dựa trên sự khớp chính xác của các từ khóa (keyword matching) giữa câu truy vấn (query) và tài liệu (document). Thay vì hiểu "ngữ nghĩa" của câu như Semantic Search, Lexical Search tập trung vào tần suất xuất hiện của từ khóa để đánh giá mức độ liên quan.

## 2. TF-IDF (Term Frequency - Inverse Document Frequency)
TF-IDF là một trong những thuật toán cơ bản và kinh điển nhất của Lexical Search. Nó đánh giá tầm quan trọng của một từ đối với một tài liệu trong một tập hợp các tài liệu (corpus).

**Công thức cơ bản:** `TF-IDF = TF * IDF`

* **TF (Term Frequency):** Tần suất xuất hiện của từ khóa trong tài liệu.
  * Càng xuất hiện nhiều lần trong một tài liệu, từ khóa đó càng quan trọng với tài liệu đó.
  * Nhược điểm: Không giới hạn. Nếu tài liệu rất dài, một từ lặp lại 100 lần sẽ có điểm TF rất cao, lấn át các từ khóa khác.
* **IDF (Inverse Document Frequency):** Tần suất nghịch đảo của từ khóa trong toàn bộ tập tài liệu.
  * Nếu một từ xuất hiện trong hầu hết các tài liệu (như "và", "là", "của", "pháp luật"), nó mang rất ít thông tin đặc trưng để phân biệt tài liệu. IDF sẽ phạt những từ này (điểm thấp đi).
  * Nếu một từ hiếm (như "ketamine", "heroin"), nó có giá trị phân loại cao. IDF sẽ thưởng cho những từ này (điểm cao lên).

**Hạn chế của TF-IDF:**
- **Không kiểm soát được độ dài tài liệu:** Tài liệu dài hơn tự nhiên có tần suất từ xuất hiện cao hơn, dễ được ưu tiên hơn các tài liệu ngắn súc tích.
- **Tần suất tăng tuyến tính:** Sự khác biệt giữa 1 lần xuất hiện và 2 lần xuất hiện có ý nghĩa lớn, nhưng sự khác biệt giữa 100 và 101 lần là rất nhỏ. Tuy nhiên, TF cơ bản cứ cộng dồn tuyến tính.

## 3. BM25 (Best Matching 25) - Sự tiến hóa của TF-IDF
Thuật toán BM25 (được sử dụng trong dự án RAG này) là phiên bản tối ưu và hiện đại hơn của TF-IDF. Nó giải quyết triệt để hai hạn chế lớn nhất của TF-IDF:

1. **Chuẩn hóa theo độ dài tài liệu (Document Length Normalization):**
   * BM25 đưa vào tham số `b` (thường bằng 0.75). Tham số này điều chỉnh điểm số dựa trên độ dài của tài liệu so với độ dài trung bình của toàn bộ tập tài liệu.
   * Nếu tài liệu quá dài, BM25 sẽ giảm điểm của nó một chút để công bằng với các tài liệu ngắn.

2. **Bão hòa Tần suất từ khóa (Term Frequency Saturation):**
   * BM25 đưa vào tham số `k1` (thường từ 1.2 đến 2.0).
   * Điểm TF trong BM25 không tăng tuyến tính mãi mãi mà sẽ tiến dần đến một ngưỡng bão hòa (asymptote). Nghĩa là từ khóa xuất hiện lần thứ 1 đến lần thứ 3 sẽ tăng điểm rất nhanh, nhưng từ lần thứ 10 trở đi, việc xuất hiện thêm không làm tăng điểm đáng kể nữa. Điều này ngăn chặn spam từ khóa.

## 4. Tại sao dự án này chọn BM25 thay vì TF-IDF?
Trong hệ thống RAG pháp luật:
- **Ngữ cảnh luật pháp:** Các điều luật có độ dài rất khác nhau (có điều rất ngắn, có điều rất dài). Khả năng chuẩn hóa độ dài của BM25 giúp các điều luật ngắn không bị lép vế.
- **Từ khóa chuyên ngành:** Các từ như "tàng trữ", "mua bán", "ma túy" có thể lặp lại nhiều lần. Tính năng bão hòa tần suất của BM25 giúp kết quả không bị thiên lệch vào một văn bản chỉ vì nó spam từ khóa đó nhiều lần.
- **Hiệu năng:** BM25 được chứng minh qua nhiều thập kỷ là thuật toán xếp hạng văn bản (text ranking) hiệu quả nhất cho lexical matching và được sử dụng làm lõi của các hệ thống tìm kiếm hàng đầu như Elasticsearch, Lucene.
