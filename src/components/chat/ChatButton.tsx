import React from "react";
import { MessageCircle, X } from "lucide-react";

interface ChatButtonProps {
  isOpen: boolean;
  toggleChat: () => void;
  isMaximized?: boolean;
}

const ChatButton: React.FC<ChatButtonProps> = ({
  isOpen,
  toggleChat,
  isMaximized = false,
}) => {
  if (isMaximized) {
    return null;
  }

  return (
    <button
      data-chat-button="true"
      onClick={toggleChat}
      className="fixed bottom-6 right-6 w-14 h-14 chat-toggle-button text-white rounded-full shadow-lg flex items-center justify-center transition-transform transform hover:scale-110 z-50"
      aria-label={isOpen ? "Close chat" : "Open chat"}
    >
      {isOpen ? (
        <X className="h-6 w-6 animate-fade-in" />
      ) : (
        <MessageCircle className="h-6 w-6 animate-fade-in" />
      )}
    </button>
  );
};

export default ChatButton;
