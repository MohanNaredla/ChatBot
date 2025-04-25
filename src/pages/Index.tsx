
import React from 'react';
import ChatContainer from '@/components/chat/ChatContainer';

const Index = () => {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-b from-blue-50 to-white">
      <div className="text-center max-w-2xl px-4">
        <h1 className="text-4xl font-bold mb-6 text-blue-900">Welcome to our Chat Assistant</h1>
        <p className="text-xl text-gray-700 mb-8">
          Click the chat button in the bottom right corner to start a conversation with our AI assistant.
        </p>
        <div className="flex justify-center space-x-4">
          <a href="#features" className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors">
            Learn More
          </a>
          <a href="#contact" className="bg-gray-200 text-gray-800 px-6 py-3 rounded-lg hover:bg-gray-300 transition-colors">
            Contact Us
          </a>
        </div>
      </div>
      
      <ChatContainer />
    </div>
  );
};

export default Index;
