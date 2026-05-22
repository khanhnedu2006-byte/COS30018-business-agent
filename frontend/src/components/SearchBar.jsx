import { useState } from "react";
import { Search, Map } from "lucide-react";

export default function SearchBar({ onSearch, onGoogleSearch }) {
  const [query, setQuery] = useState("");

  const handleYelp = (e) => {
    e.preventDefault();
    if (query.trim()) onSearch(query.trim());
  };

  const handleGoogle = (e) => {
    e.preventDefault();
    if (query.trim()) onGoogleSearch(query.trim());
  };

  return (
    <div className="search-container">
      <h2>🔍 Tìm kiếm nhà hàng</h2>
      <p className="search-desc">Nhập tên nhà hàng để tìm kiếm</p>

      <form className="search-form">
        <div className="search-input-wrap">
          <Search size={20} className="search-icon" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="VD: McDonald's, Starbucks, Phở Thìn..."
            className="search-input"
          />
        </div>

        <div className="search-buttons">
          <button
            onClick={handleYelp}
            className="btn-primary"
            disabled={!query.trim()}
          >
            🗂️ Tìm trong Yelp
          </button>
          <button
            onClick={handleGoogle}
            className="btn-secondary"
            disabled={!query.trim()}
          >
            <Map size={16} /> Google Maps
          </button>
        </div>
      </form>

      {/* Ghi chú */}
      <div className="search-notes">
        <div className="note-item">
          <span>🗂️ <strong>Yelp Dataset</strong></span>
          <span>Có sẵn trong dataset, chọn chi nhánh cụ thể</span>
        </div>
        <div className="note-item">
          <span>🗺️ <strong>Google Maps</strong></span>
          <span>Scrape trực tiếp, dùng khi không có trong Yelp</span>
        </div>
      </div>
    </div>
  );
}