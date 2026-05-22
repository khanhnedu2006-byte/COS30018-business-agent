import { useState } from "react";
import SearchBar from "./components/SearchBar";
import BusinessList from "./components/BusinessList";
import FileUpload from "./components/FileUpload";
import ReportCard from "./components/ReportCard";
import {
  searchBusinesses,
  analyzeReviews,
  analyzeFromCSV,
  uploadCSV,
  analyzeByGoogle,
} from "./api";
import { BarChart3, ArrowRight, Star, TrendingUp, Shield } from "lucide-react";
import "./App.css";

export default function App() {
  const [page, setPage] = useState("landing"); // landing | app
  const [step, setStep] = useState("search");
  const [businesses, setBusinesses] = useState([]);
  const [report, setReport] = useState(null);
  const [error, setError] = useState(null);
  const [loadingMsg, setLoadingMsg] = useState("");

  const handleSearch = async (businessName) => {
    setError(null);
    setStep("loading");
    setLoadingMsg("Đang tìm kiếm chi nhánh trong Yelp Dataset...");
    try {
      const res = await searchBusinesses(businessName);
      const data = res.data;
      if (!data.businesses || data.businesses.length === 0) {
        setError("Không tìm thấy trong Yelp Dataset");
        setStep("search");
        return;
      }
      setBusinesses(data.businesses);
      setStep("select");
    } catch (err) {
      setError("Lỗi kết nối đến server");
      setStep("search");
    }
  };

  const handleGoogleSearch = async (businessName) => {
    setError(null);
    setStep("loading");
    setLoadingMsg(`Đang scrape Google Maps: "${businessName}"...`);
    try {
      const res = await analyzeByGoogle(businessName);
      setReport(res.data);
      setStep("result");
    } catch (err) {
      setError(err.response?.data?.detail || "Không tìm thấy trên Google Maps");
      setStep("search");
    }
  };

  const handleSelectBusiness = async (biz) => {
    setError(null);
    setStep("loading");
    setLoadingMsg(`Đang phân tích "${biz.name}" tại ${biz.city}...`);
    try {
      const res = await analyzeReviews(biz.name, biz.business_id);
      setReport(res.data);
      setStep("result");
    } catch (err) {
      setError(err.response?.data?.detail || "Lỗi khi phân tích reviews");
      setStep("select");
    }
  };

  const handleCSVUpload = async (file, businessName) => {
    setError(null);
    setStep("loading");
    setLoadingMsg("Đang upload và phân tích CSV...");
    try {
      const uploadRes = await uploadCSV(file);
      const filePath = uploadRes.data.file_path;
      const analyzeRes = await analyzeFromCSV(businessName, filePath);
      setReport(analyzeRes.data);
      setStep("result");
    } catch (err) {
      setError(err.response?.data?.detail || "Lỗi khi xử lý CSV");
      setStep("search");
    }
  };

  const handleReset = () => {
    setStep("search");
    setBusinesses([]);
    setReport(null);
    setError(null);
  };

  const goToApp = () => {
    setPage("app");
    setStep("search");
  };

  // ── LANDING PAGE ──────────────────────────────────────────────────
  if (page === "landing") {
    return (
      <div className="landing">
        {/* Navbar */}
        <nav className="landing-nav">
          <div className="nav-logo">
            <BarChart3 size={24} color="white" />
            <span>Business Improvement Agent</span>
          </div>
          <div className="nav-badges">
            <span className="badge">🤖 Multiagent AI</span>
            <span className="badge">⚡ Groq LLM</span>
            <span className="badge">🔍 RAG</span>
          </div>
        </nav>

        {/* Hero Section */}
        <section className="landing-hero">
          <div className="landing-hero-content">
            <div className="hero-tag">COS30018 – Intelligent Systems</div>
            <h1>
              Hiểu khách hàng của bạn,<br />
              cải thiện kinh doanh<br />
              <span className="hero-highlight">ngay hôm nay</span>
            </h1>
            <p>
              Hệ thống AI đa tác nhân tự động thu thập, phân tích reviews nhà hàng
              từ nhiều nguồn và tạo báo cáo cải thiện kinh doanh chi tiết.
            </p>
            <div className="hero-actions">
              <button className="btn-start" onClick={goToApp}>
                Bắt đầu ngay <ArrowRight size={18} />
              </button>
              <span className="hero-note">Miễn phí · Không cần đăng ký</span>
            </div>
          </div>

          {/* Steps */}
          <div className="landing-steps">
            {[
              { num: "1", label: "Nhập tên quán", icon: "🔍" },
              { num: "2", label: "AI thu thập reviews", icon: "🤖" },
              { num: "3", label: "Phân tích sentiment", icon: "💬" },
              { num: "4", label: "Nhận báo cáo", icon: "📊" },
            ].map((s, i) => (
              <div key={i} className="landing-step-wrap">
                <div className="landing-step">
                  <span className="step-icon">{s.icon}</span>
                  <div className="step-num">{s.num}</div>
                  <p>{s.label}</p>
                </div>
                {i < 3 && <div className="step-connector">→</div>}
              </div>
            ))}
          </div>
        </section>

        {/* Features */}
        <section className="landing-features">
          <div className="features-grid">
            <div className="feature-card">
              <TrendingUp size={28} color="#6366f1" />
              <h3>Phân tích đa chiều</h3>
              <p>Sentiment, topic analysis theo 4 chủ đề: đồ ăn, dịch vụ, giá cả, không gian</p>
            </div>
            <div className="feature-card">
              <Shield size={28} color="#6366f1" />
              <h3>Hallucination Checker</h3>
              <p>Tự động kiểm tra và sửa lỗi kết quả AI, đảm bảo độ chính xác cao</p>
            </div>
            <div className="feature-card">
              <Star size={28} color="#6366f1" />
              <h3>Đa nguồn dữ liệu</h3>
              <p>Yelp Dataset, Google Maps scraping, hoặc upload CSV reviews của riêng bạn</p>
            </div>
            <div className="feature-card">
              <BarChart3 size={28} color="#6366f1" />
              <h3>RAG Technology</h3>
              <p>Vector search tìm reviews liên quan nhất theo từng chủ đề phân tích</p>
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="landing-cta">
          <h2>Sẵn sàng phân tích nhà hàng của bạn?</h2>
          <p>Chỉ cần nhập tên quán — AI sẽ lo phần còn lại</p>
          <button className="btn-start" onClick={goToApp}>
            Bắt đầu ngay <ArrowRight size={18} />
          </button>
        </section>

        {/* Footer */}
        <footer className="landing-footer">
          <p>COS30018 – Intelligent Systems | Swinburne University of Technology Vietnam</p>
        </footer>
      </div>
    );
  }

  // ── APP PAGE ──────────────────────────────────────────────────────
  return (
    <div className="app">
      {/* App Header */}
      <header className="header">
        <div className="header-content">
          <div
            className="header-logo"
            onClick={() => { setPage("landing"); handleReset(); }}
            style={{ cursor: "pointer" }}
          >
            <BarChart3 size={28} color="white" />
            <div>
              <h1>Business Improvement Agent</h1>
              <p className="header-sub">
                Powered by Groq + Llama 3.3 70b
              </p>
            </div>
          </div>
          <div className="header-badges">
            <span className="badge">🤖 Multiagent AI</span>
            <span className="badge">⚡ Groq LLM</span>
            <span className="badge">🔍 RAG</span>
          </div>
        </div>
      </header>

      <main className="main">
        {error && (
          <div className="error-banner">
            ⚠️ {error}
            <button onClick={() => setError(null)}>✕</button>
          </div>
        )}

        {step === "search" && (
          <div className="section">
            <SearchBar
              onSearch={handleSearch}
              onGoogleSearch={handleGoogleSearch}
            />
            <div className="divider"><span>hoặc</span></div>
            <FileUpload onUpload={handleCSVUpload} />
          </div>
        )}

        {step === "loading" && (
          <div className="loading-screen">
            <div className="spinner" />
            <p>{loadingMsg}</p>
            <small>Quá trình có thể mất 1-3 phút...</small>
          </div>
        )}

        {step === "select" && (
          <BusinessList
            businesses={businesses}
            onSelect={handleSelectBusiness}
            onBack={handleReset}
          />
        )}

        {step === "result" && report && (
          <ReportCard report={report} onReset={handleReset} />
        )}
      </main>
    </div>
  );
}