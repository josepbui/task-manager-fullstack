# HỒ SƠ ĐẶC TẢ KỸ THUẬT DỰ ÁN (PROJECT SPECIFICATION)

## 1. Tổng quan & Giá trị thực tế (Business & Real-life Scope)
- **Tên dự án:** Full-stack Task Management System (FastAPI + Next.js).
- **Mục đích đời sống:** Giải quyết bài toán quản lý danh sách công việc hàng ngày của cá nhân hoặc đội ngũ nhỏ: tạo mới nhiệm vụ, theo dõi tiến độ, đánh dấu hoàn thành, và xóa các đầu việc không còn cần thiết.
- **Đặc trưng kiến trúc:** 
  - Mô hình **Decoupled Architecture** tách biệt hoàn toàn giữa Backend REST API và Frontend SSR/Client Components.
  - Tối ưu hóa cho môi trường phát triển cục bộ: khởi động toàn bộ stack chỉ với 1 dòng lệnh duy nhất qua Reverse Proxy.

---

## 2. Kiến trúc kỹ thuật (System Architecture)

- Client Browser (Port 3000) -> Next.js Frontend (React 18 + Tailwind CSS)
- Next.js Proxy Rewrites: /api/:path* -> FastAPI Backend (Port 8000)
- FastAPI Backend (Uvicorn + Pydantic + task_manager.py) -> Storage (tasks.json)

---

## 3. Thành phần chi tiết
- **Backend:** FastAPI (Python 3.14+, Uvicorn trên port 8000), tệp api_server.py, task_manager.py.
- **Frontend:** Next.js 14 (TypeScript, Tailwind CSS trên port 3000), cấu hình rewrites trong next.config.mjs.
- **Orchestration:** Script dev:all dùng concurrently chạy song song cả 2 dịch vụ.

---

## 4. Đặc tả REST API
- POST /api/tasks: Tạo task mới (201 Created)
- GET /api/tasks?include_completed=true/false: Lấy danh sách task (200 OK)
- PATCH /api/tasks/{task_id}: Đổi trạng thái hoàn thành (200 OK)
- DELETE /api/tasks/{task_id}: Xóa task (204 No Content)

---

## 5. Quy trình vận hành
- Khởi động: cd frontend && npm run dev:all
- Giải phóng port: kill -9 $(lsof -ti:8000,3000) 2>/dev/null || true
- Reset dữ liệu: echo '[]' > tasks.json
