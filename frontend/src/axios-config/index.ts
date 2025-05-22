import axios from "axios";

const axiosInstance = axios.create({
  baseURL: "http://localhost:8000", // Thay bằng URL API của bạn
  withCredentials: true, // Cho phép gửi cookie cùng với yêu cầu
  headers: {
    "Content-Type": "application/json",
  },
});
axiosInstance.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token"); // Lấy token từ localStorage hoặc nơi lưu trữ khác
    if (token) {
      config.headers.Authorization = `Bearer ${token}`; // Thêm token vào header
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);
export default axiosInstance;