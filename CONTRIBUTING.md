# Cách làm việc chung

## Cài đặt lần đầu
```bash
git clone https://github.com/TieuDaoChanNhan/bureau-agent.git && cd bureau-agent
python -m venv .venv
# macOS / Linux:  source .venv/bin/activate
# Windows:        .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                       # điền khóa của chính bạn, không chia sẻ
git config core.hooksPath .githooks        # bật kiểm thử tự động trước mỗi commit
python -m unittest discover -s tests -t .
```
- **Windows:** nếu tên có dấu hiển thị sai trong terminal, chạy `set PYTHONIOENCODING=utf-8` (cmd) hoặc `$env:PYTHONIOENCODING="utf-8"` (PowerShell).
- Nếu kiểm thử không qua trên máy bạn, báo trong nhóm trước khi bắt đầu task.

## Quy trình một task
1. Trưởng nhóm gán cho bạn một issue trên GitHub (mỗi task trong [TASKS.md](TASKS.md) là một issue). Không tự nhận issue chưa được gán.
2. Cập nhật `main` rồi tạo nhánh theo tên gợi ý: `git switch main && git pull && git switch -c t05-api`.
3. Commit nhỏ, thường xuyên. Thông điệp commit bằng tiếng Anh, bắt đầu bằng ID task: `T05: implement approve route`.
4. Đẩy nhánh và mở pull request vào `main`. Tiêu đề `T05: ...`, trong mô tả có `Closes #<số issue>` để issue tự đóng khi gộp. Điền mẫu pull request, đánh dấu từng mục "Xong khi" của task.
5. CI phải xanh. Một người khác review (đọc code, chạy thử nếu cần) rồi mới gộp. Dùng **Squash and merge**.
6. Gộp xong thì xóa nhánh.

**Không sửa `TASKS.md` trong pull request của task.** Trạng thái nằm trên issue; `TASKS.md` do trưởng nhóm cập nhật.

## Kiểm thử tự động
| Khi nào | Cái gì chạy | Ở đâu |
|---|---|---|
| Trước mỗi commit (nếu đã bật hook) | Toàn bộ test (dưới 1 giây) | Máy bạn, `.githooks/pre-commit` |
| Mỗi lần push lên bất kỳ nhánh nào, mỗi pull request | Toàn bộ test | GitHub Actions, `.github/workflows/tests.yml` |

Cần commit gấp khi test đang đỏ (ví dụ lưu việc dở dang): `git commit --no-verify`, nhưng pull request vẫn phải xanh mới được gộp.

## Quy tắc
| Quy tắc | Lý do |
|---|---|
| `main` luôn chạy được; không push thẳng vào `main` | Ai cũng có thể demo bất kỳ lúc nào |
| Đổi `bureau/core/models.py` hoặc `bureau/planner/interface.py` phải báo cả nhóm trước, và chạy lại `python docs/api-examples/generate.py` | Đây là hợp đồng dữ liệu chung, giao diện web phụ thuộc vào nó |
| Agent không bao giờ thực thi; chỉ `core/executor.py` được đổi trạng thái | Con người duyệt mọi hành động có hệ quả |
| Quy tắc cần chính xác viết bằng code và có test, không đưa vào prompt | "Code cho quy tắc bất biến" |
| Tiền là số nguyên (cent); ngày giờ có múi giờ | Tránh lỗi làm tròn và lệch giờ |
| Không commit `.env`, khóa API, dữ liệu cá nhân thật | Repo sẽ công khai khi nộp bài |
| Code, comment, commit, README bằng tiếng Anh; `TASKS.md`, `CONTRIBUTING.md`, `docs/` bằng tiếng Việt | Giám khảo đọc repo; nhóm đọc tài liệu nội bộ |
| Thêm tệp mới thì cập nhật README của thư mục đó | Người mới vào đọc hiểu nhanh |

## Phong cách code
- Python 3.11, gợi ý kiểu cho hàm công khai, docstring ngắn nói hàm làm gì và trả về gì.
- Comment giải thích *vì sao*, không lặp lại code.
- Hàm trong `bureau/tools/` là hàm thuần: nhận `EventState`, trả dữ liệu chuyển được sang JSON.
- Chỗ chưa làm: `raise NotImplementedError("TASK Txx")`. Tìm `TASK T` để thấy mọi chỗ còn thiếu.
- Test cho agent dùng `tests/fake_llm.py`, không gọi API thật trong test.
