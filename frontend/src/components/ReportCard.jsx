import { RotateCcw, TrendingUp, TrendingDown, Lightbulb, Star } from "lucide-react";
import {
  PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, BarChart, Bar, XAxis, YAxis, CartesianGrid,
} from "recharts";

const COLORS = ["#22c55e", "#ef4444", "#94a3b8"];

export default function ReportCard({ report, onReset }) {
  const sentimentData = [
    { name: "Positive", value: report.sentiment_overview?.positive || 0 },
    { name: "Negative", value: report.sentiment_overview?.negative || 0 },
    { name: "Neutral",  value: report.sentiment_overview?.neutral  || 0 },
  ];

  const topicDetail = report.metadata?.topic_detail || {};
  const topics = ["food_quality", "service", "price", "ambiance"];
  const topicLabels = {
    food_quality: "Đồ ăn",
    service: "Dịch vụ",
    price: "Giá cả",
    ambiance: "Không gian",
  };

  const radarData = topics.map((t) => ({
    topic: topicLabels[t],
    score: topicDetail[t]?.score || 0,
  }));

  const barData = topics.map((t) => ({
    name: topicLabels[t],
    mentions: topicDetail[t]?.mentions || 0,
    score: topicDetail[t]?.score || 0,
  }));

  return (
    <div className="report-container">
      {/* Header */}
      <div className="report-header">
        <div>
          <h2>{report.business_name}</h2>
          <p>{report.total_reviews} reviews phân tích</p>
          {report.metadata?.validation_stats && (
            <p className="reliability-note">
              {report.metadata.validation_stats.kept_ratio}% reviews hợp lệ
            </p>
          )}
        </div>
        <div className="report-score">
          <div className="score-circle">
            <span>{report.overall_score}</span>
            <small>/5.0</small>
          </div>
          <p>Overall Score</p>
        </div>
        <button className="btn-back" onClick={onReset}>
          <RotateCcw size={16} /> Phân tích lại
        </button>
      </div>

      {/* Executive Summary */}
      <div className="summary-box">
        <h3>📋 Tóm tắt</h3>
        <p>{report.executive_summary}</p>
        <div className="priority-action">
          ⚡ <strong>Ưu tiên ngay:</strong> {report.priority_action}
        </div>
      </div>

      {/* Charts Row */}
      <div className="charts-row">
        {/* Pie Chart - Sentiment */}
        <div className="chart-card">
          <h3>💬 Sentiment</h3>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie
                data={sentimentData}
                cx="50%"
                cy="50%"
                innerRadius={55}
                outerRadius={80}
                dataKey="value"
                label={({ name, value }) => `${name}: ${value}%`}
              >
                {sentimentData.map((_, i) => (
                  <Cell key={i} fill={COLORS[i]} />
                ))}
              </Pie>
              <Tooltip formatter={(v) => `${v}%`} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Radar Chart - Topics */}
        <div className="chart-card">
          <h3>🏷️ Chủ đề</h3>
          <ResponsiveContainer width="100%" height={220}>
            <RadarChart data={radarData}>
              <PolarGrid />
              <PolarAngleAxis dataKey="topic" />
              <Radar
                name="Score"
                dataKey="score"
                stroke="#6366f1"
                fill="#6366f1"
                fillOpacity={0.3}
              />
              <Tooltip />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        {/* Bar Chart - Mentions */}
        <div className="chart-card">
          <h3>📊 Số lần đề cập</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={barData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="mentions" fill="#6366f1" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Strengths & Weaknesses */}
      <div className="sw-row">
        <div className="sw-card strengths">
          <h3><TrendingUp size={18} /> Điểm mạnh</h3>
          <ul>
            {report.strengths?.map((s, i) => (
              <li key={i}>✅ {s}</li>
            ))}
          </ul>
        </div>
        <div className="sw-card weaknesses">
          <h3><TrendingDown size={18} /> Điểm yếu</h3>
          <ul>
            {report.weaknesses?.map((w, i) => (
              <li key={i}>❌ {w}</li>
            ))}
          </ul>
        </div>
      </div>

      {/* Recommendations */}
      <div className="recommendations">
        <h3><Lightbulb size={18} /> Đề xuất cải thiện</h3>
        <div className="rec-grid">
          {report.recommendations?.map((r, i) => (
            <div key={i} className="rec-card">
              <span className="rec-num">{i + 1}</span>
              <p>{r}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Topic Detail */}
      <div className="topic-detail">
        <h3>🔍 Chi tiết từng chủ đề</h3>
        <div className="topic-grid">
          {topics.map((t) => {
            const data = topicDetail[t];
            if (!data || typeof data !== "object") return null;
            const sentColor =
              data.sentiment === "positive" ? "#22c55e" :
              data.sentiment === "negative" ? "#ef4444" : "#94a3b8";
            return (
              <div key={t} className="topic-card">
                <div className="topic-header">
                  <h4>{topicLabels[t]}</h4>
                  <span className="topic-score">
                    <Star size={12} fill="#fbbf24" color="#fbbf24" />
                    {data.score}/5
                  </span>
                </div>
                <div className="topic-sentiment" style={{ color: sentColor }}>
                  {data.sentiment}
                </div>
                <p className="topic-summary">{data.summary}</p>
                <div className="topic-keywords">
                  {data.keywords?.map((kw, i) => (
                    <span key={i} className="keyword-tag">{kw}</span>
                  ))}
                </div>
                <p className="topic-mentions">{data.mentions} lần đề cập</p>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}