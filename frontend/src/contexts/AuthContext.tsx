import React, { createContext, useContext, useState, ReactNode } from "react";
import { toast } from "../components/ui/sonner";

type User = {
  id: string;
  name: string;
  email: string;
  role: string;
  avatar?: string;
  token?: string;
  groupId?: Record<string, any>;
};

type AuthContextType = {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string, data: any) => Promise<boolean>;
  register: (
    name: string,
    email: string,
    password: string,
    role: "student" | "mentor"
  ) => Promise<boolean>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const login = async (email: string, password: string, data: any) => {
    setIsLoading(true);
    try {
      // Mock login - in a real app, this would call an API
      await new Promise((resolve) => setTimeout(resolve, 1000));
      console.log(email, password, data.role);
      const role = data.role;
      const user: User = {
        id: data._id,
        name: data.ho_ten,
        email,
        role,
        token: data.access_token,
        avatar: `https://ui-avatars.com/api/?name=${encodeURIComponent(
          data.Ten[0]
        )}&background=random`,
        groupId: data.group_id,
      };

      setUser(user);
      localStorage.setItem("academe-user", JSON.stringify(user));
      toast.success("Login successful!");
      setIsLoading(false);
      return true;
    } catch (error) {
      toast.error("Failed to login. Please try again.");
      setIsLoading(false);
      return false;
    }
  };

  const register = async (
    name: string,
    email: string,
    password: string,
    role: "student" | "mentor"
  ) => {
    setIsLoading(true);
    try {
      // Mock registration - in a real app, this would call an API
      await new Promise((resolve) => setTimeout(resolve, 1000));

      const user: User = {
        id: "user-" + Math.random().toString(36).substr(2, 9),
        name,
        email,
        role,
        avatar: `https://ui-avatars.com/api/?name=${encodeURIComponent(
          name
        )}&background=random`,
        groupId: { default: "default-group-id" }, // Replace "default-group-id" with the appropriate value
      };

      setUser(user);
      localStorage.setItem("academe-user", JSON.stringify(user));
      toast.success("Registration successful!");
      setIsLoading(false);
      return true;
    } catch (error) {
      toast.error("Failed to register. Please try again.");
      setIsLoading(false);
      return false;
    }
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem("academe-user");
    toast.success("Logged out successfully");
  };

  React.useEffect(() => {
    // Check for saved user data on component mount
    const savedUser = localStorage.getItem("academe-user");
    if (savedUser) {
      setUser(JSON.parse(savedUser));
    }
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
