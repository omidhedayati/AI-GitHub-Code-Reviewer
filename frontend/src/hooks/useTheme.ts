import { useEffect, useState } from "react";

const THEME_KEY = "reviewer-theme";

export type Theme = "light" | "dark";

export function useTheme(): {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
} {
  const [theme, setThemeState] = useState<Theme>(() => {
    const stored = localStorage.getItem(THEME_KEY);
    if (stored === "light" || stored === "dark") return stored;
    return window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";
  });

  useEffect(() => {
    const root = document.documentElement;
    if (theme === "dark") {
      root.classList.add("dark");
    } else {
      root.classList.remove("dark");
    }
    localStorage.setItem(THEME_KEY, theme);
  }, [theme]);

  const setTheme = (value: Theme) => setThemeState(value);

  const toggleTheme = () =>
    setThemeState((current) => (current === "dark" ? "light" : "dark"));

  return { theme, setTheme, toggleTheme };
}
