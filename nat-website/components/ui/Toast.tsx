"use client";

import { createContext, useCallback, useContext, useRef, useState } from "react";

type ToastVariant = "success" | "error";
type ToastItem = { id: number; message: string; variant: ToastVariant };

type ToastContextValue = {
  showToast: (message: string, variant?: ToastVariant) => void;
};

const ToastContext = createContext<ToastContextValue | null>(null);

const AUTO_DISMISS_MS = 5000;

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within <ToastProvider>");
  return ctx;
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const nextId = useRef(0);
  const timers = useRef(new Map<number, ReturnType<typeof setTimeout>>());

  const dismiss = useCallback((id: number) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
    const timer = timers.current.get(id);
    if (timer) {
      clearTimeout(timer);
      timers.current.delete(id);
    }
  }, []);

  const scheduleDismiss = useCallback(
    (id: number) => {
      const timer = setTimeout(() => dismiss(id), AUTO_DISMISS_MS);
      timers.current.set(id, timer);
    },
    [dismiss]
  );

  const showToast = useCallback(
    (message: string, variant: ToastVariant = "success") => {
      const id = nextId.current++;
      setToasts((prev) => [...prev, { id, message, variant }]);
      scheduleDismiss(id);
    },
    [scheduleDismiss]
  );

  function pauseTimer(id: number) {
    const timer = timers.current.get(id);
    if (timer) {
      clearTimeout(timer);
      timers.current.delete(id);
    }
  }

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      {/* Fixed corner, non-blocking, role="status" per constitution Principle II. */}
      <div className="pointer-events-none fixed bottom-[var(--spacing-24)] right-[var(--spacing-24)] z-50 flex flex-col gap-[var(--spacing-12)]">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            role="status"
            onMouseEnter={() => pauseTimer(toast.id)}
            onMouseLeave={() => scheduleDismiss(toast.id)}
            onFocus={() => pauseTimer(toast.id)}
            onBlur={() => scheduleDismiss(toast.id)}
            tabIndex={0}
            className={
              "pointer-events-auto rounded-(--radius-card) border px-[var(--spacing-18)] py-[var(--spacing-12)] text-[length:var(--text-nav-label)] shadow-lg " +
              (toast.variant === "success"
                ? "border-(--color-teal) bg-(--color-surface) text-(--color-bone)"
                : "border-red-500 bg-(--color-surface) text-(--color-bone)")
            }
          >
            {toast.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}
