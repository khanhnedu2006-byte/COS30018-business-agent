import { useState } from "react";
import { useDropzone } from "react-dropzone";
import { Upload } from "lucide-react";

export default function FileUpload({ onUpload }) {
  const [file, setFile] = useState(null);
  const [bizName, setBizName] = useState("");

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: { "text/csv": [".csv"] },
    maxFiles: 1,
    onDrop: (files) => setFile(files[0]),
  });

  const handleSubmit = () => {
    if (file && bizName.trim()) {
      onUpload(file, bizName.trim());
    }
  };

  return (
    <div className="upload-container">
      <h2>📂 Upload CSV Reviews</h2>
      <p className="upload-desc">
        File CSV cần có cột: <code>text</code> và <code>stars</code>
      </p>

      <div {...getRootProps()} className={`dropzone ${isDragActive ? "active" : ""}`}>
        <input {...getInputProps()} />
        <Upload size={32} color="#6366f1" />
        {file ? (
          <p className="file-name">✅ {file.name}</p>
        ) : (
          <p>Kéo thả file CSV vào đây hoặc click để chọn</p>
        )}
      </div>

      {file && (
        <div className="upload-actions">
          <input
            type="text"
            placeholder="Tên nhà hàng..."
            value={bizName}
            onChange={(e) => setBizName(e.target.value)}
            className="search-input"
          />
          <button
            className="btn-primary"
            onClick={handleSubmit}
            disabled={!bizName.trim()}
          >
            Phân tích CSV
          </button>
        </div>
      )}
    </div>
  );
}