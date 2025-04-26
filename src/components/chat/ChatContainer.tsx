import React, { useState, useEffect, useRef } from "react";
import { Message } from "@/types/chat";
import MessageList from "./MessageList";
import ChatInput from "./ChatInput";
import ChatButton from "./ChatButton";
import { sendChatMessage } from "@/services/chatService";
import { toast } from "@/hooks/use-toast";
import { X } from "lucide-react";

const ChatContainer: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isOpen, setIsOpen] = useState(false);
  const [hasInitialMessageSent, setHasInitialMessageSent] = useState(false);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  const toggleChat = () => {
    setIsOpen((prev) => !prev);
  };

  const sendWelcomeMessage = async () => {
    const welcomeMessageId = `msg_${Date.now()}`;
    const welcomeMessage: Message = {
      id: welcomeMessageId,
      text: "Hello! I'm your AI assistant for the Attendance Improvement Plan system. How can I help you today?",
      sender: "bot",
      timestamp: new Date(),
    };
    setMessages([welcomeMessage]);
    setHasInitialMessageSent(true);
  };

  useEffect(() => {
    if (isOpen && !hasInitialMessageSent) {
      sendWelcomeMessage();
    }
  }, [isOpen, hasInitialMessageSent]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (!isOpen) return;
      const target = event.target as HTMLElement;
      if (target.closest('[data-chat-button="true"]')) return;
      if (
        chatContainerRef.current &&
        !chatContainerRef.current.contains(target)
      ) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen]);

  const sendMessage = async (text: string) => {
    if (!text.trim()) return;
    const userMessageId = `msg_${Date.now()}`;
    const userMessage: Message = {
      id: userMessageId,
      text,
      sender: "user",
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);
    try {
      const botResponse = await sendChatMessage(text);
      const botMessage: Message = {
        id: `msg_${Date.now() + 1}`,
        text: botResponse,
        sender: "bot",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      console.error("Error sending message:", error);
      setError("Failed to send message. Please try again.");
      toast({
        title: "Error",
        description: "Failed to send message. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        setIsOpen(false);
      }
    };
    window.addEventListener("keydown", handleEscape);
    return () => window.removeEventListener("keydown", handleEscape);
  }, [isOpen]);

  return (
    <>
      <ChatButton isOpen={isOpen} toggleChat={toggleChat} />

      {isOpen && (
        <div
          ref={chatContainerRef}
          className="fixed bottom-24 right-6 w-80 md:w-96 h-[500px] max-h-[80vh] bg-background rounded-lg shadow-2xl flex flex-col border animate-slide-in z-40"
        >
          <div className="bg-blue-600 text-white p-4 rounded-t-lg flex items-center justify-between">
            <h3 className="font-medium">AIP Assistant</h3>
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

          <MessageList messages={messages} isLoading={isLoading} />

          {error && (
            <div className="bg-red-50 text-red-600 p-2 text-xs border-t border-red-100">
              {error}
            </div>
          )}

          <ChatInput onSend={sendMessage} disabled={isLoading} />
        </div>
      )}
    </>
  );
};

export default ChatContainer;
