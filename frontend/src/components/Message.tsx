import React from 'react';
import { format } from 'date-fns';
import { User, Bot } from 'lucide-react';

interface MessageProps {
  message: {
    role: 'user' | 'assistant';
    content: string;
    timestamp?: Date;
  };
  isLatest?: boolean;
}

const Message: React.FC<MessageProps> = ({ message, isLatest }) => {
  return (
    <div className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
      <div className={`flex items-start gap-2 max-w-[85%] sm:max-w-[70%] ${isLatest ? 'animate-message-appear' : ''}`}>
        {message.role === 'assistant' && (
          <div className="w-8 h-8 rounded-full bg-slate-100/50 dark:bg-slate-800/50 flex items-center justify-center flex-shrink-0">
            <Bot className="w-4 h-4 text-slate-600 dark:text-slate-400" />
          </div>
        )}
        <div className={`flex flex-col ${message.role === 'user' ? 'items-end' : 'items-start'}`}>
          <div className={`px-4 py-3 rounded-2xl ${
            message.role === 'user' 
              ? 'bg-gradient-to-r from-slate-600 to-blue-600 text-white rounded-tr-sm' 
              : 'bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-tl-sm'
          } shadow-sm`}>
            <p className="text-sm whitespace-pre-wrap">{message.content}</p>
          </div>
          {message.timestamp && (
            <span className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              {format(new Date(message.timestamp), 'h:mm a')}
            </span>
          )}
        </div>
        {message.role === 'user' && (
          <div className="w-8 h-8 rounded-full bg-slate-100/50 dark:bg-slate-800/50 flex items-center justify-center flex-shrink-0">
            <User className="w-4 h-4 text-slate-600 dark:text-slate-400" />
          </div>
        )}
      </div>
    </div>
  );
};

export default Message;
