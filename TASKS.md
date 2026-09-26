# Tasks

Đặc tả các công việc của dự án. **Người làm và trạng thái được theo dõi trên GitHub Issues** (mỗi task một issue, cột "Issue" bên dưới). Tệp này chỉ do project manager sửa, để tránh xung đột khi nhiều pull request cùng cập nhật một bảng.

**Cách làm một task:** tự nhận một issue chưa có người (tự gán mình và bình luận `Mình nhận`) → tạo nhánh theo tên gợi ý → làm → mở pull request có dòng `Closes #<số issue>` → CI xanh và project manager duyệt → gộp. Quy tắc nhận task (ưu tiên, phụ thuộc, mỗi người một issue, nhả issue sau 3 giờ không tiến triển) trong [CONTRIBUTING.md](CONTRIBUTING.md#nhận-task).

**Ưu tiên:** **P0** bắt buộc cho demo · **P1** kịch bản chuyến đi · **P2** nộp bài.
**Mốc cắt:** 12:00 thứ Bảy 26/09 nếu P0 chưa chạy trọn luồng thì tạm dừng P1.

**Quy ước "Xong khi":** mọi mục phải kiểm được bằng **lệnh**, **test** hoặc **checklist có/không**. Mục ghi "Thêm test: …" nghĩa là viết thêm một hàm test trong thư mục `tests/` (hướng dẫn và mẫu: [tests/README.md](tests/README.md#adding-a-test)). Ngoài ra, mọi task đều cần: CI xanh, README của thư mục liên quan được cập nhật, không commit bí mật.

## Bảng tổng
| ID | Ưu tiên | Task | Phụ thuộc | Nhánh | Issue |
|---|---|---|---|---|---|
| T01 | P0 | Khung repo, CI, tài liệu | — | — | ✅ xong |
| T02 | P0 | Lưu trữ runtime | — | `t02-store` | [#1](https://github.com/TieuDaoChanNhan/bureau-agent/issues/1) |
| T03 | P0 | Thực thi hành động đã duyệt | — | `t03-executor` | [#2](https://github.com/TieuDaoChanNhan/bureau-agent/issues/2) |
| T04 | P0 | Chạy agent với OpenAI thật, chỉnh prompt | khóa OpenAI | `t04-agent-live` | [#3](https://github.com/TieuDaoChanNhan/bureau-agent/issues/3) |
| T05 | P0 | Các route API còn lại | T02, T03 | `t05-api` | [#4](https://github.com/TieuDaoChanNhan/bureau-agent/issues/4) |
| T06 | P0 | Giao diện web: sự kiện, vấn đề, chi tiết, duyệt | — (dùng JSON mẫu) | `t06-web` | [#5](https://github.com/TieuDaoChanNhan/bureau-agent/issues/5) |
| T07 | P0 | Làm giàu dữ liệu mẫu hackathon | — | `t07-sample-data` | [#6](https://github.com/TieuDaoChanNhan/bureau-agent/issues/6) |
| T08 | P0 | Bộ đánh giá offline | T04, T07 | `t08-eval` | [#7](https://github.com/TieuDaoChanNhan/bureau-agent/issues/7) |
| T09 | P0 | Chạy agent hàng loạt và lưu đề xuất | T02 | `t09-batch-run` | [#8](https://github.com/TieuDaoChanNhan/bureau-agent/issues/8) |
| T10 | P1 | Tách ràng buộc bằng LLM (thử Pipelex) | — | `t10-extract` | [#9](https://github.com/TieuDaoChanNhan/bureau-agent/issues/9) |
| T11 | P1 | Client Jinko (live / replay) | khóa Jinko sandbox | `t11-jinko` | [#10](https://github.com/TieuDaoChanNhan/bureau-agent/issues/10) |
| T12 | P1 | Ghép phương án trọn gói bằng code | — | `t12-compose` | [#11](https://github.com/TieuDaoChanNhan/bureau-agent/issues/11) |
| T13 | P1 | Giải thích đánh đổi bằng LLM | — | `t13-explain` | [#12](https://github.com/TieuDaoChanNhan/bureau-agent/issues/12) |
| T14 | P1 | Nối planner với Jinko + ghép phương án, route `/plan` | T05, T11, T12 | `t14-planner-wiring` | [#13](https://github.com/TieuDaoChanNhan/bureau-agent/issues/13) |
| T15 | P1 | Giao diện chuyến đi | T06 | `t15-web-trip` | [#14](https://github.com/TieuDaoChanNhan/bureau-agent/issues/14) |
| T16 | P1 | Dữ liệu một chuyến đi thật | — | `t16-real-trip` | [#15](https://github.com/TieuDaoChanNhan/bureau-agent/issues/15) |
| T17 | P2 | README cuối, sơ đồ, kịch bản và video demo | P0 xong | `t17-docs-demo` | [#16](https://github.com/TieuDaoChanNhan/bureau-agent/issues/16) |
| T18 | P2 | Buổi thử với người tổ chức thật | P0 xong | — | [#17](https://github.com/TieuDaoChanNhan/bureau-agent/issues/17) |
| T19 | P2 | Kiểm tra trước khi nộp, công khai repo, nộp form | T17 | `t19-release` | [#18](https://github.com/TieuDaoChanNhan/bureau-agent/issues/18) |
| T20 | P2 | Triển khai demo miễn phí | T05, T06 | `t20-deploy` | [#19](https://github.com/TieuDaoChanNhan/bureau-agent/issues/19) |
| T21 | P0 | Executor hardening (follow-up to T03) | T03 | `t21-executor-hardening` | [#24](https://github.com/TieuDaoChanNhan/bureau-agent/issues/24) |
| T22 | P0 | Robust agent batch run (shared runner, no lost proposals) | T05, T09 | `t22-robust-batch-run` | [#29](https://github.com/TieuDaoChanNhan/bureau-agent/issues/29) |
| T23 | P1 | Show names instead of ids in the web console | T06 | `t23-web-names` | [#33](https://github.com/TieuDaoChanNhan/bureau-agent/issues/33) |
| T24 | P2 | Bulk approval of safe replies in the web console | T06 | `t24-web-bulk-approve` | [#34](https://github.com/TieuDaoChanNhan/bureau-agent/issues/34) |
| T25 | P2 | Filter and search issues in the web console | T06 | `t25-web-filter` | [#35](https://github.com/TieuDaoChanNhan/bureau-agent/issues/35) |
| T26 | P2 | Automated tests for the web console | T06 | `t26-web-tests` | [#36](https://github.com/TieuDaoChanNhan/bureau-agent/issues/36) |
| T27 | P2 | `pyproject.toml` and uv alongside `requirements.txt` | — | `t27-uv` | [#37](https://github.com/TieuDaoChanNhan/bureau-agent/issues/37) |

T21–T27 were added after review follow-ups and PM planning; their full specification lives in the linked issue (in English), not in the details below.

---

## Chi tiết

### T02 · Lưu trữ runtime · P0
- **Tệp:** `bureau/core/store.py`, `tests/test_pending.py`
- **Việc:** cài đặt các hàm theo docstring: đọc/ghi `runtime/<event>/` (state, issues, actions, outbox, log), `merge_issue_status`, `reset`.
- **Xong khi:**
  - [ ] Bỏ `@unittest.skip` của `StoreTests`; test qua.
  - [ ] Thêm test: vấn đề không còn được phát hiện thì biến mất sau khi merge.
  - [ ] Thêm test: `save_state` rồi `load_state` cho lại cùng dữ liệu (số người, số thanh toán, thành viên nhóm), **và giữ nguyên `travel`, `logistics` với sự kiện `wei`**.
  - [ ] Thêm test: `reset` xong thì `load_state` trả về dữ liệu mẫu.

### T03 · Thực thi hành động · P0
- **Tệp:** `bureau/core/executor.py`, `tests/test_pending.py`
- **Việc:** `apply()` theo bảng tác động trong docstring; không đổi trạng thái nếu vi phạm quy tắc bất biến; ghi `resolved_by_action_id`.
- **Xong khi:**
  - [ ] Bỏ `@unittest.skip` của `ExecutorTests`; test qua.
  - [ ] Mỗi `action_type` (6 loại) có ít nhất một test.
  - [ ] Có test chứng minh hành động làm đội vượt 4 người bị từ chối và trạng thái gốc không đổi.

### T04 · Chạy agent với OpenAI thật · P0
- **Tệp:** `bureau/agent/*`
- **Việc:** chạy agent với khóa thật, sửa lỗi, chỉnh prompt. **Không thêm luật cứng** kiểu "nếu tin nhắn có chữ X thì gọi công cụ Y": agent phải tự chọn công cụ.
- **Xong khi:**
  - [ ] `python -m bureau run hackathon` chạy hết không lỗi.
  - [ ] Với 3 ca trong `eval/cases/messages.jsonl`: `action_type` đúng với `expected_action`; ca có `must_ask_human: true` thì đề xuất có câu hỏi cho người tổ chức hoặc là `ESCALATE`.
  - [ ] Ca `c001` (tin `m01`): agent có gọi `match_person` (xem dòng `->` in ra màn hình).
  - [ ] Dán kết quả chạy (các dòng `->` và JSON đề xuất) vào mô tả pull request.
  - [ ] `tests/test_agent.py` vẫn qua.

### T05 · Route API · P0
- **Tệp:** `api/main.py`, thêm `tests/test_api.py`
- **Việc:** cài đặt các route đang trả 501 (xem `api/README.md`), dùng `store` và `executor`. Định dạng phản hồi khớp `docs/api-examples/`.
- **Xong khi:**
  - [ ] Không còn route nào trả 501.
  - [ ] `tests/test_api.py` (dùng `fastapi.testclient.TestClient`) kiểm: `approve` một hành động làm vấn đề tương ứng biến mất ở lần `GET /api/events/{id}` sau; `reset` đưa về dữ liệu mẫu; `dismiss` không đổi dữ liệu.
  - [ ] Phản hồi của `GET /api/actions/{id}` có đủ các khóa như `docs/api-examples/action_LINK_PAYMENT.json`.

### T06 · Giao diện web · P0
- **Tệp:** `web/*`
- **Việc:** dựng bố cục của `web/reference/mockup.html` trên API thật. Route còn 501 thì dùng JSON trong `docs/api-examples/`.
- **Xong khi (checklist kiểm bằng tay, ghi kết quả trong pull request):**
  - [ ] Thẻ sự kiện hiện số vấn đề chặn / không chặn / đã giải quyết.
  - [ ] Danh sách vấn đề: chặn đứng trước, có nhãn trạng thái.
  - [ ] Chi tiết vấn đề: đầu vào, decision trace (checked / found / applied / proposed), danh sách phép kiểm tra ✓/✗, hành động đề xuất sửa được.
  - [ ] Nút duyệt / sửa / bỏ qua gọi đúng route; sau khi duyệt, vấn đề biến mất khỏi danh sách.
  - [ ] Ở bề rộng 400 px không có thanh cuộn ngang (Chrome DevTools, chế độ thiết bị).
  - [ ] Có ảnh chụp màn hình trong pull request.

### T07 · Dữ liệu mẫu hackathon · P0
- **Tệp:** `data/hackathon/*`, `data/README.md`
- **Việc:** 40–60 người tham gia, 20–30 tin nhắn (tiếng Pháp và tiếng Anh), giữ các tình huống cài sẵn, thêm tình huống mới. Dữ liệu hư cấu hoàn toàn.
- **Xong khi:**
  - [ ] Số người trong `participants.json` từ 40 đến 60; số tin nhắn trong `messages.json` từ 20 đến 30.
  - [ ] Mọi ngày giờ có múi giờ, mọi số tiền là `amount_cents` (loader không báo lỗi).
  - [ ] `data/README.md` liệt kê từng tình huống cài sẵn và kết quả mong đợi.
  - [ ] Test vẫn qua (cập nhật số kỳ vọng trong test nếu cần, ghi rõ trong pull request).

### T08 · Đánh giá offline · P0
- **Tệp:** `eval/*`
- **Việc:** gán nhãn khoảng 50 tin nhắn; cài đặt `run_eval.py`.
- **Xong khi:**
  - [ ] `eval/cases/messages.jsonl` có ít nhất 40 dòng, mỗi dòng đủ các khóa như dòng mẫu.
  - [ ] `python -m eval.run_eval` in bảng gồm: độ chính xác loại hành động, chọn đúng công cụ, trích đúng điều khoản, hỏi người đúng lúc, số vi phạm quy tắc bất biến.
  - [ ] Kết quả được lưu vào `eval/results/<thời gian>.json`.

### T09 · Chạy agent hàng loạt · P0
- **Tệp:** `bureau/cli.py`, `bureau/agent/loop.py`
- **Việc:** chạy agent cho mọi vấn đề mở, chưa có đề xuất, không bị chặn bởi phụ thuộc; lưu đề xuất qua `store`.
- **Xong khi:**
  - [ ] Test (dùng `tests/fake_llm.py`) chứng minh: chạy hai lần liên tiếp không tạo đề xuất trùng.
  - [ ] Test chứng minh vấn đề có `depends_on` chưa xong thì không được gửi cho agent.

### T10 · Tách ràng buộc bằng LLM · P1
- **Tệp:** `bureau/planner/extract.py`, `eval/cases/planning.jsonl`
- **Việc:** thử Pipelex trước, **tối đa khoảng 1,5 giờ**; không kịp thì dùng OpenAI structured output. Tuân thủ quy tắc trong docstring.
- **Xong khi:**
  - [ ] `eval/cases/planning.jsonl` có ít nhất 6 yêu cầu có nhãn (thêm 5).
  - [ ] Với mỗi yêu cầu: các khóa trong `hard` khớp nhãn; yêu cầu mơ hồ có ít nhất một `clarification`.
  - [ ] Pull request ghi rõ đã dùng Pipelex hay OpenAI, và lý do.

### T11 · Client Jinko · P1
- **Tệp:** `bureau/planner/jinko.py`, `data/wei/jinko_cache/`
- **Việc:** gọi `POST /v1/ground_search` và `POST /v1/hotel_search` trên sandbox; chuẩn hóa kết quả theo docstring; `live` lưu phản hồi, `replay` chỉ đọc bộ nhớ đệm.
- **Xong khi:**
  - [ ] Có ít nhất một phản hồi thật cho mỗi endpoint được lưu trong `data/wei/jinko_cache/`.
  - [ ] Test ở chế độ `replay` chạy không cần mạng và trả về danh sách đã chuẩn hóa (giá bằng cent).
  - [ ] Các chi tiết đánh dấu "verify" trong docstring đã được xác nhận hoặc sửa.

### T12 · Ghép phương án · P1
- **Tệp:** `bureau/planner/compose.py`, `tests/test_planner.py`
- **Xong khi:**
  - [ ] Test: giá mỗi người = giá đi lại/người + giá chỗ ở/đêm × số đêm ÷ số người, tính bằng số nguyên.
  - [ ] Test: phương án rẻ nhất luôn có trong kết quả, kể cả khi vượt `limit`.
  - [ ] Test: chỗ ở không đủ sức chứa bị bỏ.

### T13 · Giải thích đánh đổi · P1
- **Tệp:** `bureau/planner/explain.py`
- **Xong khi:**
  - [ ] Giải thích nhắc tên phương án đứng đầu và, với mỗi phương án bị loại, tên ràng buộc bị vi phạm (kiểm bằng test: chuỗi có chứa các tên này).
  - [ ] Test: thứ hạng và kết quả kiểm tra trước và sau khi gọi `explain` giống hệt nhau.

### T14 · Nối planner · P1
- **Tệp:** `bureau/planner/planner.py`, `api/main.py`
- **Xong khi:**
  - [ ] `search_options` dùng `jinko` + `compose` (chế độ `replay`); `TravelRequest` được tạo từ `state.travel`, không đọc thẳng `event.json`.
  - [ ] Test: ngân sách 120€ → `SELECT_TRAVEL_PLAN` có ít nhất một phương án hợp lệ; 90€ → `ESCALATE` có `suggestions`.
  - [ ] `POST /api/events/wei/plan` với `{"overrides": {"max_cost_per_person_cents": 9000}}` trả `ESCALATE`.

### T15 · Giao diện chuyến đi · P1
- **Tệp:** `web/*`
- **Xong khi (checklist):**
  - [ ] Hiện ràng buộc cứng / mềm và ràng buộc cần người tổ chức xác nhận.
  - [ ] Bảng so sánh: phương án bị loại có lý do tô đỏ.
  - [ ] Nút chọn phương án; sau khi chọn, các vấn đề phụ thuộc chuyển khỏi trạng thái "chờ".
  - [ ] Thử ngân sách 90€ hiện chẩn đoán "không có phương án hợp lệ".
  - [ ] Có ảnh chụp màn hình trong pull request.

### T16 · Dữ liệu chuyến đi thật · P1
- **Tệp:** `data/wei/*`, `data/README.md`
- **Xong khi:**
  - [ ] `event.json` dùng điểm đến, số người, ngân sách, yêu cầu của một chuyến đi có thật (không có dữ liệu cá nhân).
  - [ ] `python -m bureau plan wei` chạy được.
  - [ ] `data/README.md` ghi nguồn (hội nào, chuyến nào).

### T17 · Tài liệu và video · P2
- **Xong khi:**
  - [ ] README gốc: trạng thái cập nhật, kết quả đánh giá, mục giới hạn, link video.
  - [ ] Có sơ đồ kiến trúc trong README.
  - [ ] Video ≤ 2 phút, theo kịch bản trong `docs/product-proposal.md`, xong trước **20:00 Chủ Nhật 27/09**.

### T18 · Thử với người tổ chức thật · P2
- **Xong khi:**
  - [ ] Một thành viên ban điều hành của một hội thật đã dùng thử (ghi tên hội nếu họ đồng ý).
  - [ ] Ghi lại: số đề xuất đã xem, số duyệt nguyên văn, số lần sửa, thời gian, một câu nhận xét nguyên văn.
  - [ ] Kết quả có trong README, tách riêng với chỉ số offline.

### T19 · Trước khi nộp · P2
- **Xong khi:**
  - [ ] `git log -p | grep -i -E "sk-|jnk_|api_key="` không ra khóa thật.
  - [ ] Làm theo README trên một máy khác (clone mới) chạy được.
  - [ ] Repo đã chuyển sang công khai.
  - [ ] Form nộp bài đã gửi trước **22:00 Chủ Nhật 27/09**.

### T20 · Triển khai demo miễn phí · P2
- **Tệp:** `Dockerfile`, `README.md`
- **Việc:** một container chạy FastAPI (phục vụ cả API và web); triển khai lên Hugging Face Spaces (Docker, gói CPU miễn phí; kiểm tra điều khoản hiện tại trước). Khóa API đặt trong Secrets của Space. Bản công khai chạy **chế độ demo**: dùng đề xuất đã lưu, chỉ gọi OpenAI khi có mật khẩu demo.
- **Xong khi:**
  - [ ] Link công khai mở được giao diện và duyệt được một đề xuất.
  - [ ] Không có khóa API trong image hay repo.
  - [ ] Không có mật khẩu demo thì không có lệnh gọi OpenAI nào (kiểm bằng log).
  - [ ] README có link.
