# Phiếu Phản Ánh — K4 Level 3B, Ngày 12

> **Bài làm cá nhân.** Trả lời bằng lời của chính bạn, dựa trên những gì bạn
> quan sát được khi chạy code — không sao chép đáp án của người khác.
>
> Cách trả lời: thay từng dòng giữ chỗ bên dưới bằng câu trả lời.
> `grade.py` đếm số câu đã trả lời (15 điểm cho 10 câu).
>
> Họ và tên: Bùi Quốc Việt  Mã học viên: 2A202602884

---

### Câu 1 — Fail fast (CP1)

Trong `Settings`, `agent_api_key` không có giá trị mặc định nên app chết ngay
khi khởi động nếu thiếu biến môi trường. Hãy mô tả một tình huống cụ thể mà
việc "chết sớm" này cứu bạn, so với việc để mặc định `"changeme"`.

Khi deploy lên Railway, nếu tôi quên tạo biến `AGENT_API_KEY`, ứng dụng sẽ dừng
ngay ở bước startup và log báo thiếu cấu hình. Nhờ vậy service chưa nhận
traffic và tôi biết phải bổ sung secret. Nếu dùng khóa mặc định `"changeme"`,
health check vẫn có thể báo thành công, URL được công khai và người biết khóa
mặc định có thể gọi `/ask`, làm tiêu quota và chi phí trước khi tôi phát hiện.

---

### Câu 2 — Log cho máy đọc (CP1)

Chạy service và gọi `/ask` vài lần. Dán một dòng log JSON bạn thu được, rồi
nêu **hai** việc bạn làm được với dòng log đó mà `print("đã trả lời xong")`
không làm được.

Một event tôi quan sát được khi gọi `/ask` trên Railway là:

```json
{"event":"ask_completed","level":"info","timestamp":"2026-09-29T04:13:04.939939+00:00","user_id":"cp5-review","tokens_in":1,"tokens_out":35,"cost_usd":0.00002115}
```

Từ log có cấu trúc này, tôi có thể lọc hoặc đếm số event `ask_completed` theo
`user_id` và khoảng thời gian. Tôi cũng có thể cộng `cost_usd`, theo dõi token
và tạo cảnh báo khi chi phí tăng bất thường. Dòng `print("đã trả lời xong")`
không có các field ổn định để máy truy vấn và cũng không cho biết user, thời
gian, token hay chi phí của request.

---

### Câu 3 — Kích thước image (CP2)

Build cả hai phiên bản và ghi lại số đo thật:

```bash
docker build -f <Dockerfile-1-stage> -t agent:single .
docker build -t agent:multi .
docker images | grep agent
```

| Bản | Dung lượng |
|-----|-----------|
| 1 stage (bản đầu) | 1.7 GB |
| Multi-stage | 271 MB |

Giải thích: phần dung lượng chênh lệch đó là những gì?

Tôi build lại cả hai image và đọc kết quả bằng `docker images`. Bản một-stage
dùng image đầy đủ `python:3.11`, còn runtime của bản multi-stage dùng
`python:3.11-slim`. Phần chênh lệch chủ yếu là các gói hệ điều hành và công cụ
trong base image đầy đủ. Ngoài ra, stage builder và các file phục vụ build
không được mang nguyên sang image cuối; runtime chỉ nhận dependency đã cài,
`app/` và `utils/`.

---

### Câu 4 — Thứ tự lệnh trong Dockerfile (CP2)

Sửa một ký tự trong `app/main.py` rồi build lại. Với Dockerfile của bạn, những
layer nào được dùng lại từ cache, layer nào phải chạy lại? Nếu bạn đặt
`COPY . .` lên trước `RUN pip install` thì kết quả khác thế nào?

Khi chỉ sửa `app/main.py`, các layer base image, `WORKDIR`, `COPY
requirements.txt` và `RUN pip install` vẫn dùng lại cache vì
`requirements.txt` không đổi. Layer `COPY app ./app` thay đổi nên được tạo lại;
các layer đứng sau nó như copy phần source còn lại và tạo user cũng được Docker
xét lại. Nếu đặt `COPY . .` trước `RUN pip install`, mọi thay đổi source làm
layer `COPY` đổi, kéo theo bước cài toàn bộ dependency phải chạy lại dù danh
sách thư viện không thay đổi. Build vì thế chậm hơn rõ rệt.

---

### Câu 5 — Vì sao không chạy bằng root (CP2)

Container mặc định chạy bằng root. Mô tả chuỗi sự kiện dẫn từ "một lỗ hổng
trong code Python của bạn" tới "kẻ tấn công có quyền cao trên máy host", và
lệnh `USER` cắt đứt chuỗi đó ở chỗ nào.

Nếu code Python có lỗi cho phép thực thi lệnh, kẻ tấn công trước hết chạy được
lệnh bên trong container. Nếu process đang là root, họ có toàn quyền trong
container; khi container còn được cấp capability nguy hiểm, mount Docker
socket hoặc mount thư mục nhạy cảm của host, họ có thể sửa file host hay tạo
container đặc quyền và nâng mức ảnh hưởng lên máy host. `USER app` làm process
chỉ có UID 10001, nên ngay sau bước chiếm quyền thực thi, kẻ tấn công chỉ nhận
quyền của user thường. Cách này giảm quyền đọc/ghi và làm chuỗi tấn công khó
tiếp tục, dù vẫn cần tránh mount/capability nguy hiểm vì non-root không tự giải
quyết mọi cấu hình sai.

---

### Câu 6 — Cửa sổ trượt (CP3)

Rate limit của bạn dùng sliding window 60 giây. Nếu thay bằng cách đếm theo
phút đồng hồ (reset lúc giây 00), một người dùng có thể gửi tối đa bao nhiêu
request trong 2 giây liên tiếp khi hạn mức là 10/phút? Giải thích cách đạt được
con số đó.

Người dùng có thể gửi tối đa 20 request trong khoảng 2 giây: gửi 10 request ở
cuối phút, ví dụ 10:00:59, rồi gửi thêm 10 request ngay sau khi bộ đếm reset ở
10:01:00. Cả hai nhóm đều không vượt 10 request trong phút đồng hồ của chúng,
nhưng thực tế 20 request dồn vào khoảng thời gian rất ngắn. Sliding window 60
giây vẫn nhìn thấy nhóm request trước nên sẽ chặn nhóm thứ hai.

---

### Câu 7 — Rate limit và cost guard (CP3)

Hai cơ chế này khác nhau ở điểm nào? Cho một tình huống mà rate limit cho qua
nhưng cost guard phải chặn, và một tình huống ngược lại.

Rate limit giới hạn số request trong một khoảng thời gian, còn cost guard giới
hạn tổng số tiền theo user và tháng UTC. Ví dụ user mới gửi một request có
prompt rất lớn trong phút đó: rate limit vẫn cho qua vì số request thấp, nhưng
cost guard phải chặn nếu chi phí ước tính làm vượt ngân sách tháng. Chiều ngược
lại, user còn gần như toàn bộ ngân sách và gửi 11 câu hỏi rất ngắn trong 60
giây: cost guard vẫn đủ tiền, nhưng rate limit 10/phút phải chặn request thứ 11.

---

### Câu 8 — /health khác /ready (CP4)

Nếu gộp hai endpoint làm một và cho nó kiểm tra Redis, chuyện gì xảy ra với cụm
3 container khi Redis mất kết nối 30 giây? Trả lời theo đúng thứ tự sự kiện.

Nếu gộp hai endpoint và probe đó kiểm tra Redis, khi Redis mất kết nối thì cả
ba container cùng trả 503. Load balancer loại cả ba khỏi danh sách nhận
traffic. Nếu orchestrator dùng cùng probe như liveness, nó tiếp tục restart cả
ba container dù process Python vẫn khỏe. Các container khởi động lại nhưng
Redis vẫn lỗi nên probe tiếp tục thất bại, tạo vòng lặp restart và service mất
toàn bộ khả năng phục vụ. Khi tách riêng, `/health` vẫn 200 để tránh restart
không cần thiết, còn `/ready` trả 503 để tạm ngừng chuyển request cho đến khi
Redis phục hồi.

---

### Câu 9 — Stateless (CP4)

Chạy `docker compose up --scale agent=3` rồi gọi `/ask` nhiều lần với cùng một
`X-User-Id`. Quan sát `history_length` trong response. Nếu lịch sử được lưu
trong một dict Python thay vì Redis, bạn sẽ thấy con số đó thay đổi thế nào?

Khi gọi trực tiếp ba replica với cùng `X-User-Id`, tôi quan sát
`history_length` lần lượt là 0, 2 và 4. Điều đó cho thấy request đi qua các
container khác nhau vẫn đọc được lịch sử chung trong Redis; mỗi lượt thành
công thêm hai message user/assistant. Nếu dùng dict Python, mỗi container có
một bản lịch sử riêng. Khi request chuyển replica, số liệu có thể thành
0, 0, 2 hoặc tăng rồi giảm tùy container được chọn, thay vì tăng đều 0, 2, 4.
Restart một container còn làm mất toàn bộ phần lịch sử nằm trong dict của nó.

---

### Câu 10 — Deploy thật (CP5)

Ghi lại **một** lỗi bạn gặp khi deploy lên cloud (build fail, health check
timeout, sai REDIS_URL, app không đọc `$PORT`...): thông báo lỗi là gì, bạn
tìm ra nguyên nhân bằng cách nào, và sửa ra sao?

Khi bắt đầu deploy bằng Railway CLI, lệnh đăng nhập browserless báo
`dns error: No such host is known` khi gọi `backboard.railway.com`, nên CLI
không lấy được mã xác thực. Tôi kiểm tra bằng `Resolve-DnsName` và thấy DNS hoạt
động trở lại, sau đó chạy lại `railway login --browserless`, mở URL activation
và xác nhận mã mới. Lần thứ hai CLI báo đúng tài khoản đăng nhập; tôi tiếp tục
tạo project, Redis và agent, rồi kiểm tra `/health` và `/ready` đều trả 200.
