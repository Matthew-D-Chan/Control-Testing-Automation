import { useState } from 'react';
import { AppLayout } from './components/Layout/AppLayout';
import { HomeView } from './components/HomeView';
import { ChatWindow } from './components/Chat/ChatWindow';
import { useChat } from './hooks/useChat';
import './styles/global.css';

function App() {
  const {
    sessions,
    currentSession,
    messages,
    isLoading,
    isSending,
    error,
    createNewSession,
    loadSession,
    sendMessage,
    fetchSessions
  } = useChat();

  const [view, setView] = useState('home'); // 'home' or 'chat'

  const handleCreateSession = async () => {
    try {
      await createNewSession();
      setView('chat');
    } catch (err) {
      console.error('Failed to create session:', err);
    }
  };

  const handleSelectSession = async (sessionId) => {
    try {
      await loadSession(sessionId);
      setView('chat');
    } catch (err) {
      console.error('Failed to load session:', err);
    }
  };

  const handleBackToHome = () => {
    setView('home');
    // Refresh sessions when returning to home
    fetchSessions();
  };

  return (
    <AppLayout onNavigateHome={handleBackToHome}>
      {view === 'home' ? (
        <HomeView
          sessions={sessions}
          onCreateSession={handleCreateSession}
          onSelectSession={handleSelectSession}
          isLoading={isLoading}
        />
      ) : (
        <div className="chat-container">
          <ChatWindow
            messages={messages}
            onSend={sendMessage}
            isTyping={isSending}
          />
        </div>
      )}
      {error && (
        <div className="error-toast">
          Error: {error}
        </div>
      )}
    </AppLayout>
  );
}

export default App;
