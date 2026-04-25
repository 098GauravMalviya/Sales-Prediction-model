import React, { useState } from 'react';
import { 
  BarChart3, MapPin, Calendar, DollarSign, Package, 
  Cpu, Battery, ChevronRight, Zap, Globe, Shield 
} from 'lucide-react';

export default function LandingPage({ onGetStarted }) {
  const [activeTab, setActiveTab] = useState('map');

  const addons = [
    { 
      id: 'map', 
      title: 'Regional Map Toggle', 
      icon: <MapPin />, 
      desc: 'Visualize demand heatmaps across global territories to optimize logistics.' 
    },
    { 
      id: 'festival', 
      title: 'Festival Correlation', 
      icon: <Calendar />, 
      desc: 'Our AI flags upcoming holidays and cultural events that trigger buying spikes.' 
    },
    { 
      id: 'budget', 
      title: 'Budget Optimizer', 
      icon: <DollarSign />, 
      desc: 'Input your procurement budget; the AI suggests the highest ROI inventory mix.' 
    }
  ];

  return (
    <div className="min-h-screen bg-[#0f0f0f] text-white font-sans selection:bg-orange-500/30">
      
      {/* ================= HEADER ================= */}
      <nav className="fixed top-0 w-full z-50 flex justify-between items-center px-10 py-6 backdrop-blur-md border-b border-white/5">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-gradient-to-tr from-orange-500 to-red-600 rounded-lg flex items-center justify-center">
            <BarChart3 size={18} />
          </div>
          <span className="font-black tracking-tighter text-xl">SalesInsight AI</span>
        </div>
        <button 
          onClick={onGetStarted}
          className="text-xs font-black tracking-widest uppercase bg-white text-black px-6 py-2.5 rounded-full hover:bg-orange-500 hover:text-white transition-all"
        >
          Sign In
        </button>
      </nav>

      {/* ================= HERO SECTION (Reference Image 2 style) ================= */}
      <section className="relative pt-40 pb-20 px-10 flex flex-col items-center text-center overflow-hidden">
        {/* Background Glows */}
        <div className="absolute top-20 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-orange-600/20 blur-[120px] rounded-full pointer-events-none"></div>
        <div className="absolute -top-40 -right-40 w-[400px] h-[400px] bg-blue-600/10 blur-[100px] rounded-full pointer-events-none"></div>

        <h1 className="z-10 text-6xl md:text-8xl font-black tracking-tighter leading-[0.9] max-w-4xl mb-8">
          Predict Demand <br /> <span className="text-transparent bg-clip-text bg-gradient-to-r from-orange-400 to-red-600">Before It Happens.</span>
        </h1>
        <p className="z-10 text-slate-400 text-lg md:text-xl max-w-2xl mb-12 leading-relaxed font-medium">
          Unlock enterprise-grade inventory intelligence. Our AI agents monitor global trends, festivals, and market shifts so you stay ahead.
        </p>
        <button 
          onClick={onGetStarted}
          className="z-10 group flex items-center gap-3 bg-white text-black pl-8 pr-2 py-2 rounded-full font-black uppercase text-sm tracking-widest hover:scale-105 transition-all shadow-2xl shadow-white/10"
        >
          Get Started
          <div className="bg-orange-500 p-3 rounded-full text-white group-hover:rotate-45 transition-transform">
            <Zap size={20} fill="currentColor" />
          </div>
        </button>

        {/* Floating Icons Mimicking Image 2 */}
        <div className="absolute top-1/2 left-10 opacity-20 hidden lg:block"><Globe size={100} /></div>
        <div className="absolute top-1/3 right-20 opacity-20 hidden lg:block"><Shield size={80} /></div>
      </section>

      {/* ================= ADD-ONS SECTION (Reference Image 3 style) ================= */}
      <section className="px-10 py-32 bg-[#141414]">
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-col md:flex-row gap-20">
            
            {/* Left side: Toggles */}
            <div className="flex-1 space-y-6">
              <h2 className="text-4xl font-black tracking-tighter mb-10">AI-Powered <span className="text-orange-500">Insights </span></h2>
              {addons.map((item) => (
                <div 
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`p-6 rounded-[2rem] border cursor-pointer transition-all ${
                    activeTab === item.id ? 'bg-white/5 border-orange-500/50' : 'border-white/5 hover:border-white/10'
                  }`}
                >
                  <div className="flex items-center gap-4 mb-2">
                    <div className={`p-3 rounded-xl ${activeTab === item.id ? 'text-orange-500' : 'text-slate-500'}`}>
                      {item.icon}
                    </div>
                    <h4 className="font-black text-lg">{item.title}</h4>
                  </div>
                  {activeTab === item.id && (
                    <p className="text-slate-400 text-sm leading-relaxed ml-14 animate-in fade-in duration-500">
                      {item.desc}
                    </p>
                  )}
                </div>
              ))}
            </div>

            {/* Right side: Visual Placeholder */}
            <div className="flex-1 bg-[#0f0f0f] rounded-[3rem] border border-white/5 p-10 relative flex items-center justify-center group overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-orange-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
                <div className="text-center z-10">
                   <div className="text-orange-500 mb-6 flex justify-center">{addons.find(a => a.id === activeTab).icon}</div>
                   <h3 className="text-2xl font-black mb-4">Module Locked</h3>
                   <p className="text-slate-500 text-sm mb-8">This AI sub-system requires an active session to process your data.</p>
                   <button onClick={onGetStarted} className="bg-orange-500/10 text-orange-500 border border-orange-500/20 px-8 py-3 rounded-full font-bold hover:bg-orange-500 hover:text-white transition-all">
                      Unlock Module
                   </button>
                </div>
            </div>
          </div>
        </div>
      </section>

      {/* ================= CLASSIFICATION SECTION ================= */}
      <section className="px-10 py-32">
        <div className="max-w-6xl mx-auto text-center">
          <h2 className="text-4xl font-black tracking-tighter mb-16">What To Stock</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <CategoryCard onClick={onGetStarted} icon={<Cpu />} title="ICs & Chips" />
            <CategoryCard onClick={onGetStarted} icon={<Battery />} title="Power Systems" />
            <CategoryCard onClick={onGetStarted} icon={<Package />} title="Raw Materials" />
            <CategoryCard onClick={onGetStarted} icon={<BarChart3 />} title="End Products" />
          </div>
        </div>
      </section>

      {/* ================= FOOTER ================= */}
      <footer className="bg-[#0a0a0a] px-10 py-20 border-t border-white/5">
        <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-12">
          <div className="col-span-2">
            <div className="flex items-center gap-2 mb-6">
              <div className="w-6 h-6 bg-orange-500 rounded flex items-center justify-center text-[10px]">AI</div>
              <span className="font-black text-xl tracking-tighter uppercase">SalesInsight AI</span>
            </div>
            <p className="text-slate-500 text-sm max-w-xs leading-relaxed">
              SalesInsight AI Private Limited. <br />
              Pioneering predictive retail intelligence for the modern supply chain.
            </p>
          </div>
          <div>
            <h5 className="font-black text-[10px] tracking-widest text-slate-400 uppercase mb-6">Solution</h5>
            <ul className="text-sm text-slate-500 space-y-4 font-bold">
              <li className="hover:text-orange-500 cursor-pointer">Demand Forecast</li>
              <li className="hover:text-orange-500 cursor-pointer">Market Analysis</li>
              <li className="hover:text-orange-500 cursor-pointer">API Access</li>
            </ul>
          </div>
          <div>
            <h5 className="font-black text-[10px] tracking-widest text-slate-400 uppercase mb-6">Company</h5>
            <ul className="text-sm text-slate-500 space-y-4 font-bold">
              <li className="hover:text-orange-500 cursor-pointer">Privacy Policy</li>
              <li className="hover:text-orange-500 cursor-pointer">Terms of Service</li>
              <li className="hover:text-orange-500 cursor-pointer">Contact Support</li>
            </ul>
          </div>
        </div>
        <div className="max-w-6xl mx-auto mt-20 pt-8 border-t border-white/5 flex flex-col md:flex-row justify-between items-center text-[10px] font-black text-slate-600 tracking-[0.2em]">
          <p>© 2026 SALESINSIGHT AI PVT. LTD. ALL RIGHTS RESERVED.</p>
          <div className="flex gap-8 mt-4 md:mt-0">
             <span>LONDON / NEW YORK / MUMBAI</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

function CategoryCard({ icon, title, onClick }) {
  return (
    <div 
      onClick={onClick}
      className="bg-[#1a1a1a] p-10 rounded-[2.5rem] border border-white/5 hover:border-orange-500/40 transition-all cursor-pointer group"
    >
      <div className="text-slate-500 group-hover:text-orange-500 transition-colors mb-4 flex justify-center">
        {React.cloneElement(icon, { size: 32 })}
      </div>
      <h5 className="font-bold text-sm text-slate-300 group-hover:text-white transition-colors">{title}</h5>
    </div>
  );
}