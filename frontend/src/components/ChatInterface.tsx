import React, { useState, useRef, useEffect } from 'react';
import { useChat } from '../context/ChatContext';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent, CardFooter } from './ui/card';

const ChatInterface: React.FC = () => {
  const [input, setInput] = useState('');
  const { messages, loading, sendMessage } = useChat();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    
    await sendMessage(input);
    setInput('');
  };

  return (
    <div className="flex flex-col h-screen">
      <Card className="flex-1 overflow-hidden">
        <CardContent className="h-full overflow-y-auto p-4">
          <div className="space-y-4">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex ${
                  message.role === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                <div
                  className={`max-w-[70%] rounded-lg p-3 ${
                    message.role === 'user'
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-100 text-gray-900'
                  }`}
                >
                  {message.content}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 text-gray-900 rounded-lg p-3">
                  Thinking...
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </CardContent>
        <CardFooter className="border-t p-4">
          <form onSubmit={handleSubmit} className="flex w-full space-x-2">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your message..."
              className="flex-1"
            />
            <Button type="submit" disabled={loading}>
              Send
            </Button>
          </form>
        </CardFooter>
      </Card>
    </div>
  );
};

export default ChatInterface; 