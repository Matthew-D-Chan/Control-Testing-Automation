import { useEffect, useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import cibcLogo from '../assets/cibc_logo.svg';
import { Loader } from './common/Loader';

export function HomeView({ sessions, onCreateSession, onSelectSession, onDeleteSession, isLoading }) {
  const sessionsRef = useRef(null);
  const heroRef = useRef(null);
  const heroInView = useInView(heroRef, { once: false, amount: 0.3 });
  const sessionsInView = useInView(sessionsRef, { once: false, amount: 0.2 });

  // Ensure sessions section is always visible when sessions exist
  useEffect(() => {
    if (sessionsRef.current) {
      sessionsRef.current.style.opacity = sessions.length > 0 ? 1 : 1;
    }
  }, [sessions.length]);

  const formatDate = (date) => {
    const dateObj = new Date(date);
    const now = new Date();
    const diffTime = Math.abs(now - dateObj);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    // If today, show time
    if (diffDays === 1) {
      return dateObj.toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit'
      });
    }
    
    // If this week, show day name
    if (diffDays <= 7) {
      return dateObj.toLocaleDateString([], {
        weekday: 'long'
      });
    }
    
    // Otherwise show full date
    return dateObj.toLocaleDateString([], {
      month: 'short',
      day: 'numeric',
      year: dateObj.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
    });
  };
  
  const formatSessionTitle = (date) => {
    const dateObj = new Date(date);
    return `Session from ${dateObj.toLocaleDateString([], {
      month: 'long',
      day: 'numeric',
      year: 'numeric'
    })}`;
  };

  // Animation variants
  const fadeInUp = {
    hidden: { opacity: 0, y: 30 },
    visible: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -30 }
  };

  const fadeIn = {
    hidden: { opacity: 0 },
    visible: { opacity: 1 },
    exit: { opacity: 0 }
  };

  const staggerContainer = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  return (
    <div className="home-view">
      <div ref={heroRef} className="home-hero">
        <motion.div 
          className="hero-content"
          initial="hidden"
          animate={heroInView ? "visible" : "hidden"}
          exit="exit"
          variants={staggerContainer}
        >
          <motion.img 
            src={cibcLogo} 
            alt="Logo" 
            className="hero-logo"
            variants={fadeInUp}
            transition={{ duration: 0.6 }}
          />
          <motion.h1 
            className="hero-title"
            variants={fadeInUp}
            transition={{ duration: 0.6, delay: 0.1 }}
          >
            Begin your interview here.
          </motion.h1>
          <motion.p 
            className="hero-subtitle"
            variants={fadeInUp}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            Start a new session or continue an existing one
          </motion.p>
          <motion.button 
            className="hero-button"
            onClick={onCreateSession}
            disabled={isLoading}
            variants={fadeInUp}
            transition={{ duration: 0.6, delay: 0.3 }}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            {isLoading ? (
              <>
                <Loader size="small" />
                <span>Creating...</span>
              </>
            ) : (
              <>
                <span>+</span>
                <span>Start New Chat</span>
              </>
            )}
          </motion.button>
        </motion.div>
      </div>

      <motion.div 
        ref={sessionsRef} 
        className="home-sessions"
        initial="hidden"
        animate={sessionsInView ? "visible" : "hidden"}
        exit="exit"
        variants={fadeIn}
        transition={{ duration: 0.6 }}
      >
        <div className="sessions-content">
          <motion.h2 
            className="sessions-title"
            variants={fadeInUp}
            transition={{ duration: 0.6 }}
          >
            Previous Conversations
          </motion.h2>
          {isLoading && sessions.length === 0 ? (
            <motion.div 
              className="sessions-loading"
              variants={fadeIn}
              transition={{ duration: 0.4 }}
            >
              <Loader />
            </motion.div>
          ) : sessions.length > 0 ? (
            <motion.div 
              className="sessions-list"
              variants={staggerContainer}
              initial="hidden"
              animate={sessionsInView ? "visible" : "hidden"}
            >
              {sessions.map((session, index) => (
                <motion.div
                  key={session.id}
                  className="session-item"
                  variants={fadeInUp}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                  whileHover={{ scale: 1.01, x: 4 }}
                >
                  <button
                    className="session-item-button"
                    onClick={() => onSelectSession(session.id)}
                  >
                    <div className="session-item-content">
                      <span className="session-item-title">
                        {formatSessionTitle(session.createdAt)}
                      </span>
                      <span className="session-item-date">
                        {formatDate(session.createdAt)}
                      </span>
                    </div>
                    <span className="session-item-arrow">→</span>
                  </button>
                  <button
                    className="session-item-delete"
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeleteSession(session.id);
                    }}
                    aria-label="Delete session"
                    title="Delete session"
                  >
                    🗑️
                  </button>
                </motion.div>
              ))}
            </motion.div>
          ) : (
            <motion.p 
              className="sessions-empty"
              variants={fadeIn}
              transition={{ duration: 0.4 }}
            >
              No previous conversations
            </motion.p>
          )}
        </div>
      </motion.div>
    </div>
  );
}

