import React, { useState, useEffect } from 'react';
import { createSession, sendChatMessage } from './api';
import type { IntakeState } from './api';
import ChatPanel from './components/ChatPanel';
import ContextPanel from './components/ContextPanel';
import type { Message } from './types';

function App() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [state, setState] = useState<IntakeState | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isTyping, setIsTyping] = useState(false);

  useEffect(() => {
    initSession();
  }, []);

  const initSession = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const res = await createSession();
      setSessionId(res.session_id);
      setState(res.state);
      setMessages([
        { id: Date.now().toString(), role: 'assistant', content: res.message }
      ]);
    } catch (err) {
      setError('Failed to start session. Please try again.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSendMessage = async (text: string) => {
    if (!text.trim() || !sessionId) return;

    const userMsg: Message = { id: Date.now().toString(), role: 'user', content: text };
    setMessages(prev => [...prev, userMsg]);
    setIsTyping(true);
    setError(null);

    try {
      const res = await sendChatMessage(sessionId, text);
      setState(res.state);
      
      const assistantMsg: Message = { 
        id: (Date.now() + 1).toString(), 
        role: 'assistant', 
        content: res.assistant_message 
      };
      setMessages(prev => [...prev, assistantMsg]);
    } catch (err) {
      setError('Failed to send message. Please try again.');
      console.error(err);
    } finally {
      setIsTyping(false);
    }
  };

  if (isLoading && !sessionId) {
    return (
      <div className="loading-screen">
        <div className="loading-spinner" />
        <span>Starting session...</span>
      </div>
    );
  }

  return (
    <div className="app-container">
      <ChatPanel 
        messages={messages}
        onSendMessage={handleSendMessage}
        isTyping={isTyping}
        error={error}
      />
      <ContextPanel state={state} sessionId={sessionId} />
    </div>
  );
}

export default App;
