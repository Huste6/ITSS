
import { useState, ReactNode } from "react";
import { useAuth } from "../../contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Menu, X } from "lucide-react";
import { useIsMobile } from "@/hooks/use-mobile";
import { Sidebar } from "./Sidebar";

type DashboardLayoutProps = {
  children: ReactNode;
};

export function DashboardLayout({ children }: DashboardLayoutProps) {
  const { user } = useAuth();
  const isMobile = useIsMobile();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  if (!user) {
    return null;
  }

  const closeSidebarIfMobile = () => {
    if (isMobile) {
      setSidebarOpen(false);
    }
  };

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Mobile sidebar toggle */}
      <Button 
        variant="ghost" 
        size="icon" 
        className="fixed top-4 left-4 z-50 md:hidden"
        onClick={() => setSidebarOpen(!sidebarOpen)}
      >
        {sidebarOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
      </Button>

      {/* Sidebar backdrop for mobile */}
      {isMobile && sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40"
          onClick={() => setSidebarOpen(false)}
        ></div>
      )}

      {/* Sidebar */}
      <Sidebar 
        sidebarOpen={sidebarOpen}
        closeSidebarIfMobile={closeSidebarIfMobile}
      />

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <div className="container py-4 md:py-6 px-4 md:px-6">
          {children}
        </div>
      </main>
    </div>
  );
}
