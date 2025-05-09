import React from 'react';
import { Heart, Info, User, Settings, LogOut, Bell, LogIn } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface HeaderProps {
  onLogout?: () => void;
}

const Header: React.FC<HeaderProps> = ({ onLogout }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await logout();
      if (onLogout) {
        onLogout();
      }
      navigate('/');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  return (
    <header className="bg-white/90 dark:bg-slate-900/90 backdrop-blur-sm border-b border-slate-200 dark:border-slate-800 shadow-sm">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center">
            <h1 className="text-xl font-bold bg-gradient-to-r from-slate-600 to-blue-600 dark:from-slate-400 dark:to-blue-400 bg-clip-text text-transparent">
              SanoCare AI
            </h1>
          </div>
          
          <div className="flex items-center gap-4">
            {user ? (
              <>
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-slate-100 to-blue-100 dark:from-slate-800/30 dark:to-blue-800/30 flex items-center justify-center">
                    <User className="w-4 h-4 text-slate-600 dark:text-slate-400" />
                  </div>
                  <span className="text-sm font-medium text-slate-600 dark:text-slate-300">
                    {user.username}
                  </span>
                </div>
                <Button
                  onClick={handleLogout}
                  variant="outline"
                  className="border-slate-600 text-slate-600 hover:bg-slate-50 dark:border-slate-400 dark:text-slate-400 dark:hover:bg-slate-800/30"
                >
                  <LogOut className="w-4 h-4 mr-2" />
                  Logout
                </Button>
              </>
            ) : (
              <div className="flex gap-2">
                <Button
                  onClick={() => navigate('/login')}
                  variant="outline"
                  className="border-slate-600 text-slate-600 hover:bg-slate-50 dark:border-slate-400 dark:text-slate-400 dark:hover:bg-slate-800/30"
                >
                  Login
                </Button>
                <Button
                  onClick={() => navigate('/register')}
                  className="bg-gradient-to-r from-slate-600 to-blue-600 hover:from-slate-700 hover:to-blue-700 text-white"
                >
                  Register
                </Button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
