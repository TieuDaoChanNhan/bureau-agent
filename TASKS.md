# Tasks

Danh sách công việc của dự án. Trưởng nhóm phân công bằng cách điền cột **Người làm**. Người được giao tạo nhánh riêng theo tên gợi ý, làm xong thì mở pull request (xem [CONTRIBUTING.md](CONTRIBUTING.md)) và cập nhật cột **Trạng thái** trong cùng pull request.

**Mức ưu tiên:** **P0** = bắt buộc để có demo hackathon · **P1** = kịch bản chuyến đi (điểm nhấn demo) · **P2** = nộp bài và hoàn thiện.
**Trạng thái:** ⬜ chưa làm · 🟡 đang làm · 🔍 chờ review · ✅ xong.
**Mốc cắt:** nếu 12:00 thứ Bảy 26/09 các task P0 chưa chạy trọn luồng, tạm dừng P1.

## Bảng tổng
| ID | Ưu tiên | Task | Phụ thuộc | Người làm | Trạng thái |
|---|---|---|---|---|---|
| T01 | P0 | Khung repo, CI, tài liệu | — | | ✅ |
| T02 | P0 | Lưu trữ runtime (`store.py`) | — | | ⬜ |
| T03 | P0 | Thực thi hành động đã duyệt (`executor.py`) | — | | ⬜ |
| T04 | P0 | Chạy agent với OpenAI thật, chỉnh prompt | khóa API | | ⬜ |
| T05 | P0 | Các route API còn lại | T02, T03, T04 | | ⬜ |
| T06 | P0 | Giao diện web: sự kiện, vấn đề, chi tiết, duyệt | định dạng JSON (có sẵn) | | ⬜ |
| T07 | P0 | Làm giàu dữ liệu mẫu hackathon | — | | ⬜ |
| T08 | P0 | Bộ đánh giá offline | T04, T07 | | ⬜ |
| T09 | P0 | Chạy agent hàng loạt và lưu đề xuất | T02, T04 | | ⬜ |
| T10 | P1 | Tách ràng buộc bằng LLM (thử Pipelex) | — | | ⬜ |
| T11 | P1 | Client Jinko (live / replay) | khóa Jinko sandbox | | ⬜ |
| T12 | P1 | Ghép phương án trọn gói bằng code | T11 (định dạng) | | ⬜ |
| T13 | P1 | Viết giải thích đánh đổi bằng LLM | — | | ⬜ |
| T14 | P1 | Nối planner với Jinko + ghép phương án, route `/plan` | T11, T12, T05 | | ⬜ |
| T15 | P1 | Giao diện chuyến đi: bảng so sánh, thử ngân sách | T06, T14 | | ⬜ |
| T16 | P1 | Dữ liệu một chuyến đi thật của hội sinh viên | — | | ⬜ |
| T17 | P2 | README cuối, sơ đồ kiến trúc, kịch bản và video demo | P0 xong | | ⬜ |
| T18 | P2 | Buổi thử với người tổ chức thật | P0 xong | | ⬜ |
| T19 | P2 | Kiểm tra trước khi nộp: quét bí mật, công khai repo, nộp form | T17 | | ⬜ |
| T20 | P2 | Triển khai demo miễn phí (Hugging Face Spaces, Docker) | T05, T06 | | ⬜ |

---

## Chi tiết

### T02 · Lưu trữ runtime · P0
- **Nhánh:** `t02-store` · **Tệp:** `bureau/core/store.py`, `tests/test_pending.py`
- **Kỹ năng:** Python, JSON
- **Việc:** cài đặt các hàm trong `store.py` theo docstring: đọc/ghi `runtime/<event>/` (state, issues, actions, outbox, log), `merge_issue_status` giữ trạng thái vấn đề sau khi phát hiện lại, `reset`.
- **Xong khi:** bỏ `@skip` của `StoreTests` và test qua; thêm test cho `reset` và cho vấn đề không còn được phát hiện.

### T03 · Thực thi hành động · P0
- **Nhánh:** `t03-executor` · **Tệp:** `bureau/core/executor.py`, `tests/test_pending.py`
- **Kỹ năng:** Python
- **Việc:** `apply()` theo bảng tác động trong docstring; không sửa trạng thái gốc nếu vi phạm quy tắc bất biến (dùng `check_groups`, ...); ghi `resolved_by_action_id`.
- **Xong khi:** bỏ `@skip` của `ExecutorTests`, test qua; mỗi `action_type` có ít nhất một test.

### T04 · Chạy agent thật · P0
- **Nhánh:** `t04-agent-live` · **Tệp:** `bureau/agent/*`
- **Kỹ năng:** LLM, prompt, gọi công cụ
- **Việc:** chạy `python -m bureau run hackathon` với khóa thật; sửa lỗi vòng lặp; chỉnh prompt để agent **tự chọn** công cụ (không thêm luật cứng). Luồng trọng tâm: tin nhắn `m01` → tìm người gửi → xem thanh toán chưa khớp → `match_person` → đề xuất `LINK_PAYMENT` kèm câu hỏi cho người tổ chức.
- **Xong khi:** cả 5 tin nhắn mẫu và 3 vấn đề cấu trúc cho ra đề xuất hợp lý; ghi lại kết quả mẫu vào `eval/results/` (hoặc mô tả trong pull request).

### T05 · Route API · P0
- **Nhánh:** `t05-api` · **Tệp:** `api/main.py`
- **Kỹ năng:** FastAPI
- **Việc:** cài đặt các route đang trả 501 (xem `api/README.md`), dùng `store` và `executor`; `approve` nhận `edited_description` và `option_id`.
- **Xong khi:** duyệt một đề xuất qua API làm vấn đề biến mất ở lần `GET` sau; có test gọi API (FastAPI `TestClient`).

### T06 · Giao diện web · P0
- **Nhánh:** `t06-web` · **Tệp:** `web/*`
- **Kỹ năng:** HTML, CSS, JavaScript
- **Việc:** dựng lại bố cục của `web/reference/mockup.html` trên dữ liệu thật từ API: thẻ sự kiện, danh sách vấn đề (chặn trước), chi tiết (decision trace, phép kiểm tra, hành động có thể sửa), nút duyệt/sửa/bỏ qua. Khi route còn 501, giả lập phản hồi đúng định dạng.
- **Xong khi:** duyệt được một đề xuất từ giao diện; dùng được trên màn hình điện thoại.

### T07 · Dữ liệu mẫu hackathon · P0
- **Nhánh:** `t07-sample-data` · **Tệp:** `data/hackathon/*`, `data/README.md`
- **Kỹ năng:** hiểu cách một hội vận hành sự kiện
- **Việc:** tăng lên khoảng 40–60 người tham gia và 20–30 tin nhắn thực tế (tiếng Pháp và tiếng Anh), giữ các tình huống cài sẵn và thêm vài tình huống mới (hỏi quy chế, hỏi không có trong quy chế, thanh toán mơ hồ). Dữ liệu hoàn toàn hư cấu.
- **Xong khi:** mọi test vẫn qua (cập nhật số liệu kỳ vọng nếu cần); `data/README.md` liệt kê tình huống cài sẵn.

### T08 · Đánh giá offline · P0
- **Nhánh:** `t08-eval` · **Tệp:** `eval/*`
- **Kỹ năng:** Python, gán nhãn dữ liệu
- **Việc:** gán nhãn khoảng 50 tin nhắn trong `cases/messages.jsonl`; cài đặt `run_eval.py` tính các chỉ số trong `eval/README.md`; in bảng và lưu `eval/results/`.
- **Xong khi:** `python -m eval.run_eval` in bảng chỉ số; số "vi phạm quy tắc bất biến" được đo.

### T09 · Chạy agent hàng loạt · P0
- **Nhánh:** `t09-batch-run` · **Tệp:** `bureau/cli.py`, `bureau/agent/loop.py`
- **Việc:** chạy agent cho mọi vấn đề mở chưa có đề xuất và không bị chặn bởi phụ thuộc; lưu đề xuất qua `store`; bỏ qua vấn đề đã có đề xuất.
- **Xong khi:** chạy hai lần liên tiếp không tạo đề xuất trùng.

### T10 · Tách ràng buộc bằng LLM · P1
- **Nhánh:** `t10-extract` · **Tệp:** `bureau/planner/extract.py`
- **Kỹ năng:** LLM, đầu ra có cấu trúc; Pipelex (tùy chọn)
- **Việc:** thử Pipelex trước, **giới hạn khoảng 1,5 giờ**; nếu không kịp, dùng OpenAI structured output. Tuân thủ quy tắc trong docstring (không bịa, mơ hồ thì hỏi lại, tiền bằng cent, ràng buộc khả năng tiếp cận vào `organizer_verified`).
- **Xong khi:** đúng với `eval/cases/planning.jsonl`; thêm ít nhất 5 yêu cầu có nhãn.

### T11 · Client Jinko · P1
- **Nhánh:** `t11-jinko` · **Tệp:** `bureau/planner/jinko.py`, `data/wei/jinko_cache/`
- **Kỹ năng:** HTTP API
- **Việc:** gọi `POST /v1/ground_search` và `POST /v1/hotel_search` trên sandbox; chuẩn hóa kết quả theo docstring; chế độ `live` lưu phản hồi, `replay` chỉ đọc bộ nhớ đệm. Kiểm tra lại các chi tiết đánh dấu "verify" trong docstring.
- **Xong khi:** chạy `replay` không cần mạng; có ít nhất một bộ phản hồi thật được lưu cho kịch bản WEI.

### T12 · Ghép phương án · P1
- **Nhánh:** `t12-compose` · **Tệp:** `bureau/planner/compose.py`, `tests/test_planner.py`
- **Việc:** theo docstring; mọi phép tính giá bằng số nguyên; luôn giữ phương án rẻ nhất.
- **Xong khi:** có test cho cách tính giá mỗi người và việc giữ phương án rẻ nhất.

### T13 · Giải thích đánh đổi · P1
- **Nhánh:** `t13-explain` · **Tệp:** `bureau/planner/explain.py`
- **Việc:** 2–4 câu dễ hiểu; không được đổi thứ hạng hay kết quả kiểm tra; có thể dùng Pipelex như T10.
- **Xong khi:** giải thích nhắc đúng phương án đứng đầu và lý do phương án bị loại.

### T14 · Nối planner · P1
- **Nhánh:** `t14-planner-wiring` · **Tệp:** `bureau/planner/planner.py`, `api/main.py`
- **Việc:** `search_options` dùng `jinko` + `compose`; route `POST /api/events/{id}/plan` với `overrides` (ví dụ đổi ngân sách).
- **Xong khi:** ngân sách 120€ cho 2 phương án hợp lệ, 90€ cho ESCALATE kèm chẩn đoán, trên dữ liệu Jinko đã lưu.

### T15 · Giao diện chuyến đi · P1
- **Nhánh:** `t15-web-trip` · **Tệp:** `web/*`
- **Việc:** hiển thị ràng buộc cứng/mềm, bảng so sánh phương án (lý do bị loại tô đỏ), ràng buộc cần người tổ chức xác nhận, nút chọn phương án, thử đổi ngân sách.
- **Xong khi:** chọn một phương án làm các vấn đề phụ thuộc được mở khóa.

### T16 · Dữ liệu chuyến đi thật · P1
- **Nhánh:** `t16-real-trip` · **Tệp:** `data/wei/*`
- **Việc:** thay kịch bản WEI bằng thông số một chuyến đi thật của một hội sinh viên (điểm đến, số người, ngân sách, yêu cầu), không dùng dữ liệu cá nhân thật.
- **Xong khi:** planner chạy trên kịch bản mới; ghi nguồn trong `data/README.md`.

### T17 · Tài liệu và video · P2
- **Nhánh:** `t17-docs-demo`
- **Việc:** cập nhật README (trạng thái, kết quả đánh giá, giới hạn), sơ đồ kiến trúc, kịch bản video 2 phút (xem `docs/product-proposal.md`), quay và dựng video.
- **Xong khi:** video ≤ 2 phút, xong trước **20:00 Chủ Nhật 27/09**.

### T18 · Thử với người tổ chức thật · P2
- **Việc:** một thành viên ban điều hành của một hội thật dùng thử khoảng 30 phút; ghi lại số đề xuất được duyệt nguyên văn, số lần sửa, thời gian, một câu nhận xét.
- **Xong khi:** kết quả có trong README, tách riêng với chỉ số offline.

### T19 · Trước khi nộp · P2
- **Việc:** quét lịch sử commit tìm khóa API; kiểm tra README chạy được trên một máy khác; chuyển repo sang công khai; nộp form trước **22:00 Chủ Nhật 27/09**.
- **Xong khi:** form đã nộp.

### T20 · Triển khai demo miễn phí · P2
- **Nhánh:** `t20-deploy` · **Tệp:** `Dockerfile`, `README.md`
- **Việc:** đóng gói API + web trong một container (FastAPI phục vụ cả hai); triển khai lên Hugging Face Spaces (Docker, gói CPU miễn phí). Khóa API đặt trong mục Secrets của Space, không nằm trong repo. Bản công khai chạy ở **chế độ demo**: dùng đề xuất đã lưu sẵn, chỉ gọi OpenAI khi có mật khẩu demo, để người lạ không tiêu hết credit.
- **Xong khi:** link công khai mở được giao diện, duyệt được một đề xuất; README có link.
