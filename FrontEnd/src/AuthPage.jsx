import axios from 'axios';
import React, { useState } from 'react';
import { Mail, Lock, UserPlus, EyeOff, BarChart3, ChevronRight, TrendingUp, Package, ArrowLeft } from 'lucide-react';
const BASE_URL = import.meta.env.sales-prediction-model-mu.vercel.app/ || "http://localhost:8000"
export default function AuthPage({ onLoginSuccess, onBack }) {
  const handleLogin = async () => {
  try {
    const response = await axios.post(`${BASE_URL}/login`, {
      username: email, // you'll need to capture this from your input state
      password: password
    });
    if (response.data.status === "success") {
       alert("Login Successful!");
       // This is where you would redirect to the Dashboard
    }
  } catch (error) {
    alert("Login Failed: Check your username or password");
  }
};
  const [isLogin, setIsLogin] = useState(true);
// Add these lines right below isLogin state
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState(''); // Only for signup
  // Dynamic content for the left side
  const leftPanelContent = {
    login: {
      title: "Know What To Stock.",
      desc: "Stop guessing. Use AI to predict your next bestseller before it sells out.",
      icon: <TrendingUp size={120} className="text-orange-500 opacity-80" />,
      tag: "INVENTORY INTELLIGENCE"
    },
    signup: {
      title: "Predict Your Sales.",
      desc: "Connect your data and let SalesInsight AI build your 12-month growth map.",
      icon: <BarChart3 size={120} className="text-orange-500 opacity-80" />,
      tag: "GROWTH ENGINE"
    }
  };
  const content = isLogin ? leftPanelContent.login : leftPanelContent.signup;
  const handleAuth = async (e) => {
    e.preventDefault(); // Stops the page from refreshing
    
    const endpoint = isLogin ? '/login' : '/signup';
    const payload = isLogin 
      ? { username: email, password: password } 
      : { username: email, password: password, full_name: fullName };
    try {
      // This sends the data to your Python Backend
      const response = await fetch(`${BASE_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      if (response.ok) {
        alert(isLogin ? "Welcome back to SalesInsight AI!" : "Account created successfully!");
        // Future step: window.location.href = '/dashboard';
        onLoginSuccess({ username: email });
      } else {
        alert(data.detail || "Authentication failed");
      }
    } catch (error) {
      alert("Backend not running! Start your Python server first.");
    }
  };
  return (
    <div className="min-h-screen bg-[#0f0f0f] relative flex items-center justify-center font-sans p-4 md:p-8">
      {/* --- ADD THIS BUTTON BLOCK --- */}
      <button 
        onClick={onBack} 
        className="absolute top-6 left-6 z-50 flex items-center gap-2 text-slate-500 hover:text-orange-500 transition-all font-black text-[10px] uppercase tracking-[0.2em] group"
      >
        <div className="w-9 h-9 rounded-full border border-white/5 flex items-center justify-center group-hover:border-orange-500/50 transition-all">
          <ArrowLeft size={16} /> 
        </div>
        Back to Home
      </button>
      {/* ----------------------------- */}

      {/* Main Glassmorphism Container */}
      <div className="w-full max-w-6xl h-full min-h-[600px] md:h-[85vh] flex flex-col md:flex-row bg-[#1a1a1a] rounded-[3rem] overflow-hidden shadow-[0_0_50px_rgba(0,0,0,0.5)] border border-white/5">
        
        {/* =========================================================
           LEFT PANEL (Dark / Content)
        =========================================================== */}
        <div className="relative flex-1 bg-[#141414] p-12 flex flex-col justify-between overflow-hidden">
          {/* Decorative background gradient */}
          <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-orange-600/10 blur-[120px] rounded-full"></div>
          
          {/* Logo as Back Button */}
          <div 
            onClick={onBack} 
            className="z-10 flex items-center gap-3 mb-10 cursor-pointer hover:opacity-80 transition-opacity"
          >
            <div className="w-10 h-10 bg-gradient-to-tr from-orange-500 to-red-600 rounded-xl flex items-center justify-center shadow-lg shadow-orange-900/20">
              <BarChart3 className="text-white" size={20} />
            </div>
            <h1 className="text-xl font-black text-white tracking-tighter">
              SalesInsight <span className="text-orange-500 uppercase text-xs tracking-[0.2em] ml-1">AI</span>
            </h1>
          </div>
          {/* Dynamic Content Section */
          <div className="z-10 mt-10 space-y-6">
            <span className="text-orange-500 font-bold text-[10px] tracking-[0.3em] uppercase bg-orange-500/10 px-3 py-1 rounded-full border border-orange-500/20">
              {content.tag}
            </span>
            <h2 className="text-5xl md:text-6xl font-black text-white leading-[0.9] tracking-tighter transition-all duration-500">
              {content.title}
            </h2>
            <p className="text-slate-400 text-lg max-w-sm leading-relaxed">
              {content.desc}
            </p>
          </div>
          /* The "Attractive" Graphic Area */}
          <div className="relative z-10 flex justify-center py-8">
             <div className="p-6 w-40 h-40 bg-white/5 rounded-full border border-white/10 backdrop-blur-sm animate-pulse flex items-center justify-center">
                {content.icon}
             </div>
          </div>
          <div className="z-10 text-[10px] text-slate-500 font-medium tracking-widest uppercase">
            Designed for Modern Retailers
          </div>
        </div>
        {/* =========================================================
           RIGHT PANEL (White / Form)
        =========================================================== */}
        <div className="flex-1 bg-white p-10 md:p-16 flex flex-col justify-between overflow-y-auto">
          
          {/* Top Switcher */}
          <div className="flex justify-end items-center">
            <button 
              onClick={() => setIsLogin(!isLogin)}
              className="text-xs font-bold text-slate-900 flex items-center gap-2 group hover:text-orange-600 transition-colors"
            >
              {isLogin ? "DON'T HAVE AN ACCOUNT?" : "ALREADY A MEMBER?"}
              <span className="text-orange-600 border-b-2 border-orange-600 pb-0.5 group-hover:border-slate-900 transition-all">
                {isLogin ? "SIGN UP" : "LOG IN"}
              </span>
            </button>
          </div>
          {/* Form Area */}
          <div className="max-w-md mx-auto w-full py-10">
            <h3 className="text-4xl font-black text-slate-900 tracking-tighter mb-2">
              {isLogin ? "Sign In" : "Create Account"}
            </h3>
            <p className="text-slate-500 text-sm mb-10 font-medium">
              Enter your credentials to access <span className="text-slate-900 font-bold">SalesInsight AI</span>
            </p>
            <form className="space-y-4" onSubmit={(e) => e.preventDefault()}>
              
              {!isLogin && (
                <div className="space-y-1">
                  <input 
                    type="text" 
                    className="w-full px-6 py-4 rounded-2xl bg-slate-50 border border-slate-100 outline-none focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500 transition-all text-slate-800 font-medium placeholder:text-slate-400"
                    placeholder="Full Name"
                    value={fullName} onChange={(e) => setFullName(e.target.value)}
                  />
                </div>
              )}
              <div className="space-y-1">
                <input 
                  type="email" 
                  className="w-full px-6 py-4 rounded-2xl bg-slate-50 border border-slate-100 outline-none focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500 transition-all text-slate-800 font-medium placeholder:text-slate-400"
                  placeholder="Email or Username"
                  value={email} onChange={(e) => setEmail(e.target.value)}
                />
              </div>
              <div className="space-y-1">
                <div className="relative group">
                  <input 
                    type="password" 
                    className="w-full px-6 py-4 rounded-2xl bg-slate-50 border border-slate-100 outline-none focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500 transition-all text-slate-800 font-medium placeholder:text-slate-400"
                    placeholder="Password"
                    value={password} onChange={(e) => setPassword(e.target.value)}
                  />
                  <button type="button" className="absolute right-5 top-4 text-slate-300 hover:text-slate-500">
                    <EyeOff size={20} />
                  </button>
                </div>
              </div>
              {isLogin && (
                <div className="text-right py-2">
                  <a href="#" className="text-[10px] font-black text-orange-600 hover:underline tracking-widest uppercase">Forgot Password?</a>
                </div>
              )}
              {/* Main CTA Button */}
<button 
  type="submit"
  onClick={handleAuth} 
  className="w-full mt-6 py-5 rounded-full bg-gradient-to-r from-orange-500 to-red-600 text-white font-black text-sm uppercase tracking-[0.2em] shadow-xl shadow-orange-500/20 hover:opacity-90 active:scale-[0.98] transition-all flex items-center justify-center gap-3 group"
>
  {isLogin ? "Sign In" : "Register Now"}
  <ChevronRight size={18} className="group-hover:translate-x-1 transition-transform" />
</button>
            </form>
          </div>
          {/* Footer Info */}
          <div className="flex justify-between items-center text-[9px] text-slate-400 font-black tracking-widest uppercase border-t border-slate-50 pt-6">
            <p>© 2026 SALESINSIGHT AI INC.</p>
            <div className="flex gap-4">
              <a href="#" className="hover:text-slate-900 transition-colors">Privacy</a>
              <a href="#" className="hover:text-slate-900 transition-colors">Terms</a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}


