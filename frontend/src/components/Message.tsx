import React from 'react';
import { cn } from '@/lib/utils';
import { format } from 'date-fns';

interface MessageProps {
  message: {
    role: 'user' | 'assistant';
    content: string;
    timestamp?: Date;
  };
  isLatest?: boolean;
}

const Message: React.FC<MessageProps> = ({ message, isLatest = false }) => {
  const isUser = message.role === 'user';

  return (
    <div className={cn(
      "flex mb-4 animate-fade-in",
      isUser ? "justify-end" : "justify-start"
    )}>
      <div className={cn(
        "px-4 py-3 rounded-2xl max-w-[85%] sm:max-w-[70%] shadow-sm",
        isUser 
          ? "bg-health text-white rounded-tr-sm" 
          : "bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-tl-sm"
      )}>
        <div className="flex items-center gap-2 mb-2">
          <div className={cn(
            "w-6 h-6 rounded-full flex items-center justify-center",
            isUser 
              ? "bg-white/20" 
              : "bg-health/20"
          )}>
            <span className={cn(
              "text-xs font-medium",
              isUser ? "text-white" : "text-health"
            )}>
              {isUser ? "You" : "AI"}
            </span>
          </div>
          {message.timestamp && (
            <span className={cn(
              "text-xs",
              isUser ? "text-white/70" : "text-muted-foreground"
            )}>
              {format(new Date(message.timestamp), 'h:mm a')}
            </span>
          )}
        </div>
        <div className="prose dark:prose-invert max-w-none">
          {message.content}
        </div>
      </div>
    </div>
  );
};

export default Message;
