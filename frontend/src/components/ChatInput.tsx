import React, { useState, useRef, useEffect } from 'react';
import { Send } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
}

const ChatInput: React.FC<ChatInputProps> = ({ onSendMessage, disabled = false }) => {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSendMessage = () => {
    if (message.trim()) {
      onSendMessage(message.trim());
      setMessage('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(120, Math.max(48, textareaRef.current.scrollHeight))}px`;
    }
  }, [message]);

  return (
    <div className="w-full glass-panel p-3 flex items-end gap-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-full">
      <textarea
        ref={textareaRef}
        className="flex-1 bg-transparent border-0 outline-none resize-none min-h-[24px] max-h-32 text-base placeholder:text-muted-foreground focus:ring-0 focus:border-0 py-2 px-3"
        placeholder={disabled ? "Waiting for response..." : "Type your health question..."}
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        rows={1}
      />
      <Button 
        size="icon" 
        className={cn(
          "rounded-full h-10 w-10 flex-shrink-0 bg-gradient-to-r from-health to-health-dark hover:opacity-90 transition-all",
          !message.trim() && "opacity-70 cursor-not-allowed",
          disabled && "opacity-50"
        )}
        disabled={!message.trim() || disabled}
        onClick={handleSendMessage}
      >
        {disabled ? (
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-current border-t-transparent" />
        ) : (
          <Send className="h-5 w-5" />
        )}
        <span className="sr-only">Send message</span>
      </Button>
    </div>
  );
};

export default ChatInput;
