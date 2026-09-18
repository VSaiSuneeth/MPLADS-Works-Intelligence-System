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
  Building,
  LogOut,
  User,
} from 'lucide-react';

interface SidebarProps {
  isMobileOpen?: boolean;
  onCloseMobile?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ isMobileOpen, onCloseMobile }) => {
  const { user, logout, jurisdictions, selectedJurisdictionId, setSelectedJurisdictionId } = useAuth();
  const isAdmin = user && Array.isArray(user.roles) ? user.roles.includes('ADMIN') : false;
  const userRolesText = user && Array.isArray(user.roles) ? user.roles.join(', ') : 'DISTRICT_OFFICER';

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

      <div className="mt-6 p-3 bg-slate-50 border border-gray-300 rounded-xs space-y-1 text-[11px] text-slate-600">
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
          <div className="relative w-80 max-w-[85vw] bg-white h-full shadow-2xl p-4 flex flex-col justify-between font-sans z-50 overflow-y-auto">
            <div className="space-y-4">
              <div className="flex items-center justify-between border-b border-gray-200 pb-3">
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

              {/* Mobile District Selector */}
              {Array.isArray(jurisdictions) && jurisdictions.length > 0 && (
                <div className="p-3 bg-blue-50 border border-blue-200 rounded-xs space-y-1 text-xs">
                  <span className="font-bold text-[#0B3D6E] uppercase text-[10px] flex items-center gap-1">
                    <Building className="w-3.5 h-3.5 text-blue-700" />
                    <span>Authorized District Scope</span>
                  </span>
                  <select
                    value={selectedJurisdictionId || ''}
                    onChange={(e) => {
                      setSelectedJurisdictionId(e.target.value);
                      if (onCloseMobile) onCloseMobile();
                    }}
                    className="w-full bg-white text-slate-900 text-xs border border-blue-300 rounded-xs p-1.5 font-medium focus:outline-none"
                  >
                    <option value="">All Authorized Districts</option>
                    {jurisdictions.map((j) => (
                      <option key={j.id} value={j.id}>
                        {j.districtName} ({j.districtCode})
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {renderNav(onCloseMobile)}
            </div>

            {/* Mobile User Profile Footer */}
            {user && (
              <div className="pt-4 border-t border-gray-200 mt-4 space-y-3">
                <div className="flex items-center justify-between p-2.5 bg-slate-100 border border-slate-300 rounded-xs text-xs">
                  <div className="flex items-center space-x-2 min-w-0">
                    <User className="w-4 h-4 text-slate-600 shrink-0" />
                    <div className="min-w-0">
                      <span className="font-bold block text-slate-900 leading-tight truncate">
                        {user.fullName || user.username || 'User'}
                      </span>
                      <span className="text-[10px] text-blue-800 font-mono font-semibold uppercase block truncate">
                        {userRolesText}
                      </span>
                    </div>
                  </div>

                  <button
                    onClick={() => {
                      if (onCloseMobile) onCloseMobile();
                      logout();
                    }}
                    className="p-1.5 text-slate-700 hover:text-white hover:bg-red-700 bg-white border border-gray-300 rounded-xs transition shrink-0"
                    title="Sign Out"
                  >
                    <LogOut className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
};
