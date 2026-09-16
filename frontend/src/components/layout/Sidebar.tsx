import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import {
  LayoutDashboard,
  AlertTriangle,
  FolderGit2,
  History,
  FileSpreadsheet,
  SlidersHorizontal,
  X,
} from 'lucide-react';

interface SidebarProps {
  isMobileOpen?: boolean;
  onCloseMobile?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ isMobileOpen, onCloseMobile }) => {
  const { user } = useAuth();
  const isAdmin = user && Array.isArray(user.roles) ? user.roles.includes('ADMIN') : false;

  const navItems = [
    { to: '/dashboard', label: 'Governance Dashboard', icon: LayoutDashboard },
    { to: '/queue', label: 'Prioritized Risk Queue', icon: AlertTriangle },
    { to: '/simulator', label: 'What-If Impact Simulator', icon: SlidersHorizontal },
    { to: '/cases', label: 'Review Cases', icon: FolderGit2 },
    { to: '/audit', label: 'System Audit Trail', icon: History },
  ];

  if (isAdmin) {
    navItems.push({ to: '/admin', label: 'Data Import & Recalculation', icon: FileSpreadsheet });
  }

  const renderNav = (onItemClick?: () => void) => (
    <>
      <div className="space-y-1">
        <span className="text-[10px] font-bold text-slate-700 tracking-wider uppercase px-3 mb-2 block">
          MONITORING MODULES
        </span>
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={onItemClick}
              className={({ isActive }) =>
                `flex items-center space-x-2.5 px-3 py-2.5 rounded-xs text-xs font-bold transition ${
                  isActive
                    ? 'bg-[#0B3D6E] text-white shadow-xs'
                    : 'text-slate-700 hover:bg-slate-100 hover:text-slate-900'
                }`
              }
            >
              <Icon className="w-4 h-4 shrink-0" />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </div>

      <div className="mt-8 p-3 bg-slate-50 border border-gray-300 rounded-xs space-y-1 text-[11px] text-slate-600">
        <span className="font-bold text-slate-800 uppercase tracking-wider text-[10px] block">
          Explainable AI Governance
        </span>
        <p className="leading-tight text-slate-600">
          Prioritizes works for physical verification without automated fraud assertions.
        </p>
      </div>
    </>
  );

  return (
    <>
      {/* Desktop Sidebar (hidden on mobile, fixed 256px on md+) */}
      <aside className="hidden md:block w-64 bg-white border-r border-gray-300 min-h-[calc(100vh-3.5rem)] p-4 shrink-0 font-sans">
        {renderNav()}
      </aside>

      {/* Mobile Slide-over Overlay & Drawer (md:hidden) */}
      {isMobileOpen && (
        <div className="md:hidden fixed inset-0 z-50 flex">
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs transition-opacity"
            onClick={onCloseMobile}
            aria-hidden="true"
          />

          {/* Drawer Content */}
          <div className="relative w-72 bg-white h-full shadow-2xl p-4 flex flex-col justify-between font-sans z-50 overflow-y-auto">
            <div>
              <div className="flex items-center justify-between border-b border-gray-200 pb-3 mb-4">
                <span className="font-serif font-bold text-sm text-[#0A2540]">
                  Navigation Menu
                </span>
                <button
                  onClick={onCloseMobile}
                  className="p-1.5 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-xs transition"
                  aria-label="Close menu"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              {renderNav(onCloseMobile)}
            </div>
          </div>
        </div>
      )}
    </>
  );
};

