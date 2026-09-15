import React from 'react';
import {
  Clock,
  Search,
  FolderHeart,
  Copy,
  Sparkles,
  Plus,
  ShieldCheck,
  Layers,
  LucideIcon,
} from 'lucide-react';

interface NavbarProps {
  activeTab: 'timeline' | 'search' | 'events' | 'duplicates' | 'flashbacks';
  setActiveTab: (
    tab: 'timeline' | 'search' | 'events' | 'duplicates' | 'flashbacks'
  ) => void;
  onOpenUpload: () => void;
  duplicateCount: number;
}

interface NavItem {
  id: 'timeline' | 'search' | 'events' | 'duplicates' | 'flashbacks';
  label: string;
  icon: LucideIcon;
  badge?: number | null;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  onOpenUpload,
  duplicateCount,
}) => {
  const navItems: NavItem[] = [
    { id: 'timeline', label: 'Timeline', icon: Clock },
    { id: 'search', label: 'Semantic Search', icon: Search },
    { id: 'events', label: 'Events & Stories', icon: Layers },
    {
      id: 'duplicates',
      label: 'Duplicate Review',
      icon: Copy,
      badge: duplicateCount > 0 ? duplicateCount : null,
    },
    { id: 'flashbacks', label: 'On This Day', icon: Sparkles },
  ];

  return (
    <header className="sticky top-0 z-40 w-full glass-panel border-b border-vault-border/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand Logo */}
        <div
          className="flex items-center gap-3 cursor-pointer group"
          onClick={() => setActiveTab('timeline')}
        >
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-accent-purple via-accent-indigo to-accent-cyan p-0.5 shadow-glow-purple group-hover:scale-105 transition-transform duration-300">
            <div className="w-full h-full bg-vault-darkest rounded-[10px] flex items-center justify-center">
              <FolderHeart className="w-5 h-5 text-accent-purple" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-lg tracking-tight text-white">
                Memory<span className="text-accent-purple">Vault</span>
              </span>
              <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <ShieldCheck className="w-3 h-3 mr-0.5" /> Local Private
              </span>
            </div>
            <p className="text-[11px] text-vault-muted leading-none hidden sm:block">
              Zero-Tag AI Life Vault
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="hidden md:flex items-center gap-1 bg-vault-dark/80 p-1.5 rounded-xl border border-vault-border">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-sm font-medium transition-all duration-200 relative ${
                  isActive
                    ? 'bg-accent-purple/20 text-white border border-accent-purple/50 shadow-glow-purple'
                    : 'text-vault-muted hover:text-white hover:bg-vault-card'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-accent-purple' : ''}`} />
                <span>{item.label}</span>
                {item.badge !== null && item.badge !== undefined && (
                  <span className="ml-1 px-1.5 py-0.2 rounded-full text-[10px] font-bold bg-accent-amber text-black animate-pulse">
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Action Button */}
        <div className="flex items-center gap-3">
          <button
            onClick={onOpenUpload}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-accent-purple via-accent-indigo to-accent-cyan text-white font-semibold text-sm shadow-glow-purple hover:opacity-95 hover:scale-[1.02] active:scale-[0.98] transition-all duration-200"
            id="add-memory-btn"
          >
            <Plus className="w-4 h-4" />
            <span className="hidden sm:inline">Add Memory</span>
          </button>
        </div>
      </div>

      {/* Mobile Nav Bar */}
      <div className="md:hidden flex items-center justify-around py-2 border-t border-vault-border/60 bg-vault-darkest/95">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`flex flex-col items-center gap-1 p-1 text-xs relative ${
                isActive ? 'text-accent-purple font-semibold' : 'text-vault-muted'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{item.label}</span>
              {item.badge !== null && item.badge !== undefined && (
                <span className="absolute top-0 right-1 px-1 rounded-full text-[9px] font-bold bg-accent-amber text-black">
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>
    </header>
  );
};
