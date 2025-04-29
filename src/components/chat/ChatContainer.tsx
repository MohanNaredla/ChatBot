import React, { useState, useEffect, useRef } from "react";
import { Message } from "@/types/chat";
import MessageList from "./MessageList";
import ChatInput from "./ChatInput";
import ChatButton from "./ChatButton";
import { sendChatMessage } from "@/services/chatService";
import { toast } from "@/hooks/use-toast";
import { X, Maximize2, Minimize2 } from "lucide-react";

const ChatContainer: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isOpen, setIsOpen] = useState(false);
  const [isMaximized, setIsMaximized] = useState(false);
  const [hasInitialMessageSent, setHasInitialMessageSent] = useState(false);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  const toggleChat = () => {
    setIsOpen((prev) => !prev);
    if (isOpen && isMaximized) {
      setIsMaximized(false);
    }
  };

  const toggleSize = () => {
    setIsMaximized((prev) => !prev);
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
        if (isMaximized) {
          setIsMaximized(false);
        }
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen, isMaximized]);

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
        if (isMaximized) {
          setIsMaximized(false);
        }
      }
    };

    window.addEventListener("keydown", handleEscape);
    return () => window.removeEventListener("keydown", handleEscape);
  }, [isOpen, isMaximized]);

  return (
    <>
      <ChatButton
        isOpen={isOpen}
        toggleChat={toggleChat}
        isMaximized={isMaximized}
      />

      {isOpen && (
        <div
          ref={chatContainerRef}
          className={`fixed chat-container border z-40 flex flex-col rounded-lg shadow-2xl transition-all duration-500 ease-in-out ${
            isMaximized
              ? "top-4 right-4 bottom-4 left-4 md:left-auto md:w-1/2 md:bottom-4 md:top-4"
              : "bottom-24 right-6 w-80 md:w-96 h-[500px] max-h-[80vh]"
          }`}
          style={{ backgroundColor: "white" }}
        >
          <div className="chat-header p-4 rounded-t-lg flex items-center justify-between transition-all duration-300">
            <h3 className="font-medium">AIP Assistant</h3>
            <div className="flex items-center space-x-2">
              <button
                onClick={toggleSize}
                className="text-white header-icon-button"
                aria-label={isMaximized ? "Minimize chat" : "Maximize chat"}
              >
                {isMaximized ? (
                  <Minimize2 className="h-5 w-5" />
                ) : (
                  <Maximize2 className="h-5 w-5" />
                )}
              </button>
              <button
                onClick={toggleChat}
                className="text-white header-icon-button"
                aria-label="Close chat"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
          </div>

          <MessageList messages={messages} isLoading={isLoading} />

          {error && (
            <div className="bg-red-50 text-red-600 p-2 text-xs border-t border-red-100 transition-opacity duration-300">
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
