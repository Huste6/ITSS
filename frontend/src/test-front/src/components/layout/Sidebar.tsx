
import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";
import { SidebarNavItem } from "./SidebarNavItem";
import { UserMenu } from "./UserMenu";
import { 
  Home, 
  User, 
  FolderKanban, 
  Users, 
  ClipboardList, 
  FileText, 
  Settings 
} from "lucide-react";
import { cn } from "@/lib/utils";

type SidebarProps = {
  sidebarOpen: boolean;
  closeSidebarIfMobile: () => void;
};

export const Sidebar = ({ sidebarOpen, closeSidebarIfMobile }: SidebarProps) => {
  const { user } = useAuth();
  const location = useLocation();

  if (!user) {
    return null;
  }

  const sidebarItems = [
    { 
      icon: Home, 
      label: "Dashboard", 
      href: "/dashboard" 
    },
    { 
      icon: FolderKanban, 
      label: "Projects", 
      href: "/dashboard/projects" 
    },
    { 
      icon: Users, 
      label: "Groups", 
      href: "/dashboard/groups" 
    },
    { 
      icon: ClipboardList, 
      label: "Tasks", 
      href: "/dashboard/tasks" 
    },
    { 
      icon: FileText, 
      label: "Reports", 
      href: "/dashboard/reports", 
      hidden: user.role === "student" // Only hide for students
    },
    { 
      icon: User, 
      label: "Profile", 
      href: "/dashboard/profile" 
    },
    { 
      icon: Settings, 
      label: "Settings", 
      href: "/dashboard/settings" 
    },
  ];

  return (
    <div
      className={cn(
        "fixed inset-y-0 left-0 z-50 w-64 bg-white dark:bg-gray-900 border-r transform transition-transform duration-200 ease-in-out md:translate-x-0 md:static md:z-0",
        sidebarOpen ? "translate-x-0" : "-translate-x-full"
      )}
    >
      {/* Logo & user info */}
      <div className="p-4 border-b">
        <Link to="/" className="flex items-center mb-4">
          <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-academe-500 to-academe-700">
            Academe
          </span>
        </Link>
        
        <UserMenu />
      </div>

      {/* Navigation */}
      <nav className="p-4 space-y-1">
        {sidebarItems
          .filter(item => !item.hidden)
          .map(item => (
            <SidebarNavItem
              key={item.href}
              icon={item.icon}
              label={item.label}
              href={item.href}
              active={location.pathname === item.href}
              onClick={closeSidebarIfMobile}
            />
          ))
        }
      </nav>
    </div>
  );
};
