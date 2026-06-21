"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useSyncExternalStore,
} from "react";

type Theme = "light" | "dark";

type ThemeContextValue = {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
};

const THEME_STORAGE_KEY = "rag-platform-theme";
const THEME_CHANGE_EVENT = "rag-platform-theme-change";

const ThemeContext = createContext<ThemeContextValue | null>(null);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const theme = useSyncExternalStore(
    subscribeToThemePreference,
    getThemeSnapshot,
    getServerThemeSnapshot,
  );

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
  }, [theme]);

  const setTheme = useCallback((nextTheme: Theme) => {
    window.localStorage.setItem(THEME_STORAGE_KEY, nextTheme);
    window.dispatchEvent(new Event(THEME_CHANGE_EVENT));
  }, []);

  const toggleTheme = useCallback(() => {
    setTheme(getThemeSnapshot() === "dark" ? "light" : "dark");
  }, [setTheme]);

  const value = useMemo(
    () => ({
      theme,
      setTheme,
      toggleTheme,
    }),
    [setTheme, theme, toggleTheme],
  );

  return (
    <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
  );
}

export function useTheme() {
  const value = useContext(ThemeContext);

  if (!value) {
    throw new Error("useTheme must be used within ThemeProvider.");
  }

  return value;
}

function subscribeToThemePreference(callback: () => void) {
  window.addEventListener("storage", callback);
  window.addEventListener(THEME_CHANGE_EVENT, callback);

  return () => {
    window.removeEventListener("storage", callback);
    window.removeEventListener(THEME_CHANGE_EVENT, callback);
  };
}

function getThemeSnapshot(): Theme {
  const storedTheme = window.localStorage.getItem(THEME_STORAGE_KEY);

  return storedTheme === "dark" || storedTheme === "light"
    ? storedTheme
    : "light";
}

function getServerThemeSnapshot(): Theme {
  return "light";
}
