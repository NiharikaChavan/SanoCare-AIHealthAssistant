
export interface Message {
  id: string;
  content: string;
  sender: 'user' | 'bot';
  timestamp: Date;
}

export interface ChatProps {
  messages: Message[];
  isTyping: boolean;
  onSendMessage: (message: string) => void;
}

export interface MessageProps {
  message: Message;
  isLatest: boolean;
}

export interface ChatInputProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
}

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
}

export interface ChatResponse {
  response: string;
  sources?: string[];
  confidence?: number;
}
