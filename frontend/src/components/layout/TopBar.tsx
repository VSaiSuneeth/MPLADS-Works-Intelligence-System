import React from 'react';
import { useAuth } from '../../context/AuthContext';
import { LogOut, Building, Menu } from 'lucide-react';

interface TopBarProps {
  onToggleMobileMenu?: () => void;
}

export const TopBar: React.FC<TopBarProps> = ({ onToggleMobileMenu }) => {
  const { user, logout, jurisdictions, selectedJurisdictionId, setSelectedJurisdictionId } = useAuth();

  const userRolesText = user && Array.isArray(user.roles) ? user.roles.join(', ') : 'DISTRICT_OFFICER';

  return (
    <header className="bg-[#0A2540] text-white border-b-4 border-b-[#0B3D6E] shadow-sm sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between">
        {/* Emblem & Title */}
        <div className="flex items-center space-x-3">
          {onToggleMobileMenu && (
            <button
              onClick={onToggleMobileMenu}
              className="md:hidden p-1.5 text-slate-200 hover:text-white hover:bg-blue-900 rounded-xs transition focus:outline-none"
              title="Toggle Navigation Menu"
              aria-label="Toggle Navigation Menu"
            >
              <Menu className="w-5 h-5" />
            </button>
          )}
          <div className="w-8 h-8 rounded-full bg-amber-500/20 border border-amber-400/40 flex items-center justify-center text-amber-300 font-serif font-bold text-xs shrink-0">
            🇮🇳
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-serif font-bold text-sm tracking-tight text-white hidden sm:inline">
                MPLADS Works Intelligence Engine
              </span>
              <span className="font-serif font-bold text-sm tracking-tight text-white sm:hidden">
                MPLADS Engine
              </span>
              <span className="text-[9px] bg-blue-900/80 text-blue-200 px-1.5 py-0.5 rounded-xs font-mono uppercase border border-blue-700">
                GOV.IN
              </span>
            </div>
            <p className="text-[10px] text-slate-300 font-sans hidden sm:block">
              Ministry of Statistics & Programme Implementation (MoSPI)
            </p>
          </div>
        </div>


        {/* User Scope & Persona Switcher */}
        <div className="flex items-center space-x-4">
          {/* Jurisdiction Dropdown */}
          {Array.isArray(jurisdictions) && jurisdictions.length > 0 && (
            <div className="flex items-center space-x-1.5 text-xs">
              <Building className="w-3.5 h-3.5 text-blue-300" />
              <select
                value={selectedJurisdictionId || ''}
                onChange={(e) => setSelectedJurisdictionId(e.target.value)}
                className="bg-[#0B3D6E] text-white text-xs border border-blue-700 rounded-xs px-2 py-1 font-medium focus:outline-none"
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

          {/* User Profile */}
          {user && (
            <div className="flex items-center space-x-3 border-l border-blue-900/80 pl-4">
              <div className="text-right text-xs">
                <span className="font-bold block text-white leading-tight">
                  {user.fullName || user.username || 'User'}
                </span>
                <span className="text-[10px] text-amber-300 font-mono font-semibold uppercase">
                  {userRolesText}
                </span>
              </div>

              <button
                onClick={logout}
                className="p-1.5 text-slate-300 hover:text-white hover:bg-blue-900 rounded-xs transition"
                title="Sign Out"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
