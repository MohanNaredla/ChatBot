
import React, { useEffect, useRef } from 'react';
import { Message } from '@/types/chat';
import MessageBubble from './MessageBubble';

interface MessageListProps {
  messages: Message[];
  isLoading: boolean;
}

const MessageList: React.FC<MessageListProps> = ({ messages, isLoading }) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <div className="flex-1 overflow-y-auto px-4 py-2">
      {messages.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-full text-center text-gray-500">
          <p className="mb-2">Welcome to our chat assistant!</p>
          <p>How can I help you today?</p>
        </div>
      ) : (
        <div className="flex flex-col space-y-2">
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}
          {isLoading && (
            <div className="chat-bubble-bot p-3 max-w-[80%] animate-pulse">
              <div className="flex space-x-2 items-center">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse" style={{ animationDelay: "0.2s" }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse" style={{ animationDelay: "0.4s" }}></div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      )}
    </div>
  );
};

export default MessageList;
