import React, { useState } from 'react';
import LandingPage from './LandingPage';
import AuthPage from './AuthPage'; // We'll move your login code here
import CommandCenter from './CommandCenter';

export default function App() {
  // Views: 'landing', 'auth', 'dashboard'
  const [view, setView] = useState('landing');
  const [user, setUser] = useState(null);

  return (
    <>
      {view === 'landing' && <LandingPage onGetStarted={() => setView('auth')} />}
      {view === 'auth' && (
        <AuthPage 
          onBack={() => setView('landing')} 
          onLoginSuccess={(userData) => {
            setUser(userData);
            setView('dashboard');
          }} 
        />
      )}
      {view === 'dashboard' && user && <CommandCenter user={user} onLogout={() => setView('landing')} />}
    </>
  );
}