import { StrictMode } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import * as ReactDOM from "react-dom/client";
import { App } from "./pages/app";
import Register from "./components/Auth/Register";
import ForgotPassword from "./components/Auth/ForgotPassword";
import Login from "./components/home/Login";
import Dashboard from "./pages/dashboard";
import Index from "./pages/Index";
import { AuthProvider } from "./contexts/AuthContext";
import { Toaster } from "./components/ui/toaster";
import { Toaster as Sonner } from "./components/ui/sonner";
import { TooltipProvider } from "./components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import "./styles.css";
import Projects from "./pages/Projects";
import Groups from "./pages/Groups";
import Tasks from "./pages/Tasks";
import Profile from "./pages/Profile";
import Settings from "./pages/Settings";
import ProjectDetail from "./pages/ProjectDetail";
import GroupDetail from "./pages/GroupDetail";
const root = ReactDOM.createRoot(
  document.getElementById("root") as HTMLElement
);
const queryClient = new QueryClient();
root.render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <AuthProvider>
          <Toaster />
          <Sonner />
          <BrowserRouter>
            <Routes>
              <Route path="/" element={<Index />} />
              <Route path="/register" element={<Register />}></Route>
              <Route
                path="/forgot-password"
                element={<ForgotPassword />}
              ></Route>
              <Route path="/login" element={<Login />}></Route>
              <Route path="/dashboard" element={<Dashboard />}></Route>
              <Route path="/dashboard/projects" element={<Projects />} />
              <Route
                path="/dashboard/projects/:projectId"
                element={<ProjectDetail />}
              />
              <Route path="/dashboard/groups" element={<Groups />} />
              <Route path="/dashboard/groups/:id" element={<GroupDetail />} />
              <Route path="/dashboard/tasks" element={<Tasks />} />
              <Route path="/dashboard/reports" element={<Dashboard />} />
              <Route path="/dashboard/profile" element={<Profile />} />
              <Route path="/dashboard/settings" element={<Settings />} />
            </Routes>
          </BrowserRouter>
        </AuthProvider>
      </TooltipProvider>
    </QueryClientProvider>
  </StrictMode>
);
