
import React, { useState, useEffect } from 'react';
import { Message } from '@/types/chat';
import MessageList from './MessageList';
import ChatInput from './ChatInput';
import ChatButton from './ChatButton';
import { sendChatMessage } from '@/services/chatService';
import { toast } from '@/hooks/use-toast';
import { X } from 'lucide-react';

const ChatContainer: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isOpen, setIsOpen] = useState(false);

  const toggleChat = () => {
    setIsOpen(prev => !prev);
  };

  const sendMessage = async (text: string) => {
    if (!text.trim()) return;
    
    // Generate a unique ID for the message
    const userMessageId = `msg_${Date.now()}`;
    
    // Add user message to the chat
    const userMessage: Message = {
      id: userMessageId,
      text,
      sender: 'user',
      timestamp: new Date(),
    };
    
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);
    
    try {
      // Mock API call - replace with real API in production
      let botResponse;
      try {
        botResponse = await sendChatMessage(text);
      } catch (error) {
        // Use mock response for demo purposes
        await new Promise(resolve => setTimeout(resolve, 1000));
        botResponse = "I'm a demo bot. In production, I would connect to a real API. How can I help you today?";
      }
      
      // Add bot response to the chat
      const botMessage: Message = {
        id: `msg_${Date.now() + 1}`,
        text: botResponse,
        sender: 'bot',
        timestamp: new Date(),
      };
      
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      setError('Failed to send message. Please try again.');
      toast({
        title: "Error",
        description: "Failed to send message. Please try again.",
        variant: "destructive"
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Handle the escape key to close the chat
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        setIsOpen(false);
      }
    };
    
    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  }, [isOpen]);

  return (
    <>
      <ChatButton isOpen={isOpen} toggleChat={toggleChat} />
      
      {isOpen && (
        <div className="fixed bottom-24 right-6 w-80 md:w-96 h-[500px] max-h-[80vh] bg-background rounded-lg shadow-2xl flex flex-col border animate-slide-in z-40">
          <div className="bg-blue-600 text-white p-4 rounded-t-lg flex items-center justify-between">
            <h3 className="font-medium">Chat Assistant</h3>
            <div className="flex items-center space-x-2">
              {isLoading && (
                <span className="inline-block w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
              )}
              <button 
                onClick={toggleChat}
                className="hover:bg-blue-700 p-1 rounded"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>
          
          <MessageList 
            messages={messages} 
            isLoading={isLoading} 
          />
          
          {error && (
            <div className="bg-red-50 text-red-600 p-2 text-xs border-t border-red-100">
              {error}
            </div>
          )}
          
          <ChatInput 
            onSend={sendMessage} 
            disabled={isLoading} 
          />
        </div>
      )}
    </>
  );
};

export default ChatContainer;
