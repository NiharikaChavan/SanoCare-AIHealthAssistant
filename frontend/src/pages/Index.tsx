
import React, { useState, useCallback } from 'react';
import { toast } from 'sonner';
import { v4 as uuidv4 } from 'uuid';
import { Message } from '@/utils/types';
import Header from '@/components/Header';
import Chat from '@/components/Chat';
import { API } from '@/services/api';

// Welcome message shown when the app first loads
const WELCOME_MESSAGE = {
  id: uuidv4(),
  content: "Hi there! I'm your health assistant. I can answer questions about symptoms, medications, nutrition, exercise, and general wellness. How can I help you today?",
  sender: 'bot',
  timestamp: new Date(),
} as Message;

const Index = () => {
  const [messages, setMessages] = useState<Message[]>([WELCOME_MESSAGE]);
  const [isTyping, setIsTyping] = useState(false);

  // Function to handle sending a message
  const handleSendMessage = useCallback(async (content: string) => {
    // Add user message to the chat
    const userMessage: Message = {
      id: uuidv4(),
      content,
      sender: 'user',
      timestamp: new Date(),
    };
    
    setMessages(prev => [...prev, userMessage]);
    setIsTyping(true);
    
    try {
      // Call the API service to send the message to the backend
      const response = await API.sendMessage(content);
      
      if (!response.success) {
        throw new Error(response.error || 'Failed to get response');
      }
      
      // Create the bot message from the response
      const botMessage: Message = {
        id: uuidv4(),
        content: response.data.response || "I'm having trouble processing your request right now.",
        sender: 'bot',
        timestamp: new Date(),
      };
      
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Error getting response:', error);
      toast.error('Failed to get a response. Please try again.');
    } finally {
      setIsTyping(false);
    }
  }, []);

  return (
    <div className="flex flex-col min-h-screen bg-gradient-to-b from-background to-background/90">
      <Header />
      
      <main className="flex-1 container mx-auto flex flex-col max-w-4xl">
        <div className="flex-1 flex flex-col glass-panel my-6 overflow-hidden bg-white/90 dark:bg-gray-900/90 backdrop-blur-lg border border-gray-200/50 dark:border-gray-700/50 shadow-lg rounded-2xl">
          <Chat 
            messages={messages}
            isTyping={isTyping}
            onSendMessage={handleSendMessage}
          />
        </div>
      </main>
      
      <footer className="py-4 text-center text-sm text-muted-foreground">
        <p>HealthAssist - Your AI Health Companion</p>
      </footer>
    </div>
  );
};

export default Index;
