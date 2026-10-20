import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";
import { Zap, AlertCircle, Loader2, ShieldCheck, UserCheck, Lock, Mail } from "lucide-react";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleLogin = async (userEmail: string, userPass: string) => {
    setError("");
    setLoading(true);
    try {
      const data = await login(userEmail, userPass);
      // Check role or default to customer dashboard
      if (userEmail.toLowerCase().includes("admin") || data?.role === "admin") {
        navigate("/admin/dashboard", { replace: true });
      } else {
        navigate("/customer/dashboard", { replace: true });
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || "Invalid email or password");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setError("Please fill in both email and password");
      return;
    }
    handleLogin(email, password);
  };

  const fillDemo = (demoEmail: string, demoPass: string) => {
    setEmail(demoEmail);
    setPassword(demoPass);
    handleLogin(demoEmail, demoPass);
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center p-4 bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 text-slate-100">
      <div className="w-full max-w-md">
        <div className="bg-slate-900/90 backdrop-blur-md p-8 rounded-2xl shadow-2xl border border-slate-800">
          {/* Logo & Header */}
          <div className="flex items-center gap-3 mb-6">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-blue-600 to-cyan-400 flex items-center justify-center shadow-lg shadow-blue-500/30">
              <Zap className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="font-bold text-xl text-white tracking-tight">Smart EV Charging</h1>
              <p className="text-xs text-slate-400">Station Management System</p>
            </div>
          </div>

          <h2 className="text-lg font-semibold text-slate-200 mb-4">Sign in to your account</h2>

          {error && (
            <div className="mb-4 p-3 rounded-lg bg-red-950/60 text-red-300 text-sm border border-red-800/80 flex items-center gap-2">
              <AlertCircle className="h-4 w-4 shrink-0 text-red-400" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">Email address</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                  <Mail className="h-4 w-4" />
                </div>
                <input
                  type="email"
                  required
                  className="w-full bg-slate-950/80 border border-slate-700/80 rounded-xl pl-9 pr-3 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">Password</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                  <Lock className="h-4 w-4" />
                </div>
                <input
                  type="password"
                  required
                  className="w-full bg-slate-950/80 border border-slate-700/80 rounded-xl pl-9 pr-3 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                />
              </div>
            </div>

            <button
              type="submit"
              className="w-full bg-blue-600 hover:bg-blue-500 active:bg-blue-700 text-white py-2.5 rounded-xl font-medium text-sm flex items-center justify-center gap-2 transition shadow-lg shadow-blue-600/30 disabled:opacity-60"
              disabled={loading}
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" /> Signing in...
                </>
              ) : (
                "Sign in"
              )}
            </button>
          </form>

          {/* Quick Demo Credentials */}
          <div className="mt-6 pt-6 border-t border-slate-800">
            <p className="text-xs font-medium text-slate-400 mb-2.5 text-center">Quick Demo Login</p>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => fillDemo("admin@example.com", "AdminPass123!")}
                disabled={loading}
                className="flex items-center justify-center gap-1.5 px-3 py-2 bg-slate-800/80 hover:bg-slate-700/80 text-cyan-400 text-xs font-medium rounded-xl border border-slate-700 transition"
              >
                <ShieldCheck className="h-3.5 w-3.5" /> Demo Admin
              </button>
              <button
                type="button"
                onClick={() => fillDemo("alice@example.com", "CustomerPass123!")}
                disabled={loading}
                className="flex items-center justify-center gap-1.5 px-3 py-2 bg-slate-800/80 hover:bg-slate-700/80 text-blue-400 text-xs font-medium rounded-xl border border-slate-700 transition"
              >
                <UserCheck className="h-3.5 w-3.5" /> Demo Driver
              </button>
            </div>
          </div>

          <p className="mt-6 text-xs text-slate-400 text-center">
            Don't have an account?{" "}
            <Link to="/register" className="text-blue-400 hover:text-blue-300 underline font-medium">
              Create one
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
