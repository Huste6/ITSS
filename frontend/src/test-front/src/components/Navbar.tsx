
import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Menu, X, LayoutDashboard } from "lucide-react";
import { AuthModal } from "./auth/AuthModal";

export function Navbar() {
  const { user, isAuthenticated, logout } = useAuth();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const location = useLocation();
  
  // Don't show full navbar on dashboard pages
  if (location.pathname.startsWith("/dashboard")) {
    return null;
  }

  return (
    <>
      <nav className="bg-white dark:bg-gray-900 shadow-sm border-b px-4 sm:px-6 lg:px-8 py-4">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div className="flex items-center">
            <Link to="/" className="flex items-center">
              <img 
                src="/lovable-uploads/31ff4375-cb6c-469f-971c-49da226ae007.png" 
                alt="Academe Logo" 
                className="h-32 mr-2" 
              />
            </Link>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-1">
            <Link to="/" className="nav-link">Home</Link>
            <Link to="/about" className="nav-link">About</Link>
            <Link to="/contact" className="nav-link">Contact</Link>
            
            {isAuthenticated ? (
              <>
                <Button 
                  variant="ghost" 
                  className="nav-link"
                  onClick={() => window.location.href = "/dashboard"}
                >
                  <LayoutDashboard className="h-4 w-4 mr-2" />
                  Dashboard
                </Button>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" className="relative h-10 w-10 rounded-full">
                      <Avatar>
                        <AvatarImage src={user?.avatar} />
                        <AvatarFallback>{user?.name.charAt(0)}</AvatarFallback>
                      </Avatar>
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuLabel>
                      <div>
                        <p>{user?.name}</p>
                        <p className="text-xs text-muted-foreground">{user?.email}</p>
                      </div>
                    </DropdownMenuLabel>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem asChild>
                      <Link to="/dashboard">Dashboard</Link>
                    </DropdownMenuItem>
                    <DropdownMenuItem asChild>
                      <Link to="/dashboard/profile">Profile</Link>
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onClick={logout}>
                      Log Out
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </>
            ) : (
              <div className="flex space-x-2">
                <Button variant="ghost" onClick={() => setIsAuthModalOpen(true)}>
                  Log In
                </Button>
                <Button onClick={() => setIsAuthModalOpen(true)}>
                  Register
                </Button>
              </div>
            )}
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setIsMenuOpen(!isMenuOpen)}
            >
              {isMenuOpen ? <X /> : <Menu />}
            </Button>
          </div>
        </div>

        {/* Mobile menu */}
        {isMenuOpen && (
          <div className="md:hidden mt-2 pb-4 space-y-2">
            <Link 
              to="/" 
              className="block px-4 py-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800"
              onClick={() => setIsMenuOpen(false)}
            >
              Home
            </Link>
            <Link 
              to="/about" 
              className="block px-4 py-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800"
              onClick={() => setIsMenuOpen(false)}
            >
              About
            </Link>
            <Link 
              to="/contact" 
              className="block px-4 py-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800"
              onClick={() => setIsMenuOpen(false)}
            >
              Contact
            </Link>
            
            {isAuthenticated ? (
              <>
                <Link 
                  to="/dashboard" 
                  className="block px-4 py-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800"
                  onClick={() => setIsMenuOpen(false)}
                >
                  Dashboard
                </Link>
                <div 
                  className="block px-4 py-2 text-red-600 dark:text-red-400 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800"
                  onClick={() => {
                    logout();
                    setIsMenuOpen(false);
                  }}
                >
                  Log Out
                </div>
              </>
            ) : (
              <div className="flex flex-col space-y-2 px-4">
                <Button 
                  variant="outline" 
                  onClick={() => {
                    setIsAuthModalOpen(true);
                    setIsMenuOpen(false);
                  }}
                >
                  Log In
                </Button>
                <Button 
                  onClick={() => {
                    setIsAuthModalOpen(true);
                    setIsMenuOpen(false);
                  }}
                >
                  Register
                </Button>
              </div>
            )}
          </div>
        )}
      </nav>
      
      <AuthModal 
        isOpen={isAuthModalOpen} 
        onOpenChange={setIsAuthModalOpen} 
      />
    </>
  );
}
