
import { ReactElement } from "react";
import { Link, useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";

type SidebarNavItemProps = {
  icon: React.ElementType;
  label: string;
  href: string;
  active?: boolean;
  onClick?: () => void;
};

export const SidebarNavItem = ({ 
  icon: Icon, 
  label, 
  href,
  active,
  onClick 
}: SidebarNavItemProps): ReactElement => {
  const location = useLocation();
  
  // If active prop is not provided, determine active state based on current location
  const isActive = active !== undefined 
    ? active 
    : location.pathname === href || location.pathname.startsWith(`${href}/`);
  
  return (
    <Link
      to={href}
      className={cn(
        "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-all hover:bg-academe-100 dark:hover:bg-academe-900/20",
        isActive && "bg-academe-100 text-academe-700 dark:bg-academe-900/20 dark:text-academe-300"
      )}
      onClick={onClick}
    >
      <Icon className="h-4 w-4" />
      <span>{label}</span>
    </Link>
  );
};
