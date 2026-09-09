import { createContext, useContext, useState } from "react";

const ChatContext = createContext(null);

export function ChatProvider({ children }) {
  const [messages, setMessages] = useState([]);

  function addMessage(message) {
    setMessages((prev) => [...prev, message]);
  }

  function removeLastMessage() {
    setMessages((prev) => prev.slice(0, -1));
  }

  const value = { messages, setMessages, addMessage, removeLastMessage };

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
}

export function useChat() {
  const ctx = useContext(ChatContext);
  if (!ctx) throw new Error("useChat must be used inside ChatProvider");
  return ctx;
}