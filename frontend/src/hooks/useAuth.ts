import { useState, useEffect, useCallback } from "react";
import API from "@/services/api";
import type { User } from "@/types";

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      const r = await API.get("/auth/me");
      setUser(r.data);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const onLogout = () => {
      setUser(null);
      setLoading(false);
    };
    window.addEventListener("auth:logout", onLogout);
    return () => window.removeEventListener("auth:logout", onLogout);
  }, [load]);

  const login = async (email: string, password: string) => {
    const r = await API.post("/auth/login", { email, password });
    await load();
    return r.data;
  };

  const register = async (data: { email: string; password: string; full_name: string; phone?: string }) => {
    const r = await API.post("/auth/register", data);
    await load();
    return r.data;
  };

  const logout = async () => {
    await API.post("/auth/logout");
    setUser(null);
    setLoading(false);
  };

  return { user, loading, login, register, logout };
}
