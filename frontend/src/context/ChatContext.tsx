import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

interface ChatContextType {
  messages: Message[];
  loading: boolean;
  sendMessage: (content: string) => Promise<void>;
  clearMessages: () => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export const ChatProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);

  const sendMessage = async (content: string) => {
    setLoading(true);
    try {
      const response = await axios.post('/get', { msg: content });
      if (response.data.success) {
        setMessages(prev => [
          ...prev,
          { role: 'user', content, timestamp: new Date().toISOString() },
          { role: 'assistant', content: response.data.response, timestamp: new Date().toISOString() }
        ]);
      }
    } catch (error) {
      console.error('Error sending message:', error);
    } finally {
      setLoading(false);
    }
  };

  const clearMessages = () => {
    setMessages([]);
  };

  return (
    <ChatContext.Provider value={{ messages, loading, sendMessage, clearMessages }}>
      {children}
    </ChatContext.Provider>
  );
};

export const useChat = () => {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
}; 