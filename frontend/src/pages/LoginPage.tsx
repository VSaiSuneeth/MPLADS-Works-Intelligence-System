import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ShieldCheck, UserCheck, KeyRound, AlertCircle } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const { login, isLoading } = useAuth();
  const navigate = useNavigate();

  const [username, setUsername] = useState('district.officer');
  const [password, setPassword] = useState('demo-password');
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await login(username, password);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Invalid credentials. Please verify username and password.');
    }
  };

  const handleQuickSwitch = (u: string) => {
    setUsername(u);
    setPassword('demo-password');
  };

  return (
    <div className="min-h-screen bg-slate-900 flex flex-col justify-center items-center p-4 text-slate-900 font-sans">
      <div className="max-w-md w-full bg-white border border-gray-300 border-t-8 border-t-[#0B3D6E] rounded-xs shadow-2xl p-8 space-y-6">
        {/* Header */}
        <div className="text-center space-y-2 border-b border-gray-200 pb-4">
          <div className="w-12 h-12 rounded-full bg-amber-500/20 border border-amber-400/40 flex items-center justify-center text-amber-600 font-serif font-bold text-xl mx-auto">
            🇮🇳
          </div>
          <h1 className="text-lg font-serif font-bold text-[#0A2540] tracking-tight">
            MPLADS Works Intelligence & Review System
          </h1>
          <p className="text-xs text-slate-600 font-sans">
            Government of India — Ministry of Statistics & Programme Implementation
          </p>
        </div>

        {error && (
          <div className="p-3 bg-red-50 border border-red-300 rounded-xs text-xs text-red-950 flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-red-700 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          <div>
            <label className="text-slate-700 font-bold block mb-1 uppercase tracking-wider text-[10px]">
              User Credential ID / Username *
            </label>
            <div className="relative">
              <UserCheck className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="e.g. district.officer"
                className="gov-input pl-9 font-mono"
                required
              />
            </div>
          </div>

          <div>
            <label className="text-slate-700 font-bold block mb-1 uppercase tracking-wider text-[10px]">
              Password *
            </label>
            <div className="relative">
              <KeyRound className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="gov-input pl-9 font-mono"
                required
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="gov-btn-primary w-full py-2.5 text-xs uppercase tracking-wider font-bold"
          >
            {isLoading ? 'Authenticating...' : 'Sign In to Governance Portal'}
          </button>
        </form>

        {/* Persona Quick Switcher */}
        <div className="pt-4 border-t border-gray-200 space-y-2">
          <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block text-center">
            DEMO PERSONA QUICK SWITCHER
          </span>
          <div className="grid grid-cols-1 gap-1.5 text-xs">
            <button
              onClick={() => handleQuickSwitch('district.officer')}
              className={`p-2 rounded-xs border text-left transition flex justify-between items-center ${
                username === 'district.officer'
                  ? 'bg-blue-50 border-[#0B3D6E] text-[#0B3D6E] font-bold'
                  : 'bg-slate-50 border-gray-300 text-slate-700 hover:bg-slate-100'
              }`}
            >
              <div>
                <span className="block font-bold">Delhi Nodal Officer</span>
                <span className="text-[10px] opacity-75">District Officer (Delhi Scope)</span>
              </div>
              <span className="font-mono text-[10px] bg-slate-200 px-1.5 py-0.5 rounded-xs">district.officer</span>
            </button>

            <button
              onClick={() => handleQuickSwitch('auditor.demo')}
              className={`p-2 rounded-xs border text-left transition flex justify-between items-center ${
                username === 'auditor.demo'
                  ? 'bg-blue-50 border-[#0B3D6E] text-[#0B3D6E] font-bold'
                  : 'bg-slate-50 border-gray-300 text-slate-700 hover:bg-slate-100'
              }`}
            >
              <div>
                <span className="block font-bold">Senior State Auditor</span>
                <span className="text-[10px] opacity-75">Auditor (State-wide Scope)</span>
              </div>
              <span className="font-mono text-[10px] bg-slate-200 px-1.5 py-0.5 rounded-xs">auditor.demo</span>
            </button>

            <button
              onClick={() => handleQuickSwitch('admin.demo')}
              className={`p-2 rounded-xs border text-left transition flex justify-between items-center ${
                username === 'admin.demo'
                  ? 'bg-blue-50 border-[#0B3D6E] text-[#0B3D6E] font-bold'
                  : 'bg-slate-50 border-gray-300 text-slate-700 hover:bg-slate-100'
              }`}
            >
              <div>
                <span className="block font-bold">System Administrator</span>
                <span className="text-[10px] opacity-75">Admin (Full Control + CSV Import)</span>
              </div>
              <span className="font-mono text-[10px] bg-slate-200 px-1.5 py-0.5 rounded-xs">admin.demo</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
