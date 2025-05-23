import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { MessageSquare, Heart } from 'lucide-react';
import Message from './Message';
import ChatInput from './ChatInput';
import Header from './Header';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: Date;
}

const Chat: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const { user, logout, isLoading } = useAuth();
  const navigate = useNavigate();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  // Only load conversations when user is logged in
  useEffect(() => {
    const loadConversations = async () => {
      if (!user) {
        setMessages([]);
        return;
      }
      
      try {
        setIsLoadingMessages(true);
        const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:5000'}/conversations`, {
          credentials: 'include'
        });
        if (response.ok) {
          const data = await response.json();
          if (data.success && data.conversations) {
            const formattedMessages = data.conversations.flatMap((conv: any) => [
              {
                role: 'user',
                content: conv.message,
                timestamp: new Date(conv.timestamp)
              },
              {
                role: 'assistant',
                content: conv.response,
                timestamp: new Date(conv.timestamp)
              }
            ]);
            setMessages(formattedMessages);
          }
        }
      } catch (error) {
        console.error('Failed to load conversations:', error);
      } finally {
        setIsLoadingMessages(false);
      }
    };

    loadConversations();
  }, [user]);

  const handleSendMessage = async (message: string) => {
    if (!message.trim()) return;

    // Add user message to local state
    const userMessage: Message = { 
      role: 'user', 
      content: message,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);
    setIsTyping(true);

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:5000'}/get`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ msg: message }),
      });

      const data = await response.json();

      if (data.success) {
        const assistantMessage: Message = { 
          role: 'assistant', 
          content: data.response,
          timestamp: new Date(data.timestamp)
        };
        setMessages(prev => [...prev, assistantMessage]);
      } else {
        console.error('Failed to get response:', data.error);
      }
    } catch (error) {
      console.error('Error sending message:', error);
    } finally {
      setIsTyping(false);
    }
  };

  const handleLogout = async () => {
    try {
      await logout();
      setMessages([]); // Clear messages on logout
      navigate('/');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gradient-to-b from-slate-50 to-blue-50 dark:from-slate-900 dark:to-slate-800">
      <Header onLogout={handleLogout} />

      {/* Chat Area */}
      <div className="flex-1 overflow-hidden">
        <ScrollArea className="h-full p-4">
          {isLoading || isLoadingMessages ? (
            <div className="h-full flex items-center justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-600"></div>
            </div>
          ) : messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center p-4">
              <div className="w-24 h-24 mb-6 rounded-full bg-slate-100/50 dark:bg-slate-800/50 flex items-center justify-center">
                <MessageSquare className="w-12 h-12 text-slate-600 dark:text-slate-400" />
              </div>
              <h3 className="text-2xl font-semibold mb-3 text-slate-900 dark:text-white">
                Welcome to Your Health Assistant
              </h3>
              <p className="text-slate-600 dark:text-slate-300 max-w-md text-lg mb-6">
                Ask me any health-related questions, and I'll provide helpful information and guidance based on the latest medical knowledge.
              </p>
              {!user && (
                <div className="flex flex-col items-center gap-4">
                  <p className="text-sm text-slate-500 dark:text-slate-400">
                    Sign in to save your conversation history
                  </p>
                  <div className="flex gap-2">
                    <Button
                      onClick={() => navigate('/login')}
                      className="bg-gradient-to-r from-slate-600 to-blue-600 hover:from-slate-700 hover:to-blue-700 text-white"
                    >
                      Sign In
                    </Button>
                    <Button
                      onClick={() => navigate('/register')}
                      variant="outline"
                      className="border-slate-600 text-slate-600 hover:bg-slate-50 dark:border-slate-400 dark:text-slate-400 dark:hover:bg-slate-800/30"
                    >
                      Create Account
                    </Button>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-4">
              {messages.map((message, index) => (
                <Message 
                  key={index} 
                  message={message} 
                  isLatest={index === messages.length - 1} 
                />
              ))}
              {isTyping && (
                <div className="flex mb-4 animate-fade-in">
                  <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm px-4 py-3 rounded-2xl rounded-tl-sm max-w-[85%] sm:max-w-[70%]">
                    <div className="flex items-center gap-2 mb-2">
                      <div className="w-6 h-6 rounded-full bg-slate-100/50 dark:bg-slate-800/50 flex items-center justify-center">
                        <Heart className="w-4 h-4 text-slate-600 dark:text-slate-400" />
                      </div>
                      <span className="text-sm font-medium text-slate-600 dark:text-slate-400">HealthAssist</span>
                    </div>
                    <div className="typing-indicator">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
          <div ref={messagesEndRef} />
        </ScrollArea>
      </div>
      
      {/* Input Area */}
      <div className="p-4 border-t border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 shadow-lg">
        <ChatInput onSendMessage={handleSendMessage} disabled={isTyping} />
      </div>
    </div>
  );
};

export default Chat;
