# Kiến trúc Bureau Agent
*Tài liệu kiến trúc cho nhóm dự thi X-IA Hackathon #1 · Phiên bản 1.1 · 25/09/2026*
*Tài liệu liên quan: `DE_XUAT_BUREAU_AGENT_V3.md` (sản phẩm), `README.md` (cách chạy).*

Tài liệu này mô tả hệ thống sẽ được xây dựng: các thành phần, luồng dữ liệu, giao diện giữa các phần, và cách nhóm làm việc chung trên một repo. Mục 10 liệt kê các **quyết định cần duyệt** trước khi dựng framework.

**Ký hiệu:** **[đã có]** = đã có trong bộ khung hiện tại, có kiểm thử. **[cần làm]** = chưa làm. **[VERIFY]** = chi tiết của bên thứ ba cần kiểm tra lại với tài liệu hoặc API thật.

### Thay đổi so với đề xuất v3 (sau phản biện)
| Vấn đề | Sửa |
|---|---|
| `TravelRequest` thiếu điểm đến | Thêm `destination`. **Điểm đến do người tổ chức cho**; planner không tự chọn nơi đi |
| LLM ghép phương án trọn gói dễ cộng sai giá, ghép sai ngày | **LLM hiểu yêu cầu → code ghép và kiểm tra → LLM giải thích** |
| Tiền dùng số thực | `amount_cents: int` + `currency`; ràng buộc giá dùng `max_cost_per_person_cents` |
| Quy chế là một chuỗi dài, khó trích dẫn | `Rule(id, title, text, source)`; decision trace trích được `§3` |
| Bằng chứng là chuỗi tự do | `Evidence(source_type, source_id, description)` |
| Ngày giờ không có múi giờ | Mọi `datetime` phải có múi giờ; bộ nạp dữ liệu từ chối ngày giờ thiếu múi giờ |
| Tên `duplicate_membership` dễ nhầm với phí hội viên | Đổi thành `multiple_group_membership` |
| Phát hiện lại có thể tạo vấn đề trùng | ID vấn đề là **dấu vân tay xác định** (loại + đối tượng); có kiểm thử |
| `plan_trip` trả về danh sách nhưng chỉ có một hành động | Trả về **một** `ProposedAction` |
| Không biết vấn đề được giải quyết bằng hành động nào | Thêm `Issue.resolved_by_action_id` |
| Mọi hành động đều có "độ tin cậy" | `confidence` chỉ dùng cho suy luận (danh tính, ý định); sự kiện xác định chỉ có đạt/không đạt |
| Ràng buộc "phòng không bậc thang" mà API không xác minh được | Jinko chỉ có mô tả tiện nghi dạng chữ, không có trường có cấu trúc. Ràng buộc này là **"người tổ chức xác nhận"** (`Check.verified = False`): hiển thị, nhưng không dùng để loại phương án |

---

## Mục lục
1. Mục tiêu và nguyên tắc
2. Tổng quan hệ thống
3. Mô hình dữ liệu
4. Vòng đời của một vấn đề
5. Thành phần lõi
6. Planner chuyến đi
7. API và giao diện web
8. Đánh giá
9. Cấu trúc repo và quy trình làm việc chung
10. Quyết định cần duyệt
11. Phân công và mốc thời gian
12. Rủi ro kỹ thuật

---

## 1. Mục tiêu và nguyên tắc

**Mục tiêu:** một agent duy nhất giữ cho trạng thái của một sự kiện nhất quán. Agent phát hiện vấn đề, điều tra bằng công cụ, đề xuất hành động, và người tổ chức duyệt. Demo trên hai sự kiện: hackathon (P0) và weekend d'intégration (P1).

**Nguyên tắc kiến trúc:**
| Nguyên tắc | Hệ quả trong thiết kế |
|---|---|
| LLM cho chỗ mơ hồ | LLM chỉ đọc tin nhắn, tách ràng buộc, chọn công cụ, soạn nội dung, giải thích |
| Code cho quy tắc bất biến | Điều kiện dự thi, sĩ số nhóm, mỗi người một nhóm, ngân sách, giờ đến, điểm danh tính đều là hàm Python thuần, có kiểm thử |
| Con người chịu trách nhiệm | Agent **không bao giờ thực thi**. Nó chỉ tạo `ProposedAction`. Thực thi nằm ở một module riêng (`executor`), chỉ chạy khi có duyệt |
| Một agent điều phối | Không làm đa agent. Mọi khả năng là công cụ của một vòng lặp |
| Chạy được không cần mạng | Phát hiện vấn đề, planner, kiểm thử chạy được mà không cần API. Jinko có chế độ phát lại kết quả đã lưu |
| Trạng thái tính lại được | Vấn đề được phát hiện lại từ dữ liệu sau mỗi hành động, với ID ổn định, nên không có trạng thái "lệch" giữa dữ liệu và danh sách vấn đề |

---

## 2. Tổng quan hệ thống

```
                    ┌─────────────────────────── Web UI (hàng chờ duyệt, decision trace) ───┐
                    │                                                                        │
                    ▼                                                                        │
             ┌─────────────┐   HTTP/JSON                                                     │
             │  API        │◄──────────────────────────────────────────────────────────────┘
             │  (FastAPI)  │
             └──────┬──────┘
                    │
   ┌────────────────┼──────────────────────────────────────────────┐
   │                ▼                                              │
   │  Store ◄──► EventState ──► detect_issues() ──► Issue[]        │   Lõi (bureau/)
   │  (JSON)          ▲                               │            │
   │                  │                               ▼            │
   │            executor.apply()            agent.resolve_issue()  │──► OpenAI
   │            (chỉ khi được duyệt)           │  gọi công cụ      │
   │                  ▲                       ▼                    │
   │                  │                 ProposedAction ────────────┼──► hàng chờ duyệt
   │                  │                       ▲                    │
   │                  │                       │                    │
   │                  │               planner.plan_trip()          │──► Jinko (live / replay)
   │                  │               (P1: chuyến đi)              │
   └──────────────────┴──────────────────────────────────────────────┘
```

| Thành phần | Vai trò | Trạng thái |
|---|---|---|
| `models` | Schema dữ liệu | [đã có] |
| `loader` | Nạp dữ liệu mẫu vào `EventState` | [đã có] |
| `detect` | Phát hiện vấn đề bằng code | [đã có] |
| `tools/*` | Công cụ cố định: quy chế, điều kiện, danh tính, nhóm | [đã có] |
| `agent` | Vòng lặp OpenAI, kết thúc bằng `propose_action` | [đã có, chưa chạy với API] |
| `planner/*` | Tách ràng buộc, tìm kiếm, cổng ràng buộc, xếp hạng, chẩn đoán | Cổng/xếp hạng/chẩn đoán [đã có]; tách ràng buộc và Jinko [cần làm] |
| `store` | Lưu và đọc trạng thái, hành động, hộp thư đã gửi | [cần làm] |
| `executor` | Áp hành động đã duyệt lên trạng thái | [cần làm] |
| `api` | HTTP API cho giao diện | [cần làm] |
| `web` | Giao diện duyệt | [cần làm] |
| `eval` | Bộ đánh giá | [cần làm] |

---

## 3. Mô hình dữ liệu
Schema nằm trong `bureau/models.py` [đã có]. Tóm tắt:

| Đối tượng | Trường chính | Ghi chú |
|---|---|---|
| `EventState` | `id, name, rules, deadlines, settings, participants, payments, groups, messages, logistics, issues, actions` | Một sự kiện tại một thời điểm |
| `Participant` | `id, name, emails[], registered_at, skills[], needs[], looking_for_group` | `needs` ví dụ `step_free` |
| `Payment` | `id, payer_name, amount_cents, currency, paid_at, payer_email?, reference?, participant_id?` | Tiền là số nguyên (cent); `participant_id = None` là chưa gắn với ai |
| `Rule` | `id, title, text, source` | Một mục quy chế, ví dụ `§3` |
| `Evidence` | `source_type, source_id, description` | Nguồn dùng để đề xuất (bản ghi, điều khoản, kết quả tìm kiếm) |
| `Group` | `id, kind(team/room), name, members[], capacity_min, capacity_max, declared_at?` | Đội (hackathon) hoặc phòng (WEI) |
| `Message` | `id, channel, sender, text, received_at` | Email, Discord, biểu mẫu |
| `Issue` | `id, kind, blocking, title, subject_ids[], details, status, depends_on[], resolved_by_action_id?` | ID là dấu vân tay xác định, ví dụ `multiple_group_membership:p02` |
| `Check` | `name, passed, detail, verified` | `verified = False` khi nguồn dữ liệu không xác minh được; người tổ chức phải kiểm tra |
| `ProposedAction` | `id, event_id, issue_id, action_type, title, description, evidence[Evidence], checks[Check], confidence?, requires_approval, payload` | `confidence` chỉ cho suy luận; luôn `requires_approval = True` với hành động có hệ quả |

Mọi `datetime` có múi giờ (dữ liệu mẫu dùng `+02:00`, giờ Paris đến 25/10/2026).

**Loại hành động** (`action_type`) và tác động khi được duyệt:
| `action_type` | `payload` tối thiểu | Tác động khi thực thi |
|---|---|---|
| `SEND_MESSAGE` | `to[]`, `text` | Ghi vào hộp thư đã gửi (giả lập) |
| `LINK_PAYMENT` | `payment_id`, `participant_id`, `to?`, `message?` | Kiểm người tồn tại; từ chối đổi chủ khoản đã gắn bằng ID hoặc khớp email khi chưa có ID. Gắn thanh toán; nếu có `message` thì bắt buộc có `to`, ghi một tin vào outbox (`edited_description` thay nội dung nếu có) |
| `MOVE_MEMBER` | `participant_id`, `from_group`, `to_group?`, `message?` | Sửa thành viên nhóm |
| `UPDATE_GROUPS` | `groups[]` | Thay danh sách nhóm/phòng |
| `SELECT_TRAVEL_PLAN` | `option_id` (do người chọn), `options[]` | Chỉ chấp nhận phương án có `valid = true`; ghi `logistics`, mở khóa vấn đề phụ thuộc |
| `ESCALATE` | `note?` | Đánh dấu đã chuyển người; vấn đề đóng khi người đánh dấu đã xử lý |

---

## 4. Vòng đời của một vấn đề

```
            detect_issues()                agent / planner             người duyệt           executor
 dữ liệu ─────────────────► open ──────────────────────► proposed ────────────────► approved ───────► resolved
                              │                              │                         │
                              │ (phụ thuộc chưa xong)          └──► needs_human ───────┤
                              ▼                                                        └──► dismissed
                           waiting
```
1. **Phát hiện:** `detect_issues(state)` chạy lại toàn bộ sau mỗi thay đổi. Vấn đề có ID ổn định nên trạng thái (đã duyệt, đã bỏ qua) được giữ qua các lần chạy.
2. **Chờ:** vấn đề có `depends_on` chưa xong thì không đưa cho agent.
3. **Đề xuất:** agent (hoặc planner) tạo đúng một `ProposedAction` cho mỗi vấn đề.
4. **Duyệt:** người duyệt, sửa nội dung, hoặc bỏ qua.
5. **Thực thi:** `executor.apply(state, action)` thay đổi dữ liệu. Sau đó phát hiện lại, nên vấn đề đã giải quyết biến mất và vấn đề phụ thuộc được mở khóa.

---

## 5. Thành phần lõi

### 5.1. Phát hiện vấn đề (`detect.py`) [đã có]
| Loại | Chặn | Nguồn |
|---|---|---|
| `unmatched_payment` | Có nếu có ứng viên khớp; không nếu không ai khớp | `check_eligibility` + `match_person` |
| `unpaid_membership` / `unpaid_participation` | Có | Đối chiếu đăng ký × thanh toán, loại người đang chờ xác nhận |
| `multiple_group_membership`, `group_over_capacity` | Có | `check_groups` |
| `no_logistics_plan`, `rooms_unassigned` | Có | Cài đặt sự kiện (WEI) |
| `solo_participants` | Không | Người muốn có đội |
| `unprocessed_message` | Không | Mỗi tin nhắn mới; agent tự phân loại |

### 5.2. Công cụ cố định (`tools/`) [đã có]
| Công cụ | Đầu vào → đầu ra | Ghi chú |
|---|---|---|
| `search_rules` | truy vấn → các mục quy chế liên quan | Tìm theo từ khóa trên từng mục `##` |
| `check_eligibility` | trạng thái → `paid[]`, `unpaid[]`, `unmatched_payments[]` | Chỉ khớp chính xác theo email hoặc liên kết có sẵn |
| `match_person` | `payment_id` → ứng viên kèm điểm, mức và tín hiệu | Điểm từ họ, tên, phần trước @, thời điểm. ≥ 0,98 đề xuất gắn; 0,70–0,98 hỏi người; < 0,70 khác người |
| `check_groups` | trạng thái → vi phạm | Trùng thành viên, sai sĩ số |
| `propose_groups` | danh sách người, cỡ nhóm → các nhóm | Tham lam, trải đều kỹ năng |

### 5.3. Agent (`agent.py`) [đã có, chưa chạy với API]
- **Mô hình:** OpenAI Chat Completions với gọi công cụ. Tên model lấy từ `OPENAI_MODEL` trong `.env`; mặc định `gpt-4.1`, model đã được đánh giá (T08, `eval/README.md`).
- **Vòng lặp:** tối đa 8 bước. Mỗi bước: gọi mô hình → chạy công cụ được yêu cầu → trả kết quả. Kết thúc khi mô hình gọi `propose_action`.
- **System prompt** gồm các quy tắc: phải tra quy chế trước khi trả lời; không bịa quy tắc (không có thì `ESCALATE`); không tự gộp danh tính; dữ liệu cá nhân, tiền, ngoại lệ luôn chuyển người; tin nhắn soạn theo ngôn ngữ người gửi, kèm dòng minh bạch AI.
- **Công cụ đưa cho mô hình:** `get_event_summary`, `get_participant`, `search_rules`, `check_eligibility`, `match_person`, `check_groups`, `propose_groups`, `propose_action`.
- **Không có** công cụ nào thực thi. `propose_action` chỉ ghi đề xuất.
- **Tính agentic của P0 nằm ở đây.** Tin nhắn đến chỉ được gắn nhãn `unprocessed_message`; **không có luật cứng** kiểu "tin có chữ 'payé' thì gọi `match_person`". Agent tự đọc tin, tự chọn công cụ (tìm người gửi, xem thanh toán chưa gắn, chấm điểm danh tính), tự quyết định đề xuất hay hỏi người. Nếu P1 bị cắt, phần này vẫn phải chứng minh được đây là agent, không phải một workflow cố định.

### 5.4. Lưu trữ (`store.py`) [cần làm]
- Không dùng cơ sở dữ liệu. Mỗi sự kiện có `data/<event>/` (dữ liệu gốc, chỉ đọc) và `runtime/<event>/` (trạng thái sau khi thay đổi, hành động, hộp thư đã gửi, nhật ký).
- Lệnh `reset` xóa `runtime/<event>/` để demo lại từ đầu.
- `runtime/` nằm trong `.gitignore`.

### 5.5. Thực thi (`executor.py`) [đã có]
- `apply(state, action, edited_description=None, option_id=None) -> EventState`: áp tác động theo bảng ở mục 3 trên bản sao, ghi nhật ký, trả trạng thái mới.
- Kiểm người nhận thanh toán tồn tại (`ValueError` nếu không); chặn đổi chủ thanh toán và chọn phương án không hợp lệ (`InvariantViolation`). ID chủ khoản có ưu tiên; khi chưa có ID, đối chiếu email không phân biệt hoa thường.
- **Kiểm tra lại quy tắc nhóm trong phạm vi bị tác động.** Nếu một hành động làm sai quy tắc (ví dụ đội thành 5 người), từ chối, giữ nguyên trạng thái đầu vào và không ghi outbox/nhật ký.

---

## 6. Planner chuyến đi (P1)

### 6.1. Luồng xử lý
Phân công: **LLM hiểu yêu cầu → code ghép và kiểm tra → LLM giải thích.** Điểm đến do người tổ chức cho.
```
 yêu cầu bằng lời (có điểm đến)
      │
      ▼
 extract_constraints()  ── LLM, đầu ra có cấu trúc ──► Constraints {hard, soft, organizer_verified, clarifications}
      │
      ├── clarifications không rỗng? ──► ProposedAction ESCALATE (câu hỏi cho người tổ chức), dừng
      ▼
 search_options()  ── Jinko ground_search + hotel_search (sandbox) ──► kết quả thô
      │                (chế độ replay: đọc kết quả đã lưu)
      ▼
 compose_packages()  ── CODE: ghép đi lại × chỗ ở thành phương án trọn gói, tính giá/người (cent)
      │
      ▼
 check_constraints()  ── CODE: mỗi ràng buộc cứng → Check(passed, detail, verified)  [đã có]
      │                  chỉ Check có verified = True mới được loại phương án
      │
      ├── không phương án nào hợp lệ ──► diagnose() ──► ESCALATE kèm gợi ý nới        [đã có]
      ▼
 rank()  ── xếp theo ưu tiên mềm hiện tại, rồi theo giá                                [đã có]
      │
      ▼
 explain()  ── LLM viết giải thích đánh đổi (không đổi thứ hạng)
      │
      ▼
 ProposedAction SELECT_TRAVEL_PLAN (mọi phương án kèm Check trong payload)             [đã có]
```

### 6.2. Hợp đồng (`planner/interface.py`) [đã có]
```python
TravelRequest(event_id, text, participants, origin, destination, depart_after, return_by=None)
Constraints(hard: dict, soft: list[str], organizer_verified: list[str], clarifications: list[str])
TravelOption(id, transport: dict, lodging: dict, cost_per_person_cents: int, source: str)

extract_constraints(req) -> Constraints
plan_trip(req, constraints) -> ProposedAction      # SELECT_TRAVEL_PLAN hoặc ESCALATE
```
**Khóa ràng buộc cứng được hỗ trợ:** `participants`, `max_cost_per_person_cents`, `arrive_before` (HH:MM), `no_overnight`, `step_free_rooms` (luôn thuộc `organizer_verified`).

**Hai loại ràng buộc cứng:**
| Loại | Ví dụ | Dùng để loại phương án? |
|---|---|---|
| API xác minh được | Giá, giờ đến, đi qua đêm, số phòng khi tìm | Có |
| Người tổ chức xác nhận | Phòng không bậc thang (Jinko chỉ có mô tả tiện nghi dạng chữ) | Không; hiện thành việc cần xác nhận | Thêm khóa mới = thêm một nhánh trong `check_option` và một bài kiểm thử.
**Khóa ưu tiên mềm:** `fewer_changes`, `near_station`, `early_return`, `lower_cost`.

### 6.3. Tách ràng buộc bằng LLM [cần làm]
- Dùng đầu ra có cấu trúc (JSON schema khớp `Constraints`).
- Quy tắc cho mô hình: chỉ tách điều người dùng nói; chỗ mơ hồ ghi vào `clarifications` thay vì tự đoán (ví dụ ngân sách có gồm ăn uống không).
- **Được đánh giá riêng** trên ~10 yêu cầu có đáp án (mục 8), vì tách sai thì cổng ràng buộc cũng vô dụng.

### 6.4. Kết nối Jinko [cần làm]
| Mục | Chi tiết |
|---|---|
| Môi trường | Sandbox: `https://api.sandbox.gojinko.com`, khóa sandbox riêng [VERIFY] |
| Xác thực | `Authorization: Bearer jnk_...` |
| Đi lại | `POST /v1/ground_search` (tàu, xe khách, phà). Mã ga/thành phố dạng ISO quốc gia + thành phố, ví dụ `GBLON`. Kết quả có `departure_time`, `arrival_time`, `duration_minutes` |
| Chỗ ở | `POST /v1/hotel_search`: số người lớn, số phòng, ngày; có bộ lọc `facility_ids`. Giá khách sạn là đơn vị chính (euro), cần đổi sang cent. `hotel_details` có `facilities` (chuỗi) và `max_occupancy` theo loại phòng |
| Khả năng tiếp cận | Chỉ có trong `facilities` dạng chữ, không có trường đúng/sai. Vì vậy chỉ là gợi ý, cần người xác nhận |
| Giá vé máy bay | Đơn vị nhỏ nhất (chia cho `decimal_places`); không dùng trong P1 |
| Hạn token | Kết quả có thể hết hạn sau khoảng 30 phút; chỉ dùng để so sánh, không đặt |
| Chế độ | `JINKO_MODE=live` gọi thật và lưu phản hồi vào `data/wei/jinko_cache/`; `replay` chỉ đọc bộ nhớ đệm. **Demo dùng `replay` với dữ liệu thật đã lưu** |
| Đặt vé | Không làm. P2 mới thử đặt trên sandbox |

### 6.5. Ghép phương án (`compose_packages`) [cần làm]
- Lấy tối đa 5 chuyến đi lại tốt nhất và 5 chỗ ở đủ sức chứa, ghép chéo, bỏ tổ hợp rõ ràng vô lý (ví dụ chỗ ở ở thành phố khác ga đến).
- **Hoàn toàn bằng code, không dùng LLM.** Tính `cost_per_person_cents = giá đi lại/người + giá chỗ ở/đêm × số đêm ÷ số người`, mọi phép tính bằng số nguyên.
- Giữ lại **cả phương án rẻ nhất vi phạm ràng buộc** để bảng so sánh cho thấy vì sao bị loại.

---

## 7. API và giao diện web

### 7.1. Endpoint [cần làm]
| Phương thức | Đường dẫn | Mô tả |
|---|---|---|
| GET | `/api/events` | Danh sách sự kiện kèm số vấn đề chặn / không chặn / chờ duyệt / đã giải quyết |
| GET | `/api/events/{event_id}` | Trạng thái tóm tắt, danh sách vấn đề, hành động |
| POST | `/api/events/{event_id}/run` | Phát hiện lại + chạy agent cho vấn đề mở chưa có đề xuất |
| POST | `/api/events/{event_id}/plan` | Chạy planner với `{text?, overrides?}` (ví dụ đổi ngân sách) |
| GET | `/api/actions/{action_id}` | Chi tiết hành động (decision trace) |
| POST | `/api/actions/{action_id}/approve` | `{edited_description?, option_id?}` → thực thi → trả trạng thái mới |
| POST | `/api/actions/{action_id}/dismiss` | Bỏ qua |
| GET | `/api/events/{event_id}/outbox` | Tin nhắn "đã gửi" (giả lập) |
| POST | `/api/events/{event_id}/reset` | Xóa `runtime/`, về dữ liệu gốc |

Định dạng JSON của `Issue` và `ProposedAction` giống hệt dataclass trong `models.py` (`dataclasses.asdict`). Giao diện chỉ phụ thuộc vào định dạng này.

### 7.2. Giao diện web [cần làm]
- **Bố cục** theo bản mô phỏng (https://claude.ai/artifact/JCKLf1tuJLtPUPsfXK1ox4): thẻ sự kiện → danh sách vấn đề (chặn trước) → chi tiết (đầu vào, decision trace, phép kiểm tra, hành động đề xuất có thể sửa, nút duyệt) → bảng so sánh phương án cho chuyến đi.
- Trang tĩnh do FastAPI phục vụ, gọi API bằng `fetch`. Không cần bước build (xem quyết định D2).
- Không có đăng nhập trong bản hackathon.

---

## 8. Đánh giá [cần làm]
```
eval/
  messages.jsonl        ~50 tin nhắn có nhãn: loại vấn đề, công cụ cần gọi, điều khoản đúng, có cần chuyển người
  planning.jsonl    ~10 yêu cầu chuyến đi có nhãn: ràng buộc cứng/mềm đúng, có khả thi không
  run_eval.py           chạy agent/planner, in bảng chỉ số, lưu kết quả vào eval/results/
```
**Đánh giá offline** (có đáp án do nhóm gán; chạy tự động):
| Chỉ số | Mục tiêu |
|---|---|
| Hiểu đúng loại yêu cầu | Báo số thật |
| Gọi đúng công cụ cần thiết | Báo số thật |
| Trích đúng điều khoản | Báo số thật |
| Chuyển người đúng lúc / không cần thiết | Báo cả hai |
| Hành động vi phạm quy tắc bất biến | **0** |
| Tách ràng buộc đúng | So từng khóa với đáp án |
| Phát hiện không khả thi | Báo số thật |

**Thử với người dùng thật** (chỉ báo khi có người tổ chức thật dùng thử, không phải chính nhóm):
| Chỉ số | Cách đo |
|---|---|
| Đề xuất được duyệt nguyên văn | % trên các đề xuất người đó xem |
| Số lần sửa | Đếm |
| Thời gian tiết kiệm | Làm tay so với duyệt |
| Nhận xét | Trích nguyên văn |

Kết quả đưa vào README, kể cả trường hợp sai. Không gọi chỉ số offline là "tỷ lệ người dùng duyệt".

---

## 9. Cấu trúc repo và quy trình làm việc chung

### 9.1. Cấu trúc
```
bureau-agent/
  README.md          trang điều hướng
  TASKS.md           danh sách task để phân công
  CONTRIBUTING.md    quy trình nhánh, pull request, quy tắc
  bureau/
    core/            models, loader, detect, store (T02), executor (T03)
    tools/           rules, eligibility, identity, groups
    agent/           prompts, tool_specs, loop
    planner/         interface, planner, constraints, extract (T10), jinko (T11), compose (T12), explain (T13)
    config.py  cli.py
  api/               FastAPI (main.py)
  web/               index.html, app.js, style.css, reference/mockup.html
  data/              hackathon/, wei/  (chỉ đọc)
  runtime/           trạng thái khi chạy (không commit)
  eval/              cases/, run_eval.py
  tests/             test_core, test_tools, test_planner, test_pending
  docs/              ARCHITECTURE.md, product-proposal.md
  .github/           workflows/tests.yml, pull_request_template.md
```
Mỗi thư mục có một `README.md` ngắn. Chỗ chưa cài đặt dùng `raise NotImplementedError("TASK Txx")`.

### 9.2. Quy tắc làm việc
| Quy tắc | Chi tiết |
|---|---|
| Nhánh | `main` luôn chạy được. Mỗi người làm trên nhánh riêng: `core/...`, `planner/...`, `web/...`, `eval/...` |
| Gộp code | Pull request vào `main`; kiểm thử phải qua; một người khác xem nhanh trước khi gộp |
| Ranh giới | Mỗi module có một người phụ trách (mục 11). Đổi `models.py` hoặc `planner/interface.py` phải báo cả nhóm trước, vì đó là hợp đồng chung |
| Bí mật | Không commit `.env`, khóa API hay dữ liệu cá nhân thật. `.env.example` liệt kê tên biến |
| Kiểm thử | Mọi quy tắc bất biến mới phải có một bài kiểm thử trong `tests/`. GitHub Actions chạy `python -m unittest` trên mỗi pull request |
| Việc cần làm | GitHub Issues với nhãn `P0`, `P1`, `P2` và người phụ trách |
| Ngôn ngữ | Code, commit, README bằng tiếng Anh (giám khảo quốc tế); tài liệu nội bộ có thể bằng tiếng Việt |
| Thời điểm | Toàn bộ code được viết từ 25/09 09:00, trong thời gian thi; ghi rõ trong README để tránh bị coi là dự án có sẵn |

---

## 10. Quyết định cần duyệt

| # | Quyết định | Đề xuất | Phương án khác | Lý do đề xuất |
|---|---|---|---|---|
| D1 | Backend | **Python + FastAPI** | Flask | Lõi đã viết bằng Python; FastAPI tự sinh tài liệu API, dễ cho người làm giao diện |
| D2 | Frontend | **HTML + JavaScript thuần, dựa trên bản mô phỏng**, do FastAPI phục vụ | React + Vite | Không cần bước build, tái dùng thẳng bản mô phỏng, ít thứ hỏng. Chọn React nếu người làm giao diện quen hơn hẳn |
| D3 | Lưu trữ | **Tệp JSON** (`data/` chỉ đọc, `runtime/` khi chạy) | SQLite | Dữ liệu nhỏ, dễ xem, dễ reset khi demo |
| D4 | Gọi LLM | **OpenAI Chat Completions + gọi công cụ**, model đặt trong `.env` | OpenAI Responses API; Dust | Đã viết và kiểm tra công cụ; ổn định, nhiều tài liệu |
| D5 | Pipelex, Dust, Gradium | **Pipelex cho hai bước LLM của planner (tách ràng buộc, giải thích), dạng thử có giới hạn ~1,5 giờ (T10, T13)**; nếu không kịp thì dùng OpenAI structured output. Không dùng Dust, Gradium | Không dùng sponsor nào ngoài OpenAI, Jinko | Pipelex được làm cho các bước LLM có đầu ra có cấu trúc, lặp lại được, đúng hai bước này. Phần kiểm tra ràng buộc vẫn là Python thuần. Hai bước nằm sau một giao diện cố định nên đổi cách làm không ảnh hưởng phần khác |
| D6 | Jinko | **Sandbox; demo ở chế độ replay với kết quả thật đã lưu** | Gọi trực tiếp khi demo | Demo không phụ thuộc mạng và credit |
| D7 | Repo GitHub | **Riêng tư khi làm, công khai trước khi nộp** | Công khai từ đầu | Tránh lộ bí mật do sơ suất; bài nộp cần link xem được |
| D8 | Tên repo | `bureau-agent` | | |
| D9 | Phiên bản Python | **3.11** | 3.12 | Có sẵn trên máy của người code chính |

---

## 11. Phân công và mốc thời gian
Danh sách task, phụ thuộc và tiêu chí hoàn thành nằm trong [`TASKS.md`](../TASKS.md). Trưởng nhóm phân công người làm trong tệp đó.

| Mốc | Việc | Tiêu chí xong |
|---|---|---|
| Thứ Sáu 25/09, tối | Duyệt kiến trúc; tạo repo; CI; mỗi người clone và chạy được kiểm thử | `python -m unittest discover -s tests -t .` qua trên máy mọi người |
| Thứ Bảy 26/09, 12:00 | **P0 chạy trọn luồng**: agent thật + store + executor + API + giao diện cho hackathon | Duyệt một đề xuất trên giao diện làm vấn đề biến mất |
| Thứ Bảy 26/09, 18:00 | P1: planner với Jinko (replay), bảng so sánh trên giao diện | Chạy được cả hai ngân sách 120€ và 90€ |
| Thứ Bảy 26/09, 23:00 | Bộ đánh giá chạy được; **ngừng thêm tính năng** | Có bảng chỉ số |
| Chủ Nhật 27/09 | Sửa lỗi, README, video; nộp trước 22:00 | Chạy README trên máy khác |

**Mốc cắt:** nếu 12:00 thứ Bảy P0 chưa chạy trọn luồng, tạm dừng P1.

---

## 12. Rủi ro kỹ thuật
| Rủi ro | Cách giảm |
|---|---|
| Model được cấp không hỗ trợ gọi công cụ tốt | Thử ngay khi có khóa; giữ prompt ngắn, công cụ ít; có thể đổi model trong `.env` |
| Agent lặp không kết thúc | Giới hạn 8 bước; lỗi rõ ràng; kiểm thử với vài vấn đề mẫu |
| Agent đề xuất hành động phá quy tắc | `executor` kiểm tra lại quy tắc bất biến trước khi ghi |
| Lõi và planner ghép không khớp | Hợp đồng chung đã có; thay đổi hợp đồng phải báo cả nhóm |
| Giao diện chờ API | Làm trước với tệp JSON mẫu đúng định dạng mục 7.1 |
| Jinko lỗi, chậm, thiếu kết quả nhóm lớn | Chế độ replay; ghép nhiều phòng; không đủ thì chuyển người |
| Xung đột khi nhiều người sửa cùng tệp | Ranh giới module theo người; pull request nhỏ, gộp thường xuyên |
| Lộ khóa API | `.env` trong `.gitignore`; repo riêng tư đến trước khi nộp; kiểm tra lịch sử commit trước khi công khai |
