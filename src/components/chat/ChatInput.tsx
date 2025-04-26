import React, { useState, useRef, useEffect } from "react";
import { SendHorizonal } from "lucide-react";

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled: boolean;
}

const ChatInput: React.FC<ChatInputProps> = ({ onSend, disabled }) => {
  const [message, setMessage] = useState("");
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      onSend(message);
      setMessage("");
      if (inputRef.current) {
        inputRef.current.style.height = "auto";
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleInput = () => {
    const textarea = inputRef.current;
    if (textarea) {
      const scrollPos = textarea.scrollTop;
      textarea.style.height = "auto";
      const newHeight = Math.min(textarea.scrollHeight, 120);
      textarea.style.height = `${newHeight}px`;
      textarea.scrollTop = scrollPos;
    }
  };

  return (
    <form onSubmit={handleSubmit} className="border-t p-3 flex items-end gap-2">
      <div className="relative flex-1">
        <textarea
          ref={inputRef}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          disabled={disabled}
          placeholder="Type a message..."
          rows={1}
          className="w-full resize-none border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 max-h-[120px] min-h-[40px]"
          style={{
            resize: "none",
            overflow: "hidden",
            appearance: "none",
            WebkitAppearance: "none",
            MozAppearance: "none",
          }}
        />
      </div>
      <button
        type="submit"
        disabled={!message.trim() || disabled}
        className={`bg-blue-600 text-white rounded-full p-2 flex items-center justify-center ${
          !message.trim() || disabled
            ? "opacity-50 cursor-not-allowed"
            : "hover:bg-blue-700"
        } transition-colors duration-200`}
        aria-label="Send message"
      >
        <SendHorizonal className="h-5 w-5" />
      </button>
    </form>
  );
};

export default ChatInput;
