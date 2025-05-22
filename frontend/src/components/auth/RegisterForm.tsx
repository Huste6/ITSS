import { useState } from "react";
import { useAuth } from "../../contexts/AuthContext";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { RadioGroup, RadioGroupItem } from "../ui/radio-group";
import { toast } from "../ui/sonner";
import axiosInstance from "../../axios-config";
type RegisterFormProps = {
  onSuccess?: () => void;
  onLogin: () => void;
};

export function RegisterForm({ onSuccess, onLogin }: RegisterFormProps) {
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [role, setRole] = useState<"student" | "mentor">("student");
  const { register, isLoading } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!firstName || !lastName || !email || !password || !confirmPassword) {
      toast.error("Please fill in all fields");
      return;
    }

    if (password !== confirmPassword) {
      toast.error("Passwords do not match");
      return;
    }
    try {
      console.log(firstName, lastName, email, password, role);
      const response = await axiosInstance.post("/users/register", {
        HoDem: firstName,
        Ten: lastName,
        email,
        password,
        role,
      });
      if (response.status === 200) {
        // Lưu token hoặc thực hiện hành động sau khi đăng nhập thành công
        console.log("Login successful:", response.data);
        // Ví dụ: Lưu token vào localStorage
        localStorage.setItem("token", response.data.token);
        toast.success("Registration successful!");
        setTimeout(() => {
          onLogin();
        }, 1500);
      }
    } catch (error: any) {
      toast.error(
        error.response?.data?.message || "An error occurred during registration"
      );
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="name">Họ Đệm </Label>
        <Input
          id="name"
          placeholder="Nguyen ngoc"
          value={firstName}
          onChange={(e) => setFirstName(e.target.value)}
          required
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="name">Tên</Label>
        <Input
          id="name"
          placeholder="Quan"
          value={lastName}
          onChange={(e) => setLastName(e.target.value)}
          required
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="email">Academic Email</Label>
        <Input
          id="email"
          type="email"
          placeholder="your.email@university.edu"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
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
      <div className="space-y-2">
        <Label htmlFor="confirmPassword">Confirm Password</Label>
        <Input
          id="confirmPassword"
          type="password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          required
        />
      </div>

      <div className="space-y-2">
        <Label>I am a:</Label>
        <RadioGroup
          value={role}
          onValueChange={(value) => setRole(value as "student" | "mentor")}
          className="flex space-x-4"
        >
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="student" id="student" />
            <Label htmlFor="student">Student</Label>
          </div>
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="mentor" id="mentor" />
            <Label htmlFor="mentor">Mentor</Label>
          </div>
        </RadioGroup>
      </div>

      <Button type="submit" className="w-full" disabled={isLoading}>
        {isLoading ? "Creating account..." : "Create account"}
      </Button>
      <div className="text-center mt-4">
        <p className="text-sm text-muted-foreground">
          Already have an account?{" "}
          <button
            type="button"
            onClick={onLogin}
            className="text-primary hover:underline focus:outline-none"
          >
            Sign in
          </button>
        </p>
      </div>
    </form>
  );
}
