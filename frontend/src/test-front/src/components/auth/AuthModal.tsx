
import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { LoginForm } from "./LoginForm";
import { RegisterForm } from "./RegisterForm";

type AuthModalProps = {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  defaultTab?: "login" | "register";
};

export function AuthModal({ isOpen, onOpenChange, defaultTab = "login" }: AuthModalProps) {
  const [activeTab, setActiveTab] = useState<"login" | "register">(defaultTab);

  const handleSuccess = () => {
    onOpenChange(false);
  };

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle className="text-2xl text-center font-semibold text-academe-800 dark:text-academe-200">
            Welcome to Academe
          </DialogTitle>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as "login" | "register")} className="w-full">
          <TabsList className="grid grid-cols-2 w-full">
            <TabsTrigger value="login">Login</TabsTrigger>
            <TabsTrigger value="register">Register</TabsTrigger>
          </TabsList>
          <TabsContent value="login" className="mt-4">
            <LoginForm 
              onSuccess={handleSuccess}
              onRegister={() => setActiveTab("register")}
            />
          </TabsContent>
          <TabsContent value="register" className="mt-4">
            <RegisterForm 
              onSuccess={handleSuccess}
              onLogin={() => setActiveTab("login")}
            />
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
