import React from "react";
import { Message } from "@/types/chat";
import { parseMarkdown } from "@/utils/markdownParser";

interface MessageBubbleProps {
  message: Message;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const bubbleClass =
    message.sender === "user" ? "chat-bubble-user" : "chat-bubble-bot";

  return (
    <div
      className={`${bubbleClass} p-3 max-w-[80%] mb-2 shadow-sm animate-slide-in message-gap`}
    >
      <div
        dangerouslySetInnerHTML={{ __html: parseMarkdown(message.text) }}
        className="text-sm break-words"
      />
      <div className="text-xs opacity-70 mt-1 text-right">
        {new Date(message.timestamp).toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        })}
      </div>
    </div>
  );
};

export default MessageBubble;
