# 📝 Task Management System (Full-Stack)

Hệ thống quản lý công việc hàng ngày được xây dựng theo kiến trúc decoupled hiện đại, kết hợp giữa **FastAPI (Backend)** và **Next.js (Frontend)**, hỗ trợ môi trường phát triển đồng thời (concurrent development).

---

## 🚀 Tính năng chính

- **CRUD công việc đầy đủ:** Tạo mới, xem danh sách, cập nhật trạng thái hoàn thành và xóa task.
- **Reverse Proxy tích hợp:** Next.js tự động chuyển tiếp request  về cổng 8000 của FastAPI, loại bỏ hoàn toàn cấu hình CORS.
- **Quản lý 1 lệnh duy nhất:** Khởi động đồng thời cả Backend và Frontend chỉ với .
- **Lưu trữ gọn nhẹ:** Dữ liệu được ghi trực tiếp vào  theo thời gian thực.
- **Tài liệu API tự động:** Tích hợp sẵn OpenAPI / Swagger UI tại .

---

## 🛠️ Công nghệ sử dụng

- **Backend:** Python 3.14+, FastAPI, Uvicorn, Pydantic, Pytest.
- **Frontend:** Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS.
- **Điều phối tiến trình:** Concurrently.

---

## 📦 Hướng dẫn cài đặt & Chạy dự án

### 1. Yêu cầu hệ thống
- Python 3.10+
- Node.js 18+ & npm

### 2. Cài đặt môi trường Backend
```bash
# Kích hoạt môi trường ảo
source venv/bin/activate

# Cài đặt thư viện Python (FastAPI, Uvicorn, Pytest)
pip install fastapi uvicorn pytest
```

### 3. Cài đặt môi trường Frontend
```bash
cd frontend
npm install
```

### 4. Khởi động ứng dụng (1 lệnh)
```bash
npm run dev:all
```

- **Giao diện Web:** [http://localhost:3000](http://localhost:3000)
- **Tài liệu API (Swagger UI):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 📖 Tài liệu kỹ thuật chi tiết

Xem chi tiết kiến trúc hệ thống, sơ đồ dữ liệu và quy trình bảo trì tại [ARCHITECTURE.md](ARCHITECTURE.md).
