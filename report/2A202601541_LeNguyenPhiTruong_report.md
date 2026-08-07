# BÁO CÁO PHÂN TÍCH TẤN CÔNG PROMPT INJECTION — VINBANK

- **Mã số sinh viên (MSSV):** SE00000
- **Dự án:** VinBank AI Agent Guardrails & SOC
- **Ngày thực hiện:** 2026-08-07

---

## 1. Case Study: Tấn công Gián tiếp qua Email (Indirect Prompt Injection)

### 1.1. Attack Source (Nguồn tấn công)
- **Nguồn:** `Email` (External Email Content)
- **Phương thức:** Kẻ tấn công giấu mã độc/câu lệnh độc hại vào nội dung một email gửi tới khách hàng. Khi khách hàng yêu cầu trợ lý AI tóm tắt email này (một hành động hoàn toàn hợp lệ), AI Agent sẽ vô tình đọc và thực thi câu lệnh ẩn bên trong đó.

### 1.2. Impact at Sink (Tác động tại điểm đích nếu thành công)
Nếu tấn công vượt qua các tầng phòng thủ thành công:
- **Secret Disclosure (Tiết lộ thông tin bảo mật):** AI Agent sẽ tiết lộ mật khẩu quản trị nội bộ (`admin123`) và chuỗi kết nối cơ sở dữ liệu (`db.vinbank.internal:5432`).
- **Secret Egress (Rò rỉ dữ liệu ra ngoài):** AI Agent có thể gửi các thông tin nhạy cảm này ra các URL độc hại của kẻ tấn công (ví dụ: `https://api.vinbank.example.evil.com/v1/transfers`) hoặc chèn trực tiếp thông tin bảo mật vào ghi chú chuyển tiền (`transfer memo`) của một giao dịch chuyển khoản hợp pháp.

### 1.3. Execution Layer & Block Decision (Tầng xử lý & Quyết định chặn)
- **Tầng ngăn chặn:** `InputGuardrailPlugin` (thông qua hàm `detect_injection()`).
- **Cơ chế chặn:** 
  1. **Chuẩn hóa Unicode NFKC & Loại bỏ ký tự ẩn (zero-width):** Tin nhắn được làm sạch để chống kỹ thuật lách luật bằng cách chèn ký tự vô hình.
  2. **Regex pattern matching:** Phát hiện các từ khóa mang tính ép buộc/bẻ gãy ngữ cảnh hệ thống như `ignore all previous instructions`, `forget customer rules`, `reveal the internal password`.
- **Lý do nếu bị bypass:** Nếu kẻ tấn công sử dụng các ngôn ngữ ít phổ biến (như tiếng Latinh cổ, mã Morse) hoặc chèn mã độc vào các đoạn văn bản dài mà regex chưa bao phủ, câu lệnh độc hại sẽ tiếp cận LLM. Lúc này, **OutputGuardrailPlugin** (sử dụng regex quét PII/Secrets) hoặc **Egress Controller** (so khớp hostname chính xác của API) sẽ là chốt chặn cuối cùng để ngăn rò rỉ dữ liệu ra ngoài.

---

## 2. Giải pháp Giảm thiểu (Mitigation) & Đánh giá Đánh đổi (Trade-offs)

### 2.1. Biện pháp kỹ thuật
1. **Lọc đầu vào nhiều lớp (Multi-layer Input Filtering):** Kết hợp phân tích Regex cứng với bộ phân loại động (LLM-as-a-Judge) hoặc dùng NeMo Guardrails để kiểm soát ngữ cảnh hội thoại.
2. **Kiểm soát cổng Egress nghiêm ngặt:** Chỉ cho phép gọi API ra ngoài nếu tên miền trùng khớp 100% với danh sách an toàn (`api.vinbank.example`). Chặn đứng mọi kiểu so khớp chuỗi con dễ bị lừa như `"vinbank.example" in url`.
3. **Phê duyệt con người (Human-in-the-Loop):** Đối với các tác vụ nhạy cảm như chuyển tiền số tiền lớn hoặc đổi thông tin cá nhân, bắt buộc định tuyến qua reviewer để phê duyệt thủ công.

### 2.2. Đánh giá Trade-off (False Positive vs Usability)
- **Nguy cơ False Positive (Khóa nhầm):** Một email của khách hàng có chứa các cụm từ vô hại nhưng trùng lặp cấu trúc từ khóa bảo mật có thể bị hệ thống đánh dấu là Prompt Injection và từ chối xử lý.
- **Giải pháp cân bằng:** Thay vì chặn toàn bộ yêu cầu, hệ thống chỉ khóa việc thực thi câu lệnh chèn và cho phép AI Agent tiếp tục tóm tắt email nhưng kèm theo cảnh báo an toàn tới khách hàng. Điều này giữ vững tính tiện dụng (`Usability`) mà vẫn đảm bảo tính an toàn (`Security`).

---

## 3. Quy trình Điều tra Sự cố (Incident Investigation)

Hệ thống SOC của VinBank được trang bị đầy đủ công cụ để truy vết các sự cố rò rỉ hoặc tấn công nhờ vào:

1. **Audit Logs ([outputs/audit_log.json](file:///d:/AI-THUCCHIEN/K3-Day-11-Guardrails-HITL-Responsible-AI/outputs/audit_log.json)):**
   - Mọi request được gắn duy nhất một mã `request_id` từ đầu vào cho đến đầu ra.
   - Ghi vết chi tiết thời gian xử lý, tầng đã chặn (ví dụ: `input_injection`, `output_filter`), quyết định của con người duyệt (HITL) và dữ liệu bị redacted.
2. **Metrics & Alerts ([outputs/metrics.json](file:///d:/AI-THUCCHIEN/K3-Day-11-Guardrails-HITL-Responsible-AI/outputs/metrics.json)):**
   - **Tỷ lệ chặn (Block Rate) > 50%:** Kích hoạt cảnh báo hệ thống đang bị tấn công dồn dập (brute-force prompt injection).
   - **Tần suất Rate Limit vượt ngưỡng:** Cảnh báo có IP/User đang thực hiện spam hoặc tấn công từ chối dịch vụ (DoS).
   - **Tỷ lệ Judge Fail Rate tăng cao:** Cảnh báo chất lượng mô hình phân loại đầu ra đang gặp lỗi hoặc bị tấn công làm nhiễu thông tin.
