import axios from "axios";

const API = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000/api",
  timeout: 300000,
});

export const searchBusinesses = (businessName) =>
  API.post("/search", { business_name: businessName });

export const analyzeReviews = (businessName, businessId, useRag = true) =>
  API.post("/analyze", {
    business_name: businessName,
    business_id: businessId,
    use_rag: useRag,
  });

export const analyzeFromCSV = (businessName, csvPath) =>
  API.post("/analyze", {
    business_name: businessName,
    csv_path: csvPath,
    business_id: null,
    use_rag: true,
  });

export const analyzeByGoogle = (businessName) =>
  API.post("/analyze/google", { business_name: businessName });

export const uploadCSV = (file) => {
  const formData = new FormData();
  formData.append("file", file);
  return API.post("/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
};

export const healthCheck = () => API.get("/health");