import { useState, useEffect, useCallback } from 'react';
import { API_BASE_URL, createSession, createSessionSummary, createMessage } from '../types/chat';

/**
 * Custom hook for managing chat state and API calls
 */
export function useChat() {
  const [sessions, setSessions] = useState([]);
  const [currentSession, setCurrentSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState(null);

  // Fetch all sessions
  const fetchSessions = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await fetch(`${API_BASE_URL}/api/sessions/`);
      if (!response.ok) throw new Error('Failed to fetch sessions');
      const data = await response.json();
      console.log('Fetched sessions data:', data);
      const sessionsList = data.map(createSessionSummary);
      console.log('Processed sessions:', sessionsList);
      setSessions(sessionsList);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching sessions:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Create a new session
  const createNewSession = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await fetch(`${API_BASE_URL}/api/sessions/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      if (!response.ok) throw new Error('Failed to create session');
      const data = await response.json();
      const newSession = createSessionSummary(data);
      setCurrentSession(newSession);
      setMessages([]);
      setSessions(prev => [newSession, ...prev]);
      return newSession;
    } catch (err) {
      setError(err.message);
      console.error('Error creating session:', err);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Load a specific session with its messages
  const loadSession = useCallback(async (sessionId) => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}`);
      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('Session not found');
        }
        throw new Error('Failed to load session');
      }
      const data = await response.json();
      const session = createSession(data);
      setCurrentSession(session);
      setMessages(session.messages);
      return session;
    } catch (err) {
      setError(err.message);
      console.error('Error loading session:', err);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Send a message (user answer)
  const sendMessage = useCallback(async (userAnswer) => {
    if (!currentSession || !userAnswer.trim()) return;

    // Optimistically add user message
    const tempMessageId = `temp_${Date.now()}`;
    const userMessage = {
      id: tempMessageId,
      role: 'user',
      content: userAnswer,
      createdAt: new Date()
    };

    try {
      setIsSending(true);
      setError(null);
      setMessages(prev => [...prev, userMessage]);

      const response = await fetch(
        `${API_BASE_URL}/api/sessions/${currentSession.id}/answer`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ userAnswer })
        }
      );

      if (!response.ok) throw new Error('Failed to send message');

      const data = await response.json();
      
      // Replace optimistic message and add assistant response
      const newMessages = data.messages.map(createMessage);
      setMessages(newMessages);
    } catch (err) {
      setError(err.message);
      console.error('Error sending message:', err);
      // Remove optimistic message on error
      setMessages(prev => prev.filter(m => m.id !== tempMessageId));
    } finally {
      setIsSending(false);
    }
  }, [currentSession]);

  // Delete a session
  const deleteSession = useCallback(async (sessionId) => {
    try {
      setError(null);
      const response = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}`, {
        method: 'DELETE'
      });
      if (!response.ok) throw new Error('Failed to delete session');
      
      setSessions(prev => prev.filter(s => s.id !== sessionId));
      
      // If deleted session was current, clear it
      if (currentSession?.id === sessionId) {
        setCurrentSession(null);
        setMessages([]);
      }
    } catch (err) {
      setError(err.message);
      console.error('Error deleting session:', err);
    }
  }, [currentSession]);

  // Initialize: fetch sessions on mount
  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  return {
    sessions,
    currentSession,
    messages,
    isLoading,
    isSending,
    error,
    fetchSessions,
    createNewSession,
    loadSession,
    sendMessage,
    deleteSession
  };
}

