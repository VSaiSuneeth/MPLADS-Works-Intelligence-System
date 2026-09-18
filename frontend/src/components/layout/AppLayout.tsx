import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { TopBar } from './TopBar';
import { Sidebar } from './Sidebar';

export const AppLayout: React.FC = () => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col font-sans text-slate-900 w-full max-w-full overflow-x-hidden">
      <TopBar onToggleMobileMenu={() => setIsMobileMenuOpen((prev) => !prev)} />
      <div className="flex flex-1 max-w-7xl w-full mx-auto min-w-0">
        <Sidebar isMobileOpen={isMobileMenuOpen} onCloseMobile={() => setIsMobileMenuOpen(false)} />
        <main className="flex-1 min-w-0 p-3 sm:p-6 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
