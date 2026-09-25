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

## Nhận task
Mọi người **tự nhận** issue. Project manager theo dõi tiến độ và duyệt pull request.

1. Mở [danh sách issue](https://github.com/TieuDaoChanNhan/bureau-agent/issues). Chọn issue **chưa có ai trong ô Assignees**.
2. Ưu tiên theo thứ tự **P0 → P1 → P2**. Không nhận P1 khi còn P0 chưa có người, trừ khi project manager đồng ý.
3. Kiểm tra mục **Phụ thuộc** của task: chỉ nhận khi các task phụ thuộc đã xong (issue đã đóng), hoặc task ghi rõ làm trước được bằng dữ liệu giả (ví dụ T06 dùng `docs/api-examples/`).
4. Nhận bằng cách tự gán mình vào ô **Assignees** và bình luận `Mình nhận` kèm thời gian dự kiến xong (ví dụ "xong trước 18:00").
5. **Mỗi người chỉ giữ một issue đang làm** tại một thời điểm. Xong (đã mở pull request) mới nhận issue tiếp theo.
6. Nếu **3 giờ** không có commit nào được đẩy lên nhánh, hoặc bạn không làm tiếp được, gỡ mình khỏi Assignees và bình luận lý do để người khác nhận. Project manager có thể gỡ người khỏi issue đứng yên quá lâu.
7. Gặp vướng mắc, bình luận ngay trong issue để cả nhóm thấy.

## Quy trình một task
1. Cập nhật `main` rồi tạo nhánh theo tên gợi ý: `git switch main && git pull && git switch -c t05-api`.
2. Commit nhỏ, thường xuyên. Thông điệp commit bằng tiếng Anh, bắt đầu bằng ID task: `T05: implement approve route`.
3. Đẩy nhánh sớm (`git push -u origin t05-api`) để mọi người thấy tiến độ.
4. Mở pull request vào `main`. Tiêu đề `T05: ...`, trong mô tả có `Closes #<số issue>` để issue tự đóng khi gộp. Điền mẫu pull request, đánh dấu từng mục "Xong khi" của task.
5. CI phải xanh. Project manager (hoặc một thành viên khác) review rồi gộp bằng **Squash and merge**. Nhánh tự xóa sau khi gộp.
6. Nếu được yêu cầu sửa, sửa trên cùng nhánh; pull request tự cập nhật.

**Không sửa `TASKS.md` trong pull request của task.** Trạng thái nằm trên issue; `TASKS.md` do project manager cập nhật.

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
- Cách viết test (mẫu, đặt test ở đâu, chạy riêng một test): [tests/README.md](tests/README.md#adding-a-test).
