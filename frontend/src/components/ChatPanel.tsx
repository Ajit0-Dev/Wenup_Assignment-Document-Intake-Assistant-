import React, { useState, useRef, useEffect } from 'react';
import type { Message } from '../types';

interface ChatPanelProps {
  messages: Message[];
  onSendMessage: (text: string) => void;
  isTyping: boolean;
  error: string | null;
}

const ChatPanel: React.FC<ChatPanelProps> = ({ messages, onSendMessage, isTyping, error }) => {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isTyping) {
      onSendMessage(input);
      setInput('');
    }
  };

  return (
    <div className="chat-panel">
      <div className="chat-header">
        <h1>Document Intake Assistant</h1>
        <p>I will help you draft your Personal Wishes Document.</p>
      </div>

      <div className="chat-messages">
        {messages.map((msg) => (
          <div key={msg.id} className={`message-bubble message-${msg.role}`}>
            {msg.content}
          </div>
        ))}
      {isTyping && (
          <div className="message-bubble message-assistant typing-indicator">
            <span className="typing-dot" />
            <span className="typing-dot" />
            <span className="typing-dot" />
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {error && <div className="error-message">{error}</div>}

      <div className="chat-input-area">
        <form onSubmit={handleSubmit} className="chat-input-form">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message..."
            disabled={isTyping}
          />
          <button type="submit" disabled={!input.trim() || isTyping}>
            Send
          </button>
        </form>
      </div>
    </div>
  );
};

export default ChatPanel;
