# Thông tin deploy — Checkpoint 5

## Thông tin học viên

| Mục | Nội dung |
|---|---|
| Họ và tên | Bùi Quốc Việt |
| Mã học viên | 2A202602884 |
| Repo | https://github.com/vietbui000/K4-L3B-DAY12-BuiQuocViet-2A202602884-CloudServicesAndDeployment |

## Service

| Mục | Nội dung |
|---|---|
| Public URL | https://agent-production-786b.up.railway.app |
| Platform | Railway |
| Ngày deploy | 2026-09-29 |
| Project | day12-buiquocviet-agent |
| Triển khai | Railway CLI upload source local, Dockerfile multi-stage |
| Health check deploy | /ready |

## Biến môi trường đã set trên cloud

| Biến | Nguồn giá trị |
|---|---|
| `PORT` | Railway tự cấp |
| `AGENT_API_KEY` | Đọc từ .env local và truyền qua stdin vào Railway Variables |
| `REDIS_URL` | Tham chiếu REDIS_URL của service Redis trong cùng project |
| `RATE_LIMIT_PER_MINUTE` | 10 |
| `MONTHLY_BUDGET_USD` | 10.0 |
| `LOG_LEVEL` | INFO |

Không ghi giá trị secret trong tài liệu. DEPLOY_API_KEY chỉ dùng trong .env local để chạy test.

## Kết quả chạy thật

Các request được gửi tới Public URL ngày 2026-09-29.

```text
GET /health: 200 {"status":"ok","service":"day12-agent","version":"1.0.0"}
GET /ready: 200 {"status":"ready","redis":true}
POST /ask without key: 401 {"detail":"invalid or missing API key"}
POST /ask with key: 200 {"answer":"Ngắn gọn: Hello phụ thuộc vào ba yếu tố — cấu hình qua biến môi trường, health check để orchestrator biết trạng thái, và giới hạn tài nguyên.","user_id":"cp5-review-1848d0b271114099b7bd454ce0880508","history_length":0,"cost_usd":2.115e-05,"tokens":{"in":1,"out":35}}
Rate limit (15 requests, same user): [200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 429, 429, 429, 429, 429]
```

Request thứ hai cùng user thấy history_length = 2, xác nhận Redis lưu lại hội thoại.
Chi tiết output: `screenshots/cp5-http-results.txt`.

## Kiểm tra lại

```powershell
curl.exe -i https://agent-production-786b.up.railway.app/health
curl.exe -i https://agent-production-786b.up.railway.app/ready
.\.venv\Scripts\python.exe -m pytest tests/test_cp5.py -v
```

## Ảnh chụp màn hình

- `screenshots/dashboard.png`: dashboard Railway cho thấy agent và Redis đều Online.
- `screenshots/health.png`: URL công khai `/health` trả `status: ok`.
- `screenshots/ready.png`: URL công khai `/ready` trả Redis sẵn sàng (bằng chứng bổ sung).

Không dùng local fallback. Deployment dùng source upload từ máy, chưa cấu hình GitHub autodeploy.
