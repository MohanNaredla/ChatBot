export interface Message {
  content: string;
  sender: 'user' | 'bot';
  timestamp: Date;
}

export interface ChatRequest {
  question: string;
  conversation_context?: { question: string; answer: string }[];
}

export interface ChatResponse {
  question: string;
  answer: string;
}
