# Đề xuất dự án: Bureau Agent (phiên bản 3)
### Agent vận hành sự kiện cho các hội tình nguyện
*Đề xuất dự thi X-IA Hackathon #1 "Rise of Agents X" · Phiên bản 3 · 25/09/2026*
*Thay thế `DE_XUAT_BUREAU_AGENT_V2.md`. Đây là bản dùng để bắt đầu code.*

**Luận điểm (một câu):**
> Bureau Agent giữ cho một sự kiện luôn nhất quán về mặt vận hành: nó phát hiện điều gì cần xử lý, điều tra trên dữ liệu nội bộ và dữ liệu bên ngoài, đề xuất hành động hợp lệ, và để người tổ chức duyệt những gì có hệ quả.

**Câu pitch:** *Bureau Agent biến người tổ chức tình nguyện từ người làm thành người giám sát.*

**Nguyên tắc thiết kế:** *LLM xử lý chỗ mơ hồ. Code giữ các quy tắc bất biến. Con người chịu trách nhiệm.*

**Nguồn gốc ý tưởng:** phần lõi vận hành do Khuê đề xuất; kịch bản chuyến đi (weekend d'intégration, voyage de section) do Huy đề xuất; cơ chế lập kế hoạch nhiều ràng buộc lấy từ ý tưởng *Polaris* của Bảo. Phiên bản 3 tiếp thu góp ý phản biện độc lập về khái niệm trung tâm, thuật ngữ và phạm vi.

**Ký hiệu:** **[nguồn]** = có nguồn công khai (cuối tài liệu). **[ước]** = nhận định của nhóm, chưa kiểm chứng.

---

## Có gì mới so với phiên bản 2
| Chủ đề | Phiên bản 2 | Phiên bản 3 |
|---|---|---|
| Khái niệm trung tâm | Danh sách tính năng (trả lời email, kiểm tra phí, ghép đội, lên kế hoạch chuyến đi) | **Trạng thái sự kiện → vấn đề → hành động đề xuất → duyệt → trạng thái mới**. Mọi tính năng chỉ là công cụ của một vòng lặp |
| Màn hình đầu tiên | Hộp thư và hàng chờ duyệt | **Tình trạng sự kiện**: số vấn đề chặn và không chặn |
| Hai kịch bản | Hai "tab" gần như độc lập | Hai sự kiện dùng **cùng một mô hình vấn đề và cùng một vòng lặp** |
| Cách diễn đạt | "Làm thay ban điều hành" | "Xử lý phần việc vận hành lặp lại; người tổ chức giữ quyền quyết định" |
| Minh bạch | "Nhật ký suy luận" | **Decision trace**: đã kiểm tra gì, thấy gì, áp quy tắc nào, vì sao đề xuất |
| Dữ liệu | Chưa định nghĩa | Chốt schema `EventState`, `Issue`, `ProposedAction` và giao diện lõi ↔ planner |
| Phạm vi | Lõi / mở rộng 1 / mở rộng 2 | **P0 / P1 / P2**, bỏ giọng nói, bỏ báo cáo, không làm đa agent |
| Đánh giá | Độ chính xác phân loại, không lọt vi phạm | Thêm **độ chính xác tách ràng buộc** và **tỷ lệ đề xuất được duyệt nguyên văn** |
| Khoảnh khắc demo | Phương án rẻ bị loại có lý do | Thêm **"không có phương án hợp lệ"**: agent chỉ ra ràng buộc đang chặn và gợi ý nới |

---

## Mục lục
1. Bối cảnh
2. Định nghĩa
3. Mô hình sản phẩm
4. Mô hình dữ liệu
5. Hai luồng trọng tâm
6. Đối thủ và điểm khác biệt
7. Vì sao chọn hướng này
8. Đánh giá theo tiêu chí chấm
9. Kế hoạch triển khai
10. Rủi ro
11. Kết luận

---

## 1. Bối cảnh

### 1.1. Cuộc thi
| Mục | Nội dung |
|---|---|
| Tên | X-IA Hackathon #1 "Rise of Agents X" (X-IA cùng Binet IA tổ chức), online trên Discord |
| Thời gian code | 25/09/2026 09:00 → 27/09/2026 23:59 |
| Nộp bài | Link repo (README có hướng dẫn chạy thử), video tối đa 2 phút, mô tả ngắn, tên thành viên. Nộp trễ không được nhận. |
| Điều kiện bắt buộc | Dự án "agentic": dùng LLM để suy luận, ra quyết định, điều phối hành động |
| Tiêu chí chấm | Tác động 30% · Đổi mới 20% · Chất lượng thực hiện 20% · Trải nghiệm người dùng 15% · Demo và pitch 15%. Không cộng điểm vì dùng nhiều công cụ. |
| Vòng loại / chung kết | Ban điều hành X-IA chọn tối đa 5 finalist (đầu tháng 10); pitch trực tiếp tháng 11 |
| Sponsor | OpenAI, Pipelex, Dust, Gradium, Jinko |

### 1.2. Vấn đề
Vận hành một sự kiện nhỏ gồm rất nhiều việc vô hình: đối chiếu danh sách đăng ký với danh sách đã đóng tiền, trả lời cùng một câu hỏi nhiều lần, kiểm tra quy tắc, ghép đội hoặc xếp phòng, nhắc hạn, và với chuyến đi thì tìm phương án đi lại, chỗ ở trong ngân sách. Dữ liệu nằm rải rác ở email, biểu mẫu, bảng tính và quy chế; con người phải tự đối chiếu.

Ở các hội, những việc này do **tình nguyện viên không lương** làm:
| Số liệu | Giá trị | Nguồn |
|---|---|---|
| Số hội ở Pháp | khoảng 1,5 triệu | Associathèque [nguồn] |
| Tỷ lệ người Pháp làm tình nguyện | 40% (2013) → 34% (2025) | Thượng viện Pháp, 2025 [nguồn] |
| Lý do người điều hành hội bỏ cuộc | kiệt sức, **gánh nặng hành chính**, mất động lực | Thượng viện; Recherches & Solidarités [nguồn] |

Hội là **thị trường khởi đầu**. Cùng kiểu vận hành rời rạc (email + biểu mẫu + bảng tính + quy tắc) có ở câu lạc bộ sinh viên, hội thảo, hackathon, câu lạc bộ thể thao, hội cựu sinh viên.

### 1.3. Hai ví dụ dùng để demo
- **Hackathon của X-IA:** 108 người đăng ký, điều kiện phí hội viên 10€, đội 1–4 người (thi cá nhân hoặc đội 2–4), câu hỏi liên tục, ngày chung kết bị dời.
- **Weekend d'intégration (WEI):** chuyến đi cuối tuần của hội sinh viên cho khoảng 40 người, ngân sách cố định mỗi người, cần chọn phương án đi lại và chỗ ở, thu tiền, xếp phòng.

Khi trình bày, bối cảnh được đóng khung là *"chúng tôi nhận ra có bao nhiêu công việc vô hình phía sau một sự kiện như thế này"*, không phải nhận xét cách ban tổ chức làm việc.

---

## 2. Định nghĩa

| Thuật ngữ | Nghĩa |
|---|---|
| **Hội loi 1901** | Hình thức hội phi lợi nhuận ở Pháp (luật 1/7/1901). Ví dụ: câu lạc bộ thể thao, hội sinh viên, X-IA. |
| **Bureau** | Ban điều hành của hội (chủ tịch, thủ quỹ, thư ký), thường là tình nguyện viên. |
| **Cotisation** | Phí hội viên hằng năm. |
| **Weekend d'intégration (WEI)** | Chuyến đi cuối tuần đầu năm học của hội sinh viên. |
| **Trạng thái sự kiện** (`EventState`) | Toàn bộ dữ liệu của một sự kiện tại một thời điểm: người tham gia, khoản thanh toán, nhóm, hậu cần, quy tắc, hạn chót, tin nhắn, vấn đề, hành động. |
| **Vấn đề** (`Issue`) | Một điểm chưa nhất quán hoặc chưa xong trong trạng thái sự kiện. **Chặn** (blocking) nếu sự kiện chưa thể diễn ra đúng khi nó còn mở; **không chặn** nếu chỉ cần xử lý cho tốt hơn. |
| **Hành động đề xuất** (`ProposedAction`) | Việc agent đề xuất để giải quyết một vấn đề (gửi tin, sửa đội, ghi nhận thanh toán, chọn phương án chuyến đi...), kèm bằng chứng và các phép kiểm tra. |
| **Decision trace** | Phần hiển thị: agent đã kiểm tra những nguồn nào, tìm thấy gì, áp quy tắc nào, vì sao đề xuất. Không hiển thị chuỗi suy nghĩ nội bộ của mô hình. |
| **Ràng buộc cứng / ưu tiên mềm** | Ràng buộc cứng bị vi phạm thì phương án bị loại. Ưu tiên mềm chỉ dùng để xếp hạng các phương án hợp lệ. |
| **Người duyệt** | Mọi hành động có hệ quả (gửi ra ngoài, đổi trạng thái người tham gia, liên quan tiền) chỉ thực hiện sau khi người tổ chức duyệt. |
| **Sandbox** | Môi trường thử của Jinko: tìm và đặt thử không phát sinh giao dịch thật. |

---

## 3. Mô hình sản phẩm

### 3.1. Một vòng lặp duy nhất
```
      ┌──────────────────────────────────────────────────────────┐
      ▼                                                          │
 Trạng thái sự kiện ──► Phát hiện vấn đề ──► Điều tra ──► Đề xuất hành động
 (dữ liệu nội bộ +       (code cố định +       (công cụ,     (kèm bằng chứng,
  tin nhắn mới)           LLM đọc tin nhắn)     Jinko)        phép kiểm tra)
                                                                 │
                                                                 ▼
                                                  Người tổ chức duyệt / sửa / từ chối
                                                                 │
                                                                 ▼
                                                  Thực hiện → trạng thái mới ─────┘
```
Trả lời câu hỏi, đối chiếu thanh toán, ghép đội, lên kế hoạch chuyến đi đều là **cách giải quyết một loại vấn đề**, không phải tính năng riêng.

### 3.2. Ba lớp, ba vai trò
| Lớp | Làm gì | Ví dụ |
|---|---|---|
| **LLM** (chỗ mơ hồ) | Hiểu tin nhắn; tách yêu cầu thành ràng buộc; chọn công cụ và thứ tự; quyết định tự đề xuất hay hỏi người; giải thích đánh đổi | "Người viết 'j'ai payé avec mon adresse perso' đang nói về khoản thanh toán nào?" |
| **Code cố định** (quy tắc bất biến) | Kiểm tra điều kiện, sĩ số nhóm, mỗi người một nhóm, ngân sách, giờ đến; tính điểm tương đồng danh tính | `team_size ≤ 4`, `teams_per_participant ≤ 1`, `cost_per_person ≤ budget` |
| **Con người** (trách nhiệm) | Duyệt mọi hành động có hệ quả; xác nhận danh tính không chắc chắn; quyết định ngoại lệ | Gửi tin ra ngoài, ghi nhận thanh toán, hoàn tiền, chọn phương án chuyến đi |

### 3.3. Giao diện
- **Màn hình đầu:** danh sách sự kiện, mỗi sự kiện hiện **số vấn đề chặn và không chặn đang mở**. Không dùng một "phần trăm sẵn sàng" tự đặt công thức.
- **Bấm vào một sự kiện:** danh sách vấn đề, chặn trước. Mỗi vấn đề có trạng thái: *mở → đã có đề xuất → chờ người → đã giải quyết*.
- **Bấm vào một vấn đề:** decision trace, bằng chứng, các phép kiểm tra (✓/✗), độ tin cậy, hành động đề xuất có thể sửa, và nút duyệt/sửa/từ chối.
- **Sau khi duyệt:** vấn đề chuyển sang đã giải quyết; các vấn đề phụ thuộc (ví dụ nhắc thanh toán phụ thuộc vào phương án chuyến đi) được mở khóa.
- Tin nhắn, email và tệp CSV chỉ là **nguồn dữ liệu**, hiện ở một dòng nhỏ, không phải màn hình chính.

---

## 4. Mô hình dữ liệu

### 4.1. Schema (bản chốt để bắt đầu code)
```python
class Participant:
    id: str
    name: str
    emails: list[str]
    registered_at: datetime
    skills: list[str]          # hackathon
    needs: list[str]           # ví dụ "step_free" (WEI)
    group_id: str | None

class Payment:
    id: str
    payer_name: str
    payer_email: str | None
    amount: float
    paid_at: datetime
    reference: str | None
    participant_id: str | None  # None = chưa khớp với ai

class Group:                    # đội (hackathon) hoặc phòng (WEI)
    id: str
    kind: "team" | "room"
    members: list[str]          # participant ids
    capacity_min: int
    capacity_max: int
    declared_at: datetime | None

class Message:
    id: str
    channel: "email" | "discord" | "form"
    sender: str
    text: str
    received_at: datetime

class Issue:
    id: str
    kind: str                   # xem catalog 4.2
    blocking: bool
    title: str
    subject_ids: list[str]      # người/nhóm/tin nhắn liên quan
    status: "open" | "proposed" | "needs_human" | "resolved"
    depends_on: list[str]       # issue ids phải giải quyết trước

class Check:
    name: str                   # ví dụ "budget ≤ €120/person"
    passed: bool
    detail: str

class ProposedAction:
    id: str
    event_id: str
    issue_id: str
    action_type: str            # SEND_MESSAGE | LINK_PAYMENT | MOVE_MEMBER | SELECT_TRAVEL_PLAN | ESCALATE ...
    title: str
    description: str
    evidence: list[str]         # nguồn đã dùng (bản ghi, điều khoản, kết quả Jinko)
    checks: list[Check]
    confidence: float           # 0–1
    requires_approval: bool     # luôn True với hành động có hệ quả
    payload: dict               # dữ liệu để thực thi

class EventState:
    id: str
    name: str
    rules: str                  # quy chế / thông tin sự kiện
    deadlines: dict[str, datetime]
    participants: list[Participant]
    payments: list[Payment]
    groups: list[Group]
    messages: list[Message]
    logistics: dict | None      # phương án chuyến đi đã chọn (WEI)
    issues: list[Issue]
    actions: list[ProposedAction]
```
Trong bản hackathon, "nhiều sự kiện" chỉ là một từ điển `{ "hackathon": EventState, "wei": EventState }`. Không làm quản lý tổ chức, phân quyền hay trình tạo sự kiện.

### 4.2. Danh mục vấn đề cho hai sự kiện demo
| Sự kiện | Loại vấn đề (`kind`) | Chặn? | Phát hiện bằng | Giải quyết bằng |
|---|---|---|---|---|
| Hackathon | `unpaid_membership` | Có | Code: đối chiếu đăng ký × thanh toán | Nhắc cá nhân hóa |
| Hackathon | `unmatched_payment` / tin nhắn "tôi đã trả rồi" | Có | Code + LLM đọc tin nhắn | Đối chiếu danh tính; điểm thấp hoặc vừa thì hỏi người |
| Hackathon | `duplicate_membership` (một người ở hai đội) | Có | Code | Đề xuất giữ đội khai trước |
| Hackathon | `group_over_capacity` (đội > 4) | Có | Code | Yêu cầu đội tự chọn người rời |
| Hackathon | `unanswered_question` | Không | LLM | Trả lời có trích điều khoản; không có trong quy chế thì chuyển người |
| Hackathon | `sensitive_request` (xin dữ liệu cá nhân) | Không | LLM | Chuyển người, không chuẩn bị gì |
| Hackathon | `solo_participants` (muốn có đội) | Không | Code + LLM | Đề xuất ghép đội (tham lam, đơn giản) |
| WEI | `no_logistics_plan` | Có | Code | Planner nhiều ràng buộc (mục 5.2) |
| WEI | `unmatched_payment` | Có | Code | Như hackathon |
| WEI | `unpaid_participation` | Có | Code | Nhắc, **phụ thuộc** `no_logistics_plan` (số tiền phụ thuộc phương án) |
| WEI | `rooms_unassigned` | Có | Code | Xếp phòng, **phụ thuộc** `no_logistics_plan` |
| WEI | `unanswered_question` | Không | LLM | Trả lời, phụ thuộc phương án (giờ tập trung) |
| WEI | `refund_request` | Không | LLM | Kiểm tra chính sách, chuyển người quyết |

### 4.3. Giao diện giữa lõi và planner
Người làm lõi và người làm planner code song song, chỉ gặp nhau ở hợp đồng này:
```python
class TravelRequest:
    event_id: str
    text: str                       # yêu cầu nguyên văn của người tổ chức
    participants: int
    origin: str
    depart_after: datetime
    return_by: datetime | None

class Constraints:
    hard: dict                      # {"max_cost_per_person": 120, "arrive_before": "21:00",
                                    #  "no_overnight": True, "step_free_rooms": 2, ...}
    soft: list[str]                 # thứ tự ưu tiên, ví dụ ["fewer_changes", "near_station"]
    clarifications: list[str]       # câu cần hỏi lại (rỗng nếu đủ thông tin)

def extract_constraints(req: TravelRequest) -> Constraints: ...          # LLM
def plan_trip(req: TravelRequest, c: Constraints) -> ProposedAction: ...
# Trả về: 1 ProposedAction(action_type="SELECT_TRAVEL_PLAN") chứa mọi phương án
# trong payload (kể cả phương án bị loại và lý do), hoặc 1 ProposedAction
# (action_type="ESCALATE") khi không có phương án hợp lệ, kèm chẩn đoán ràng buộc chặn.
```

---

## 5. Hai luồng trọng tâm

### 5.1. Hackathon: một khoản phí không khớp, xuất phát từ một tin nhắn mơ hồ
**Đầu vào:** *"Bonjour, j'ai déjà payé ma cotisation mais je reçois encore des relances. J'ai utilisé mon adresse perso pour payer."* từ `a.nguyen@polytechnique.edu`.

| Bước | Ai làm | Nội dung |
|---|---|---|
| 1 | LLM | Hiểu: người này khẳng định đã trả phí bằng email khác; cần đối chiếu |
| 2 | Code | Tìm đăng ký theo email gửi: *Antoine Nguyen*, chưa có phí |
| 3 | Code | `match_person` trên các khoản thanh toán chưa khớp: *A. Nguyen · nguyen.a@gmail.com · 19/09* · điểm 0,91 (tên gần khớp, phần trước @ đảo thứ tự, trả sau khi đăng ký) |
| 4 | Code | Ngưỡng: ≥ 0,98 đề xuất ghép; 0,70–0,98 **hỏi người**; < 0,70 coi là khác người |
| 5 | LLM | Soạn câu hỏi xác nhận cho người tổ chức và thư trả lời sẵn cho người tham gia |
| 6 | Người | Xác nhận |
| 7 | Hệ thống | Thanh toán gắn với người tham gia → vấn đề `unpaid_membership` của người này tự đóng → thư trả lời được gửi → nhắc hạn sau đó không còn gửi nhầm |

Luồng phụ trong cùng sự kiện: người ở hai đội (đề xuất sửa), đội 5 người (yêu cầu đội tự chọn).

### 5.2. WEI: lập kế hoạch theo nhiều ràng buộc
**Đầu vào:** *"WEI cho 40 người, đi tối thứ Sáu 9/10 từ Paris, về chiều Chủ Nhật. Tối đa 120€/người cả đi lại và ở. Đến trước 21h. Không đi xe đêm. Hai bạn cần phòng không bậc thang."*

| Bước | Ai làm | Nội dung |
|---|---|---|
| 1 | LLM | Tách ràng buộc cứng (40 người, ≤ 120€, đến trước 21:00, không qua đêm, ≥ 2 phòng không bậc thang) và ưu tiên mềm (ít đổi tàu, gần ga, về trước 20:00 Chủ Nhật) |
| 2 | LLM | Thấy mơ hồ: ngân sách có gồm ăn uống? → **hỏi lại** trước khi tìm |
| 3 | Jinko | `ground-search` (tàu, xe khách), `hotel-search` (chỗ ở), trên sandbox |
| 4 | LLM | Ghép thành phương án trọn gói, cố ý gồm cả phương án rẻ nhất để kiểm tra |
| 5 | Code | `check_constraints`: loại phương án vi phạm, ghi lý do cụ thể |
| 6 | Code + LLM | Xếp hạng phương án hợp lệ **theo ưu tiên hiện tại** (không tuyên bố "khách quan tốt nhất"); LLM giải thích đánh đổi |
| 7 | Người | Chọn một phương án |
| 8 | Hệ thống | Vấn đề `no_logistics_plan` đóng → mở khóa nhắc thanh toán (điền đúng số tiền), xếp phòng, trả lời giờ tập trung |

**Khi không có phương án hợp lệ** (ví dụ ngân sách 90€): agent **không tự nới ràng buộc**. Nó đề xuất hành động `ESCALATE` kèm chẩn đoán: *"Ràng buộc đang chặn: ngân sách ≤ 90€/người. Nếu nâng lên 112€ thì có 1 phương án hợp lệ; nếu chấp nhận đến lúc 22:10 thì có 1 phương án 96€."*

---

## 6. Đối thủ và điểm khác biệt
| Nhóm | Ví dụ | Khác ở đâu |
|---|---|---|
| Phần mềm quản lý hội | AssoConnect (40.000 hội), HelloAsso | Họ lưu dữ liệu; Bureau Agent phát hiện vấn đề và đề xuất hành động trên dữ liệu đó |
| Tư vấn làm agent riêng | E-mhotep, Product'IA, Path IA, Batemark | Họ làm chatbot theo đơn đặt hàng; Bureau Agent là một vòng lặp vận hành có sẵn |
| Agent cho tổ chức phi lợi nhuận (Mỹ) | Pickaxe, Workclaw, Salesforce Agentforce, ClubRunner | Thiên về gây quỹ, tiếng Anh, doanh nghiệp lớn |
| Ứng dụng du lịch nhóm | MonkeyTravel, Agoroam, Roamly | Phục vụ nhóm bạn đi chơi; không lo thu tiền, xếp phòng, quy tắc của ban tổ chức |
| Agent xử lý chuyến bay bị hủy | ~20 dự án mã nguồn mở năm 2026 | Một hành khách; không có trạng thái sự kiện |
| Nền tảng dựng agent | Dust | Công cụ chung; Bureau Agent có sẵn mô hình trạng thái sự kiện và các quy tắc nghiệp vụ |

**Nhận định:** từng mảnh đều đã có người làm. Điểm khác nằm ở **cách tổ chức**: một agent được giám sát, giữ nhất quán cho trạng thái của một sự kiện, trên cả giao tiếp, dữ liệu nội bộ và hậu cần ngoài đời thật. Mức đổi mới: trung bình khá.

**Câu khác biệt dùng trong pitch:**
> "Không phải chatbot cho hội, cũng không phải trợ lý hộp thư. Bureau Agent là trung tâm điều hành cho một sự kiện: nó thấy cái gì chưa ổn, tìm hiểu, đề xuất cách sửa hợp lệ, và người tổ chức chỉ việc duyệt."

---

## 7. Vì sao chọn hướng này
1. Nhóm rà soát 23 ý tưởng, tìm đối thủ cho từng ý tưởng, chấm theo tiêu chí cuộc thi. Ý tưởng "agent cho ban điều hành hội" đứng đầu vì **ban giám khảo vòng loại là người dùng mục tiêu** và rủi ro kỹ thuật thấp.
2. Góp ý của Huy (chuyến đi của hội) và Bảo (lập kế hoạch nhiều ràng buộc) bù đúng điểm yếu lớn nhất: demo thiếu hành động ngoài đời thật và thiếu suy luận nhìn thấy được.
3. Ý tưởng *Polaris* (agent xử lý chuyến bay bị hủy cho một hành khách) được **gộp phần mạnh nhất** (cơ chế ràng buộc) thay vì làm riêng, vì mảng đó đã có khoảng 20 dự án gần trùng trong năm 2026.
4. Phản biện độc lập chỉ ra rủi ro "hai sản phẩm ghép lại". Phiên bản 3 giải quyết bằng một mô hình chung (trạng thái → vấn đề → hành động) cho cả hai sự kiện.

**Về phần chuyến đi:** mức tăng điểm ước tính nhỏ (khoảng 0,15, trong sai số tự chấm). Giá trị chính là độ tin cậy của demo và bằng chứng agentic. Phần này thuộc P1 và bị cắt nếu lõi chưa xong đúng hạn (mục 9.3).

---

## 8. Đánh giá theo tiêu chí chấm
Thang 1–5 do nhóm tự đặt; ban tổ chức không công bố thang chi tiết.

| Tiêu chí (trọng số) | Hiện tại | Có thể đạt | Điều kiện |
|---|---|---|---|
| Tác động (30%) | 3 | 4 | Một hội thật dùng thử; số đo thời gian tiết kiệm |
| Đổi mới (20%) | 3 | 3 | Khái niệm "trung tâm điều hành sự kiện" rõ trong UI và pitch |
| Chất lượng thực hiện (20%) | 3 | 4 | Đúng schema, P0 chạy trọn, bộ đánh giá |
| Trải nghiệm người dùng (15%) | 3 | 4 | Màn hình tình trạng sự kiện, decision trace gọn |
| Demo và pitch (15%) | 4 | 5 | Phương án rẻ bị loại; "không có phương án hợp lệ" và gợi ý nới |
| **Tổng có trọng số** | **3,15** | **khoảng 3,95** | |

**Yếu tố bổ sung (không thuộc tiêu chí chính thức):** mức gần với ban giám khảo 5/5, vì X-IA là hội tình nguyện.

**Điểm mạnh:** giám khảo là người dùng; tính agentic nhìn thấy được; phần lõi rủi ro thấp; đo lường được; có đường dùng thật sau cuộc thi.
**Điểm yếu:** đổi mới trung bình khá; tác động của một hội khó quy ra con số lớn; phạm vi rộng hơn nếu làm cả P1; phụ thuộc Jinko cho phần demo ấn tượng nhất.

---

## 9. Kế hoạch triển khai

### 9.1. Kiến trúc
**Một agent điều phối duy nhất**, không làm đa agent (đa agent chỉ tăng chỗ hỏng trong 63 giờ).
```
 Email / Discord / Biểu mẫu / CSV ──► Nạp dữ liệu ──► EventState
                                                        │
                                        Phát hiện vấn đề (code) ◄── LLM đọc tin nhắn
                                                        │
                                               ┌────────▼────────┐
                                               │  Event Agent    │  (OpenAI, gọi công cụ)
                                               └───┬────┬────┬───┘
                                                   │    │    │
                                     Tra quy chế ◄─┘    │    └─► Planner chuyến đi
                                                        │        (Jinko + check_constraints)
                                        Công cụ trạng thái:
                                        eligibility, match_person,
                                        check_groups, propose_groups
                                                        │
                                                 ProposedAction[]
                                                        │
                                                 Hàng chờ duyệt (web)
```
| Thành phần | Công nghệ |
|---|---|
| Agent | OpenAI, gọi công cụ, đầu ra có cấu trúc |
| Quy tắc cố định | Python thuần (Pipelex chỉ dùng nếu làm quen nhanh; không bắt buộc) |
| Hậu cần | Jinko `ground-search`, `hotel-search` trên sandbox; lưu kết quả để chạy lại |
| Giao diện | Ứng dụng web nhẹ, chạy cục bộ |
| Dữ liệu | Giả lập (JSON/CSV) cho hai sự kiện; không dùng dữ liệu cá nhân thật |
| Không làm | Giọng nói, báo cáo, Discord thật, tích hợp HelloAsso, phân quyền |

### 9.2. Công cụ của agent
| Công cụ | Loại | Làm gì |
|---|---|---|
| `get_event_state` | Code | Đọc tóm tắt trạng thái, vấn đề đang mở |
| `search_rules` | Code | Tìm điều khoản liên quan trong quy chế / thông tin sự kiện |
| `check_eligibility` | Code | Đối chiếu đăng ký × thanh toán |
| `match_person` | Code (điểm) + LLM (quyết định) | Tính điểm danh tính từ tên, phần trước @, tên miền, thời điểm; áp ngưỡng |
| `check_groups` | Code | Sĩ số nhóm, mỗi người một nhóm |
| `propose_groups` | Code | Ghép tham lam theo kỹ năng hoặc xếp phòng theo sức chứa và nhu cầu |
| `search_transport`, `search_lodging` | Jinko | Tìm phương án thật |
| `check_constraints` | Code | Kiểm từng ràng buộc cứng, trả lý do |
| `propose_action` | Code | Ghi một `ProposedAction` vào hàng chờ (agent không tự thực thi) |

### 9.3. Phạm vi
| P0: bắt buộc | P1: điểm nhấn demo | P2: chỉ khi thừa thời gian |
|---|---|---|
| `EventState` + nạp dữ liệu hackathon | Planner WEI: tách ràng buộc, Jinko, `check_constraints`, xếp hạng | Xếp phòng WEI |
| Phát hiện vấn đề bằng code | Bảng so sánh phương án | Đặt thử trên sandbox |
| Vòng lặp agent + các công cụ | Trường hợp "không có phương án hợp lệ" | Discord thật |
| Đối chiếu danh tính, quy chế, đội | Nhắc thanh toán WEI phụ thuộc phương án | Pipelex, Dust |
| Hàng chờ duyệt + decision trace | | Giọng nói |
| Bộ đánh giá | | |

**Mốc cắt:** nếu 12:00 thứ Bảy P0 chưa chạy trọn luồng, bỏ P1 và nộp riêng kịch bản hackathon.

### 9.4. Cấu trúc mã nguồn
```
bureau-agent/
  bureau/
    models.py        schema mục 4.1
    loader.py        nạp EventState từ data/
    detect.py        phát hiện vấn đề bằng code
    tools/           rules, eligibility, identity, groups
    agent.py         vòng lặp agent (OpenAI)
    planner/         hợp đồng mục 4.3, check_constraints, Jinko
    cli.py           chạy từ dòng lệnh
  app/               giao diện hàng chờ duyệt
  data/hackathon/    dữ liệu giả lập
  data/wei/          dữ liệu giả lập + kết quả Jinko đã lưu
  eval/              bộ đánh giá
  tests/             kiểm tra các quy tắc bất biến
  README.md
```

### 9.5. Lịch làm việc
| Thời điểm | Việc |
|---|---|
| Thứ Sáu 25/09 tối | Schema, dữ liệu giả lập hackathon, phát hiện vấn đề, công cụ cố định, kiểm thử; chạy thử OpenAI khi có khóa |
| Thứ Bảy sáng | Vòng lặp agent + hàng chờ duyệt; P0 chạy trọn luồng **trước 12:00** |
| Thứ Bảy chiều | P1: planner WEI (Bảo làm song song từ thứ Sáu theo hợp đồng 4.3) |
| Thứ Bảy tối | Bộ đánh giá, sửa lỗi. **Ngừng thêm tính năng lúc 23:00.** |
| Chủ Nhật sáng | Hoàn thiện giao diện, README; buổi dùng thử với hội thật |
| Chủ Nhật chiều | Video, **xong trước 20:00** |
| Chủ Nhật tối | Chạy README trên máy khác; **nộp trước 22:00** |

### 9.6. Phân vai
| Vai trò | Người làm | Việc |
|---|---|---|
| Lõi | (xem TASKS.md) | Schema, phát hiện vấn đề, vòng lặp agent, công cụ |
| Planner | (xem TASKS.md) | Hợp đồng 4.3, tách ràng buộc, Jinko, `check_constraints`, xếp hạng |
| Kịch bản chuyến đi + người dùng thật | (xem TASKS.md) | Dữ liệu một chuyến đi thật; liên hệ một hội sinh viên dùng thử |
| Giao diện, video, pitch | (xem TASKS.md) | Hàng chờ duyệt, decision trace, video, README |

### 9.7. Đánh giá
| Chỉ số | Cách đo |
|---|---|
| Hiểu đúng yêu cầu | Tỷ lệ tin nhắn được gán đúng loại vấn đề (bộ ~50 tin có đáp án) |
| Chọn đúng công cụ | Tỷ lệ trường hợp gọi đúng công cụ cần thiết |
| Không tạo trạng thái sai | Số hành động đề xuất vi phạm quy tắc bất biến (mục tiêu 0) |
| Trích đúng quy chế | Tỷ lệ câu trả lời trích đúng điều khoản |
| Hỏi người đúng lúc | Tỷ lệ trường hợp mơ hồ được chuyển người; tỷ lệ chuyển người không cần thiết |
| **Duyệt nguyên văn** | % đề xuất được duyệt không cần sửa |
| Tách ràng buộc đúng | So ràng buộc trích ra với đáp án trên ~10 yêu cầu chuyến đi |
| Phát hiện không khả thi | Tỷ lệ báo đúng "không có phương án hợp lệ" |
| Thời gian | Làm tay so với agent cộng thời gian duyệt |

### 9.8. Kịch bản video (2 phút)
| Thời gian | Nội dung |
|---|---|
| 0:00–0:10 | "Tổ chức một sự kiện thì vui. Vận hành phía sau thì không." Hình: 108 đăng ký, 50 tin nhắn, phí, đội, hạn chót, chuyến đi, phòng. "Và phần lớn do tình nguyện viên làm." |
| 0:10–0:18 | "Bureau Agent: agent vận hành sự kiện cho các hội." Màn hình: hai sự kiện, số vấn đề chặn. |
| 0:18–0:42 | Hackathon: tin nhắn mơ hồ về phí → đối chiếu danh tính, hỏi xác nhận → duyệt → vấn đề đóng, nhắc hạn không còn gửi nhầm. |
| 0:42–1:22 | WEI: yêu cầu bằng lời → ràng buộc cứng/mềm → Jinko → phương án 96€ bị loại vì đến 22:10, 141€ bị loại vì vượt ngân sách → hai phương án hợp lệ → thử ngân sách 90€: "không có phương án hợp lệ, ràng buộc chặn là ngân sách". |
| 1:22–1:40 | Duyệt phương án 112€ → "Travel plan resolved" → vấn đề tiếp theo: 6 người chưa trả, phòng chưa xếp. |
| 1:40–1:52 | Kiến trúc trong một hình: LLM cho chỗ mơ hồ, code cho quy tắc, Jinko cho dữ liệu thật, con người duyệt. Số liệu đánh giá. |
| 1:52–2:00 | "Một agent. Mọi sự kiện. Người tổ chức vẫn nắm quyền." |

---

## 10. Rủi ro
| Rủi ro | Cách xử lý |
|---|---|
| Phạm vi phình | P0/P1/P2; mốc cắt 12:00 thứ Bảy; ngừng thêm tính năng 23:00 thứ Bảy |
| Hai kịch bản trông như hai sản phẩm | Cùng mô hình vấn đề, cùng hàng chờ, cùng decision trace; demo chuyển giữa hai sự kiện qua màn hình tình trạng |
| Bị coi là chatbot / AI hộp thư | Màn hình đầu là tình trạng sự kiện, không phải hộp thư |
| Lõi và planner ghép không khớp | Hợp đồng 4.3 chốt trước khi code |
| Jinko chậm, lỗi, hết credit | Lưu kết quả thật để chạy lại; README ghi rõ phần nào gọi trực tiếp |
| Kho Jinko thiếu chỗ ở cho nhóm lớn | Ghép nhiều phòng; không đủ thì chuyển người, không tự nới ràng buộc |
| Agent sai quy chế hoặc bỏ qua ràng buộc | Trích điều khoản bắt buộc; ràng buộc kiểm bằng code; mọi thứ qua duyệt |
| Gộp nhầm danh tính | Ngưỡng; vùng giữa luôn hỏi người; không tự gộp |
| Xếp hạng bị cho là tùy tiện | Nói rõ "xếp theo ưu tiên hiện tại"; ưu tiên chỉnh được |
| Dữ liệu cá nhân (RGPD) | Chỉ dữ liệu giả lập |
| Minh bạch AI (EU AI Act, Điều 50) | Tin do agent soạn có dòng "soạn với trợ giúp của AI, đã được ban tổ chức duyệt" |

---

## 11. Kết luận
Phiên bản 3 là **ứng viên tốt để vào nhóm 5 finalist** và có cơ hội cạnh tranh chức vô địch nếu P0 và P1 chạy trọn, có người dùng thật và có số liệu đánh giá. So với phiên bản 2, ý tưởng không đổi; thứ thay đổi là **bản sắc sản phẩm**: một trung tâm điều hành sự kiện với một vòng lặp duy nhất, thay vì một tập tính năng.

Các yếu tố quyết định, theo mức ảnh hưởng:
1. Làm xong P0 và nộp đúng hạn.
2. Một hội thật dùng thử và nhận xét.
3. Khoảnh khắc demo: phương án rẻ bị loại có lý do; "không có phương án hợp lệ" kèm chẩn đoán.
4. Số liệu: không hành động nào vi phạm quy tắc; tỷ lệ duyệt nguyên văn; thời gian tiết kiệm.
5. Đề nghị cụ thể: chạy thử cho sự kiện tháng 11 của X-IA.

---

## Nguồn
- Quy chế, slide buổi giới thiệu sponsor, trang Luma của cuộc thi.
- X-IA: https://www.egis-group.com/fr/actualites/x-ia-le-reseau-des-polytechniciens-professionnels-de-lia-sassocie-a-six-sponsors-de-premier-plan-pour-accelerer-son-developpement-dont-egis · https://ax.polytechnique.org/en/group/x-intelligence-artificielle/102
- Số hội: https://www.associatheque.fr/fr/creer-association/chiffres-cles.html
- Tình nguyện: https://www.senat.fr/questions/base/2025/qSEQ250605041.html · https://recherches-solidarites.org/benevolat/
- Jinko: https://docs.gojinko.com/llms.txt · https://docs.gojinko.com/api/ground-search.md · https://docs.gojinko.com/api/hotel-search.md · https://docs.gojinko.com/guides/sandbox-walkthrough.md
- Đối thủ: https://www.assoconnect.com/tableau-comparatif-logiciel-association/ · https://e-mhotep.com/blog/agent-ia-adherents-association · https://product-ia.fr/secteurs/ia-pour-associations · https://pickaxe.co/post/ai-agents-for-nonprofits · https://monkeytravel.app/group-trip-planner · https://github.com/austinlai22/trip-recovery-agent
- Bản mô phỏng giao diện: https://claude.ai/artifact/JCKLf1tuJLtPUPsfXK1ox4
