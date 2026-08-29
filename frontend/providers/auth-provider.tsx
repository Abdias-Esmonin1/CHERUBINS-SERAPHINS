"use client";

import { createContext, useCallback, useContext, type ReactNode } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { authApi } from "@/lib/api/auth";
import { ApiClientError } from "@/lib/api/client";
import type { LoginRequest, RegisterRequest } from "@/types/auth";
import type { UserPublicRead } from "@/types/user";

const ME_QUERY_KEY = ["auth", "me"] as const;

interface AuthContextValue {
  user: UserPublicRead | null;
  /** true uniquement pendant la résolution initiale de /me. */
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (payload: LoginRequest) => Promise<UserPublicRead>;
  register: (payload: RegisterRequest) => Promise<UserPublicRead>;
  logout: () => Promise<void>;
  isLoginPending: boolean;
  isRegisterPending: boolean;
  isLogoutPending: boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);

/**
 * GET /auth/me répond 401 lorsqu'il n'y a simplement pas de session
 * valide — ce n'est pas une erreur applicative, juste "utilisateur
 * anonyme". Toute autre erreur (réseau, 5xx) doit rester une vraie
 * erreur de query, pas être avalée silencieusement.
 */
async function fetchCurrentUser(): Promise<UserPublicRead | null> {
  try {
    const { data } = await authApi.me();
    return data;
  } catch (error) {
    if (error instanceof ApiClientError && error.status === 401) {
      return null;
    }
    throw error;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();

  const meQuery = useQuery({
    queryKey: ME_QUERY_KEY,
    queryFn: fetchCurrentUser,
    staleTime: 60 * 1000,
    retry: false,
  });

  const loginMutation = useMutation({
    mutationFn: (payload: LoginRequest) => authApi.login(payload),
    onSuccess: ({ data }) => {
      queryClient.setQueryData(ME_QUERY_KEY, data);
    },
  });

  const registerMutation = useMutation({
    mutationFn: (payload: RegisterRequest) => authApi.register(payload),
    onSuccess: ({ data }) => {
      // register pose le cookie HttpOnly immédiatement côté backend
      // (auto-login) — pas besoin d'un login() séparé après inscription.
      queryClient.setQueryData(ME_QUERY_KEY, data);
    },
  });

  const logoutMutation = useMutation({
    mutationFn: () => authApi.logout(),
    onSuccess: () => {
      queryClient.setQueryData(ME_QUERY_KEY, null);
    },
  });

  const login = useCallback(
    async (payload: LoginRequest) => {
      const result = await loginMutation.mutateAsync(payload);
      return result.data;
    },
    [loginMutation]
  );

  const register = useCallback(
    async (payload: RegisterRequest) => {
      const result = await registerMutation.mutateAsync(payload);
      return result.data;
    },
    [registerMutation]
  );

  const logout = useCallback(async () => {
    await logoutMutation.mutateAsync();
  }, [logoutMutation]);

  const value: AuthContextValue = {
    user: meQuery.data ?? null,
    isLoading: meQuery.isPending,
    isAuthenticated: Boolean(meQuery.data),
    login,
    register,
    logout,
    isLoginPending: loginMutation.isPending,
    isRegisterPending: registerMutation.isPending,
    isLogoutPending: logoutMutation.isPending,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth doit être utilisé à l'intérieur d'un AuthProvider.");
  }
  return context;
}
