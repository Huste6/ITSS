import { useAuth } from "../../contexts/AuthContext";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { toast } from "../ui/sonner";
import { Link, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import axiosInstance from "../../axios-config"; // Import axios instance
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "../ui/dialog";
type LoginFormProps = {
  onSuccess?: () => void;
  onRegister: () => void;
};

export function LoginForm({ onSuccess, onRegister }: LoginFormProps) {
  const navigate = useNavigate();
  const [isVisible, setIsVisible] = useState(false);
  const [error, setError] = useState(""); // State for error message
  const [username, setUsername] = useState(""); // State for username input
  const [password, setPassword] = useState(""); // State for password input
  const [showErrorModal, setShowErrorModal] = useState(false);
  const { login, isLoading } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!username || !password) {
      toast.error("Please enter both username and password");
      return;
    }
    try {
      // Gửi yêu cầu POST đến API /users/login
      console.log(
        "Logging in with username:",
        username,
        "and password:",
        password
      );
      const formData = new URLSearchParams();
      formData.append("username", username);
      formData.append("password", password);
      console.log("Form Data:", formData);
      const response = await axiosInstance.post("/users/login", formData, {
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
      });
      console.log("Response:", response);
      // Kiểm tra phản hồi từ server
      if (response.status === 200) {
        // Lưu token hoặc thực hiện hành động sau khi đăng nhập thành công
        localStorage.setItem("token", response.data.access_token);
        console.log("Login successful:", response.data);
        const user = await axiosInstance.get("/users/me");
        console.log("User data:", user.data);
        // Ví dụ: Lưu token vào localStorage
        const success = await login(username, password, user.data);
        if (success && onSuccess) {
          onSuccess();
        }
        // Điều hướng đến trang chính
        navigate("/dashboard");
      }
    } catch (error: any) {
      // Xử lý lỗi và hiển thị thông báo
      if (
        error.response &&
        error.response.data &&
        error.response.data.message
      ) {
        setError(error.response.data.message);
      } else {
        setError("An error occurred. Please try again.");
      }
      setShowErrorModal(true);
    }
  };
  const closeErrorModal = () => {
    setShowErrorModal(false);
    setError("");
  };
  return (
    <>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="username">username</Label>
          <Input
            id="username"
            type="username"
            placeholder="your.username@university.edu"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="password">Password</Label>
          <Input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        <Button type="submit" className="w-full" disabled={isLoading}>
          {isLoading ? "Signing in..." : "Sign in"}
        </Button>
        <div className="text-center mt-4">
          <p className="text-sm text-muted-foreground">
            Don't have an account?{" "}
            <button
              type="button"
              onClick={onRegister}
              className="text-primary hover:underline focus:outline-none"
            >
              Register
            </button>
          </p>
        </div>
      </form>
      {/* Error Popup Modal */}
      <Dialog open={showErrorModal} onOpenChange={closeErrorModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="text-red-600">Login Error</DialogTitle>
            <DialogDescription>{error}</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              type="button"
              onClick={closeErrorModal}
              className="bg-red-600 hover:bg-red-700"
            >
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
