
import React, { createContext, useContext, useState, ReactNode } from "react";
import { toast } from "@/components/ui/sonner";

type User = {
  id: string;
  name: string;
  email: string;
  role: "student" | "mentor" | "leader";
  avatar?: string;
};

type AuthContextType = {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<boolean>;
  register: (name: string, email: string, password: string, role: "student" | "mentor") => Promise<boolean>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    try {
      // Mock login - in a real app, this would call an API
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Simulate different user roles for demo purposes
      let role: "student" | "mentor" | "leader" = "student";
      if (email.includes("mentor")) {
        role = "mentor";
      } else if (email.includes("leader")) {
        role = "leader";
      }
      
      const user: User = {
        id: "user-" + Math.random().toString(36).substr(2, 9),
        name: email.split("@")[0],
        email,
        role,
        avatar: `https://ui-avatars.com/api/?name=${encodeURIComponent(email.split("@")[0])}&background=random`,
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

  const register = async (name: string, email: string, password: string, role: "student" | "mentor") => {
    setIsLoading(true);
    try {
      // Mock registration - in a real app, this would call an API
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const user: User = {
        id: "user-" + Math.random().toString(36).substr(2, 9),
        name,
        email,
        role,
        avatar: `https://ui-avatars.com/api/?name=${encodeURIComponent(name)}&background=random`,
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
