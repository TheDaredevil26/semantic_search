import { createContext, useContext, useState, useCallback } from 'react';

const ToastContext = createContext(null);

/**
 * Toast notification provider. Wrap your app with this to use useToast().
 */
export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const addToast = useCallback((message, type = 'success', duration = 3000) => {
    const id = Date.now() + Math.random();
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, duration);
  }, []);

  const removeToast = useCallback((id) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ addToast }}>
      {children}
      {/* Toast container */}
      <div className="fixed bottom-6 right-6 z-[100] flex flex-col gap-2 pointer-events-none">
        {toasts.map(toast => (
          <div
            key={toast.id}
            className={`pointer-events-auto toast-enter flex items-center gap-2 px-4 py-3 rounded-lg shadow-lg text-sm font-medium cursor-pointer transition-all ${
              toast.type === 'error'
                ? 'bg-red-50 text-red-700 border border-red-200'
                : toast.type === 'info'
                ? 'bg-blue-50 text-blue-700 border border-blue-200'
                : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
            }`}
            onClick={() => removeToast(toast.id)}
          >
            <span>{toast.type === 'error' ? '⚠' : toast.type === 'info' ? 'ℹ' : '✓'}</span>
            <span>{toast.message}</span>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

/**
 * Hook to show toast notifications.
 */
export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used within ToastProvider');
  return ctx;
}
