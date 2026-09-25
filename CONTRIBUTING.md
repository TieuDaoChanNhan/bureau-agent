# Cách làm việc chung

## Cài đặt lần đầu
```bash
git clone <repo-url> && cd bureau-agent
pip install -r requirements.txt
cp .env.example .env              # điền khóa của chính bạn, không chia sẻ
python -m unittest discover -s tests -t .
```
Nếu kiểm thử không qua trên máy bạn, báo trong nhóm trước khi bắt đầu task.

## Quy trình một task
1. Trưởng nhóm giao task trong [TASKS.md](TASKS.md). Không tự nhận task chưa được giao.
2. Tạo nhánh từ `main` mới nhất, đặt tên theo gợi ý trong task, ví dụ `t05-api`.
3. Commit nhỏ, thường xuyên. Thông điệp commit bằng tiếng Anh, bắt đầu bằng ID task: `T05: implement approve route`.
4. Mở pull request vào `main`, tiêu đề `T05: ...`, điền mẫu có sẵn. Cập nhật trạng thái task trong `TASKS.md` ngay trong pull request đó.
5. Kiểm thử trên CI phải qua. Một người khác xem nhanh rồi mới gộp.
6. Gộp xong thì xóa nhánh.

## Quy tắc
| Quy tắc | Lý do |
|---|---|
| `main` luôn chạy được | Ai cũng có thể demo bất kỳ lúc nào |
| Đổi `bureau/core/models.py` hoặc `bureau/planner/interface.py` phải báo cả nhóm trước | Đây là hợp đồng dữ liệu chung |
| Agent không bao giờ thực thi; chỉ `core/executor.py` được đổi trạng thái | Nguyên tắc sản phẩm: con người duyệt mọi hành động có hệ quả |
| Quy tắc cần chính xác viết bằng code và có test, không đưa vào prompt | "Code cho quy tắc bất biến" |
| Tiền là số nguyên (cent); ngày giờ có múi giờ | Tránh lỗi làm tròn và lệch giờ |
| Không commit `.env`, khóa API, dữ liệu cá nhân thật | Repo sẽ công khai khi nộp bài |
| Code, comment, commit, README bằng tiếng Anh; tài liệu nội bộ trong `docs/` có thể bằng tiếng Việt | Giám khảo quốc tế đọc repo |
| Mỗi thư mục có README ngắn; thêm tệp mới thì cập nhật README của thư mục đó | Người mới vào đọc hiểu nhanh |

## Phong cách code
- Python 3.11, gợi ý kiểu (type hints) cho hàm công khai, docstring ngắn nói hàm làm gì và trả về gì.
- Comment giải thích *vì sao*, không lặp lại code.
- Hàm trong `bureau/tools/` là hàm thuần: nhận `EventState`, trả dữ liệu tuần tự hóa được sang JSON.
- Chỗ chưa làm: `raise NotImplementedError("TASK Txx")` để ai cũng tìm được bằng cách tìm `TASK T`.

## Chạy nhanh
```bash
python -m bureau detect hackathon
python -m bureau plan wei --budget 90
uvicorn api.main:app --reload
```
