import React, { createContext, useContext, useState, useEffect } from 'react';
import { User, Jurisdiction } from '../types';
import { apiClient } from '../api/client';

interface AuthContextType {
  user: User | null;
  token: string | null;
  jurisdictions: Jurisdiction[];
  selectedJurisdictionId: string;
  setSelectedJurisdictionId: (id: string) => void;
  login: (uname: string, pwd: string) => Promise<void>;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => {
    try {
      const cached = localStorage.getItem('mplads_auth_user');
      if (!cached) return null;
      const parsed = JSON.parse(cached);
      if (parsed && typeof parsed === 'object') {
        if (!Array.isArray(parsed.roles)) parsed.roles = ['DISTRICT_OFFICER'];
        return parsed;
      }
      return null;
    } catch {
      localStorage.removeItem('mplads_auth_user');
      return null;
    }
  });

  const [token, setToken] = useState<string | null>(() => localStorage.getItem('mplads_auth_token'));
  const [jurisdictions, setJurisdictions] = useState<Jurisdiction[]>([]);
  const [selectedJurisdictionId, setSelectedJurisdictionId] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);

  useEffect(() => {
    if (token) {
      apiClient.get('/auth/me')
        .then((res) => {
          const u = res.data.user || res.data;
          if (u && typeof u === 'object') {
            if (!Array.isArray(u.roles)) {
              u.roles = ['DISTRICT_OFFICER'];
            }
            const jList = u.jurisdictions || [];
            setUser(u);
            if (Array.isArray(jList)) setJurisdictions(jList);
            localStorage.setItem('mplads_auth_user', JSON.stringify(u));
            
            if (!selectedJurisdictionId && u?.defaultJurisdictionId) {
              setSelectedJurisdictionId(u.defaultJurisdictionId);
            }
          }
        })
        .catch(() => {
          // If token is truly invalid (401), logout
          logout();
        });
    }
  }, [token]);

  const login = async (uname: string, pwd: string) => {
    setIsLoading(true);
    try {
      const res = await apiClient.post('/auth/login', { username: uname, password: pwd });
      const accessToken = res.data.accessToken;
      const u = res.data.user || res.data;
      if (u && !Array.isArray(u.roles)) {
        u.roles = ['DISTRICT_OFFICER'];
      }
      
      setToken(accessToken);
      setUser(u);
      localStorage.setItem('mplads_auth_token', accessToken);
      localStorage.setItem('mplads_auth_user', JSON.stringify(u));
      
      if (u?.defaultJurisdictionId) {
        setSelectedJurisdictionId(u.defaultJurisdictionId);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    setSelectedJurisdictionId('');
    localStorage.removeItem('mplads_auth_token');
    localStorage.removeItem('mplads_auth_user');
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        jurisdictions,
        selectedJurisdictionId,
        setSelectedJurisdictionId,
        login,
        logout,
        isLoading,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
