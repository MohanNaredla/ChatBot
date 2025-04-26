import React, { useEffect } from "react";
import ChatContainer from "@/components/chat/ChatContainer";

const Index = () => {
  useEffect(() => {
    console.log("Index component mounted");
  }, []);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-b from-blue-50 to-white">
      <ChatContainer />
    </div>
  );
};

export default Index;
