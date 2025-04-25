
export interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
}

export interface ChatContextType {
  messages: Message[];
  isLoading: boolean;
  error: string | null;
  sendMessage: (text: string) => Promise<void>;
}
