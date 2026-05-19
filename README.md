# 🍜 Business Improvement Agent
> COS30018 – Intelligent Systems | Option D | LLM-Powered Multiagent System

Hệ thống phân tích reviews nhà hàng tự động, sử dụng nhiều AI agents phối hợp để thu thập, xử lý và tạo báo cáo cải thiện kinh doanh.

---

## 📌 Mục lục

- [Giới thiệu](#giới-thiệu)
- [Kiến trúc hệ thống](#kiến-trúc-hệ-thống)
- [Pipeline chi tiết](#pipeline-chi-tiết)
- [Cấu trúc thư mục](#cấu-trúc-thư-mục)
- [Công nghệ sử dụng](#công-nghệ-sử-dụng)
- [Yêu cầu hệ thống](#yêu-cầu-hệ-thống)
- [Hướng dẫn cài đặt](#hướng-dẫn-cài-đặt)
- [Hướng dẫn chạy](#hướng-dẫn-chạy)
- [API Endpoints](#api-endpoints)
- [Ví dụ output](#ví-dụ-output)

---

## Giới thiệu

**Business Improvement Agent** là hệ thống multiagent được xây dựng bằng Python, cho phép người dùng nhập tên một nhà hàng và nhận về báo cáo phân tích toàn diện dựa trên reviews thực tế từ nhiều nguồn dữ liệu.

### Tính năng chính

| Tính năng | Mô tả |
|---|---|
| 🔍 Thu thập đa nguồn | Yelp Dataset, Google Maps scraping, CSV upload |
| 🧹 Làm sạch dữ liệu | Lọc spam, duplicate, chuẩn hoá tự động |
| 🧠 RAG | Vector search tìm reviews liên quan theo từng chủ đề |
| 💬 Sentiment Analysis | Phân tích cảm xúc positive/negative/neutral |
| 🏷️ Topic Analysis | Phân tích 4 chủ đề: food, service, price, ambiance |
| 🛡️ Hallucination Check | Kiểm tra và auto-fix kết quả LLM |
| 📝 Báo cáo | Điểm mạnh, điểm yếu, đề xuất cải thiện |
| 🌐 Web UI | React frontend + FastAPI backend |

---

## Kiến trúc hệ thống

```
┌─────────────────────────────────────┐
│           React Frontend            │
│  - Tìm kiếm quán                    │
│  - Upload CSV reviews               │
│  - Hiển thị báo cáo + biểu đồ      │
└──────────────┬──────────────────────┘
               │ HTTP Request
┌──────────────▼──────────────────────┐
│         FastAPI Backend             │
│  - Nhận request từ React            │
│  - Gọi Manager Agent                │
│  - Trả kết quả về React             │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│         Multiagent System           │
│                                     │
│  Manager Agent                      │
│  ├── Data Collector Agent           │
│  │   ├── Yelp Loader                │
│  │   ├── Google Scraper             │
│  │   └── CSV Handler                │
│  ├── Data Validator Agent           │
│  ├── RAG Agent (ChromaDB)           │
│  ├── Sentiment Agent                │
│  ├── Topic Agent                    │
│  ├── Hallucination Checker          │
│  └── Report Agent                   │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│         LLM – Groq API              │
│      Llama 3.3 70b Versatile        │
└─────────────────────────────────────┘
```

---

## Pipeline chi tiết

### Tổng quan luồng xử lý

```
User nhập tên quán
        │
        ▼
[1] Data Collector Agent
        │── Yelp Dataset (ưu tiên 1)
        │── Google Maps Scraping (ưu tiên 2)
        └── CSV Upload (ưu tiên 3)
        │
        ▼ raw DataFrame
[2] Data Validator Agent
        │── Xoá null / rỗng
        │── Lọc review quá ngắn (< 10 ký tự)
        │── Lọc spam (số, ký tự đặc biệt)
        │── Xoá trùng lặp
        └── Validate stars (1–5)
        │
        ▼ clean DataFrame
[3] RAG Agent
        │── Embed reviews → ChromaDB
        │── Query theo 4 chủ đề
        └── Trả về top-k reviews liên quan
        │
        ├─────────────────┐
        ▼                 ▼
[4] Sentiment Agent   [5] Topic Agent
    positive %            food_quality
    negative %            service
    neutral %             price
    highlights            ambiance
        │                 │
        └────────┬────────┘
                 ▼
         Hallucination Checker
         (validate + auto-fix)
                 │
                 ▼
         [6] Report Agent
                 │── Overall score
                 │── Strengths
                 │── Weaknesses
                 │── Recommendations
                 └── Executive summary
                 │
                 ▼
         JSON Response
         → FastAPI → React UI
```

### Chi tiết từng Agent

#### 1. Data Collector Agent (`agents/data_collector.py`)
Thu thập reviews theo thứ tự ưu tiên:
- **Nguồn 1 – CSV Upload**: Nếu user upload file CSV có cột `text` và `stars`
- **Nguồn 2 – Yelp Dataset**: Tìm `business_id` trong `yelp_academic_dataset_business.json`, sau đó lấy reviews tương ứng trong `yelp_academic_dataset_review.json`
- **Nguồn 3 – Google Maps**: Dùng Playwright scrape reviews từ Google Maps

#### 2. Data Validator Agent (`agents/data_validator.py`)
Làm sạch dữ liệu theo 6 bước:
1. Validate cột bắt buộc (`text`, `stars`)
2. Clean text (null, rỗng, strip whitespace)
3. Lọc review quá ngắn (< 10 ký tự)
4. Cắt review quá dài (> 5000 ký tự)
5. Validate stars (1–5, loại bỏ giá trị ngoài khoảng)
6. Xoá duplicate và spam

#### 3. RAG Agent (`agents/rag_agent.py`)
- Embed toàn bộ reviews thành vector dùng `sentence-transformers` (model: `all-MiniLM-L6-v2`)
- Lưu vào **ChromaDB** (persistent local vector DB)
- Query 4 chủ đề với các từ khoá tiếng Anh tương ứng
- Trả về top-k reviews liên quan nhất cho mỗi chủ đề

#### 4. Sentiment Agent (`agents/sentiment_agent.py`)
- Gọi **Groq API** (Llama 3.3 70b) với toàn bộ clean reviews
- Phân loại: positive / negative / neutral (%)
- Trích xuất highlights tích cực và tiêu cực
- Output: JSON có `positive`, `negative`, `neutral`, `summary`, `highlights`

#### 5. Topic Agent (`agents/topic_agent.py`)
- Phân tích theo 4 chủ đề: `food_quality`, `service`, `price`, `ambiance`
- Với mỗi chủ đề: sentiment, score (1–5), mentions, keywords, summary
- Dùng reviews đã được RAG filter để tăng độ chính xác

#### 6. Hallucination Checker (`agents/hallucination_checker.py`)
Kiểm tra kết quả LLM:
- Tổng % sentiment = 100
- Score trong khoảng 1.0–5.0
- Sentiment hợp lệ (positive/negative/neutral)
- Keywords có trong reviews thực tế
- Auto-fix những gì có thể, báo lỗi những gì không thể

#### 7. Report Agent (`agents/report_agent.py`)
- Nhận kết quả từ Sentiment + Topic agent
- Gọi Groq API tạo báo cáo kinh doanh
- Output: overall score, strengths, weaknesses, recommendations, executive summary, priority action

#### 8. Manager Agent (`agents/manager_agent.py`)
- Điều phối toàn bộ 6 bước trên
- Xử lý lỗi từng bước, fallback khi RAG thất bại
- Tổng hợp metadata (nguồn dữ liệu, thời gian xử lý, validation stats)
- Entry point duy nhất: `run_analysis(business_name, ...)`

---

## Cấu trúc thư mục

```
COS30018-business-agent/
│
├── agents/
│   ├── __init__.py
│   ├── manager_agent.py         # Điều phối toàn bộ pipeline
│   ├── data_collector.py        # Thu thập reviews đa nguồn
│   ├── data_validator.py        # Làm sạch và validate
│   ├── rag_agent.py             # Vector search với ChromaDB
│   ├── sentiment_agent.py       # Phân tích cảm xúc
│   ├── topic_agent.py           # Phân tích chủ đề
│   ├── hallucination_checker.py # Kiểm tra kết quả LLM
│   └── report_agent.py          # Tạo báo cáo cuối
│
├── data/
│   ├── __init__.py
│   ├── yelp_loader.py           # Đọc Yelp Dataset
│   ├── google_scraper.py        # Playwright scrape Google Maps
│   ├── csv_handler.py           # Xử lý CSV upload
│   └── chroma_db/               # Vector DB (auto-generated, gitignored)
│
├── backend/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app
│   ├── routes.py                # API endpoints
│   └── models.py                # Pydantic data models
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── SearchBar.jsx
│   │   │   ├── FileUpload.jsx
│   │   │   ├── ReportCard.jsx
│   │   │   └── Charts.jsx
│   │   └── api/
│   │       └── index.js
│   └── package.json
│
├── evaluation/
│   ├── eda.ipynb                # Exploratory Data Analysis
│   └── eval.ipynb               # Đánh giá độ chính xác
│
├── config.py                    # Cấu hình toàn dự án
├── .env                         # API keys (gitignored)
├── .env.example                 # Template cho .env
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Công nghệ sử dụng

| Thành phần | Công nghệ |
|---|---|
| LLM | Groq API – Llama 3.3 70b Versatile |
| Multiagent Framework | CrewAI (Manager), Python modules (Agents) |
| Vector DB | ChromaDB |
| Embedding Model | sentence-transformers (all-MiniLM-L6-v2) |
| Web Scraping | Playwright (Chromium) |
| Backend | FastAPI + Uvicorn |
| Frontend | React + Vite |
| Data Processing | Pandas |
| LLM Bridge | LiteLLM |

---

## Yêu cầu hệ thống

- Python **3.10+**
- Node.js **18+** (cho React frontend)
- RAM tối thiểu **4GB** (do embedding model)
- Kết nối internet (cho Groq API và Google Maps scraping)
- Groq API key (miễn phí tại [console.groq.com](https://console.groq.com))

---

## Hướng dẫn cài đặt

### Bước 1 – Clone repository

```bash
git clone https://github.com/your-username/COS30018-business-agent.git
cd COS30018-business-agent
```

### Bước 2 – Tạo môi trường ảo Python

```bash
# Tạo môi trường ảo
python -m venv venv

# Kích hoạt (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Kích hoạt (Mac/Linux)
source venv/bin/activate
```

### Bước 3 – Cài thư viện Python

```bash
pip install -r requirements.txt
```

Nếu chưa có `requirements.txt`, cài thủ công:

```bash
pip install groq python-dotenv crewai fastapi uvicorn pydantic \
            pandas playwright chromadb sentence-transformers litellm
playwright install chromium
```

### Bước 4 – Cấu hình API key

Tạo file `.env` từ template:

```bash
cp .env.example .env
```

Mở file `.env` và điền API key:

```env
GROQ_API_KEY=your_groq_api_key_here
LLM_MODEL=llama-3.3-70b-versatile
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
AGENT_VERBOSE=true
MAX_REVIEWS_PER_RUN=100
LITELLM_DROP_PARAMS=True
```

> Lấy Groq API key miễn phí tại: https://console.groq.com

### Bước 5 – Tải Yelp Dataset (tuỳ chọn)

Nếu muốn dùng Yelp Dataset:

1. Vào https://www.kaggle.com/datasets/yelp-dataset/yelp-dataset
2. Tải về 2 file:
   - `yelp_academic_dataset_business.json`
   - `yelp_academic_dataset_review.json`
3. Đặt vào thư mục `data/`

> Nếu không có Yelp Dataset, hệ thống sẽ tự động chuyển sang Google Maps scraping.

### Bước 6 – Cài Node.js cho Frontend

```bash
cd frontend
npm install
cd ..
```

---

## Hướng dẫn chạy

### Chạy toàn bộ hệ thống

**Terminal 1 – Backend:**
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 – Frontend:**
```bash
cd frontend
npm run dev
```

Truy cập: **http://localhost:5173**

---

### Chạy từng phần riêng lẻ (để test)

**Test config:**
```bash
python config.py
```

**Test Yelp loader:**
```bash
python data/yelp_loader.py
```

**Test Google scraper:**
```bash
python data/google_scraper.py
```

**Test CSV handler:**
```bash
python data/csv_handler.py
```

**Test Sentiment Agent:**
```bash
python agents/sentiment_agent.py
```

**Test Topic Agent:**
```bash
python agents/topic_agent.py
```

**Test RAG Agent:**
```bash
python agents/rag_agent.py
```

**Test Hallucination Checker:**
```bash
python agents/hallucination_checker.py
```

**Test Data Validator:**
```bash
python agents/data_validator.py
```

**Test Report Agent:**
```bash
python agents/report_agent.py
```

**Test toàn bộ pipeline (Manager Agent):**
```bash
python agents/manager_agent.py
```

---

## API Endpoints

| Method | Endpoint | Mô tả |
|---|---|---|
| `POST` | `/api/analyze` | Phân tích theo tên quán |
| `POST` | `/api/upload` | Upload CSV reviews |
| `GET` | `/api/status/{job_id}` | Kiểm tra tiến độ |
| `GET` | `/api/report/{job_id}` | Lấy báo cáo |
| `GET` | `/api/health` | Kiểm tra server |

**Ví dụ gọi API:**

```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"business_name": "McDonald'\''s", "limit": 50}'
```

---

## Ví dụ output

```json
{
  "business_name": "Phở Thìn",
  "total_reviews": 45,
  "overall_score": 3.8,
  "sentiment_overview": {
    "positive": 65,
    "negative": 22,
    "neutral": 13
  },
  "strengths": [
    "Chất lượng món ăn được đánh giá cao, đặc biệt là phở",
    "Không gian quán sạch sẽ và thoáng mát",
    "Giá cả hợp lý so với chất lượng"
  ],
  "weaknesses": [
    "Thời gian chờ đợi lâu vào giờ cao điểm",
    "Thái độ phục vụ của một số nhân viên chưa tốt",
    "Chỗ đỗ xe hạn chế"
  ],
  "recommendations": [
    "Tăng cường nhân viên phục vụ vào giờ cao điểm (11h-13h, 18h-20h)",
    "Đào tạo kỹ năng giao tiếp và thái độ phục vụ cho nhân viên",
    "Cải thiện hệ thống đặt bàn trước để giảm thời gian chờ",
    "Hợp tác với bãi đỗ xe gần đó để giải quyết vấn đề parking"
  ],
  "executive_summary": "Phở Thìn có nền tảng tốt với chất lượng món ăn và không gian được khách hàng đánh giá cao. Điểm cần cải thiện ngay là tốc độ và thái độ phục vụ để nâng cao trải nghiệm tổng thể.",
  "priority_action": "Cải thiện tốc độ phục vụ và đào tạo thái độ nhân viên ngay trong tháng tới"
}
```

---




