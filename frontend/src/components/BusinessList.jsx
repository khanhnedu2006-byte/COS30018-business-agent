import { Building2, ArrowLeft, Star } from "lucide-react";

const RELIABILITY_COLOR = {
  "🟢 Cao": "#22c55e",
  "🟡 Trung bình": "#eab308",
  "🟠 Thấp": "#f97316",
  "🔴 Rất thấp": "#ef4444",
};

export default function BusinessList({ businesses, onSelect, onBack }) {
  return (
    <div className="biz-list-container">
      <div className="biz-list-header">
        <button className="btn-back" onClick={onBack}>
          <ArrowLeft size={16} /> Quay lại
        </button>
        <h2>Chọn chi nhánh ({businesses.length} kết quả)</h2>
        <p>Sắp xếp theo số lượng reviews — chọn chi nhánh có độ tin cậy cao</p>
      </div>

      <div className="biz-list">
        {businesses.map((biz) => (
          <div
            key={biz.business_id}
            className="biz-card"
            onClick={() => onSelect(biz)}
          >
            <div className="biz-card-left">
              <Building2 size={20} color="#6366f1" />
              <div>
                <h3>{biz.name}</h3>
                <p className="biz-address">
                  {biz.address}, {biz.city}, {biz.state}
                </p>
                <p className="biz-categories">{biz.categories}</p>
              </div>
            </div>

            <div className="biz-card-right">
              <div className="biz-stars">
                <Star size={14} fill="#fbbf24" color="#fbbf24" />
                <span>{biz.stars}</span>
              </div>
              <div className="biz-reviews">{biz.review_count} reviews</div>
              <div
                className="biz-reliability"
                style={{ color: RELIABILITY_COLOR[biz.reliability] || "#888" }}
              >
                {biz.reliability}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}