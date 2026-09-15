import React, { Component, ErrorInfo, ReactNode } from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.tsx';
import './index.css';

interface Props {
  children?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught React Error:', error, errorInfo);
  }

  private handleReset = () => {
    localStorage.clear();
    window.location.href = '/login';
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-slate-900 flex flex-col justify-center items-center p-6 text-slate-900 font-sans">
          <div className="max-w-lg w-full bg-white border border-gray-300 border-t-8 border-t-red-700 rounded-sm p-8 space-y-4 shadow-2xl">
            <div className="flex items-center space-x-3 text-red-700 border-b border-gray-200 pb-3">
              <span className="text-2xl">⚠️</span>
              <div>
                <h1 className="text-base font-bold uppercase tracking-wide">Governance Portal Session Recovery</h1>
                <p className="text-xs text-slate-600">A client-side state error occurred in the browser context.</p>
              </div>
            </div>

            <p className="text-xs text-slate-700 font-mono bg-red-50 p-3 border border-red-200 rounded-sm">
              {this.state.error?.message || 'Unknown React rendering exception.'}
            </p>

            <div className="flex justify-end space-x-2 pt-2">
              <button
                onClick={this.handleReset}
                className="bg-[#0B3D6E] text-white text-xs font-bold px-4 py-2 rounded-sm hover:bg-[#0A2540] transition"
              >
                Reset Session & Return to Login
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>,
);
