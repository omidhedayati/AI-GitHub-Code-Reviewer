import {
  createContext,
  useCallback,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import {
  ACCESS_TOKEN_KEY,
  REFRESH_TOKEN_KEY,
  apiClient,
  setAccessTokenProvider,
} from "../api/client";
import type { User } from "../api/types";

export interface AuthContextValue {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (
    email: string,
    password: string,
    fullName?: string,
  ) => Promise<void>;
  logout: () => void;
}

export const AuthContext = createContext<AuthContextValue | null>(null);

function persistTokens(accessToken: string, refreshToken: string): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
}

function clearTokens(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const logout = useCallback(() => {
    clearTokens();
    setAccessToken(null);
    setUser(null);
  }, []);

  const applyAuthResponse = useCallback(
    (authUser: User, tokens: { access_token: string; refresh_token: string }) => {
      persistTokens(tokens.access_token, tokens.refresh_token);
      setAccessToken(tokens.access_token);
      setUser(authUser);
    },
    [],
  );

  const login = useCallback(
    async (email: string, password: string) => {
      const response = await apiClient.login({ email, password });
      applyAuthResponse(response.user, response.tokens);
    },
    [applyAuthResponse],
  );

  const register = useCallback(
    async (email: string, password: string, fullName?: string) => {
      const response = await apiClient.register({
        email,
        password,
        full_name: fullName,
      });
      applyAuthResponse(response.user, response.tokens);
    },
    [applyAuthResponse],
  );

  useEffect(() => {
    setAccessTokenProvider(() => accessToken);
  }, [accessToken]);

  useEffect(() => {
    async function bootstrapAuth() {
      const storedAccess = localStorage.getItem(ACCESS_TOKEN_KEY);
      const storedRefresh = localStorage.getItem(REFRESH_TOKEN_KEY);

      if (!storedAccess) {
        setIsLoading(false);
        return;
      }

      setAccessToken(storedAccess);

      try {
        const currentUser = await apiClient.getMe();
        setUser(currentUser);
      } catch {
        if (!storedRefresh) {
          logout();
          setIsLoading(false);
          return;
        }

        try {
          const tokens = await apiClient.refresh(storedRefresh);
          persistTokens(tokens.access_token, tokens.refresh_token);
          setAccessToken(tokens.access_token);
          const currentUser = await apiClient.getMe();
          setUser(currentUser);
        } catch {
          logout();
        }
      } finally {
        setIsLoading(false);
      }
    }

    void bootstrapAuth();
  }, [logout]);

  const value = useMemo(
    () => ({
      user,
      isAuthenticated: user !== null,
      isLoading,
      login,
      register,
      logout,
    }),
    [user, isLoading, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
