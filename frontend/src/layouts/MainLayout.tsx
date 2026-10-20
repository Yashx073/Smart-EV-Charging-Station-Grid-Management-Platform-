import { useState } from "react";
import { Link, useLocation, Outlet } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";
import {
  LayoutDashboard,
  Wallet,
  Calendar,
  Settings,
  Shield,
  User,
  LogOut,
  Car,
  Building,
  PlugZap,
  Zap,
  Network,
  Bell,
  BatteryCharging,
  Clock,
  Wrench,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";

const navItems = [
  { key: "dashboard", label: "Dashboard", href: "/customer/dashboard", icon: LayoutDashboard },
  { key: "stations", label: "Stations", href: "/customer/stations", icon: Building },
  { key: "ports", label: "Charging Ports", href: "/customer/ports", icon: PlugZap },
  { key: "evs", label: "My EVs", href: "/customer/evs", icon: Car },
  { key: "battery", label: "Battery Telemetry", href: "/customer/battery-status", icon: BatteryCharging },
  { key: "bookings", label: "Bookings", href: "/customer/bookings", icon: Calendar },
  { key: "sessions", label: "Sessions", href: "/customer/sessions", icon: Wallet },
  { key: "payments", label: "Payments", href: "/customer/payments", icon: Wallet },
  { key: "notifications", label: "Notifications", href: "/customer/notifications", icon: Bell },
];

const adminItems = [
  { key: "dashboard", label: "Dashboard", href: "/admin/dashboard", icon: LayoutDashboard },
  { key: "users", label: "Users & Phones", href: "/admin/users", icon: User },
  { key: "admins", label: "Administrators", href: "/admin/admins", icon: Shield },
  { key: "stations", label: "Stations", href: "/admin/stations", icon: Building },
  { key: "ports", label: "Ports (AC / DC)", href: "/admin/ports", icon: PlugZap },
  { key: "sources", label: "Energy Sources", href: "/admin/sources", icon: Zap },
  { key: "grids", label: "Power Grids", href: "/admin/grids", icon: Network },
  { key: "tariffs", label: "Tariffs", href: "/admin/tariffs", icon: Wallet },
  { key: "schedules", label: "Schedules", href: "/admin/schedules", icon: Clock },
  { key: "maintenance", label: "Maintenance", href: "/admin/maintenance", icon: Wrench },
  { key: "bookings", label: "Bookings", href: "/admin/bookings", icon: Calendar },
  { key: "sessions", label: "Sessions", href: "/admin/sessions", icon: Wallet },
  { key: "payments", label: "Payments", href: "/admin/payments", icon: Wallet },
  { key: "evs", label: "All EVs", href: "/admin/evs", icon: Car },
  { key: "battery", label: "Battery Status", href: "/admin/battery-status", icon: BatteryCharging },
  { key: "notifications", label: "Notifications", href: "/admin/notifications", icon: Bell },
];

export default function MainLayout() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [open, setOpen] = useState(true);
  const items = user?.role === "admin" ? adminItems : navItems;

  return (
    <div className="flex h-screen bg-gray-50">
      <aside className="hidden w-64 bg-white border-r border-gray-200 flex-col md:flex">
        <div className="p-6 flex items-center gap-2 border-b border-gray-200">
          <PlugZap className="h-6 w-6 text-blue-600" />
          <span className="font-bold text-lg tracking-tight">Smart EV 2.0</span>
        </div>
        <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
          {items.map((item) => {
            const active = location.pathname.startsWith(item.href);
            return (
              <Link
                key={item.key}
                to={item.href}
                className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition ${
                  active ? "bg-blue-50 text-blue-700 font-semibold" : "text-gray-600 hover:bg-gray-100"
                }`}
              >
                <item.icon className={`h-4 w-4 ${active ? "text-blue-700" : "text-gray-400"}`} />
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="p-4 border-t border-gray-200">
          <button
            onClick={logout}
            className="w-full flex items-center gap-3 px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg transition"
          >
            <LogOut className="h-4 w-4" /> Sign out
          </button>
        </div>
      </aside>

      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="sticky top-0 z-10 bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between shadow-sm">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setOpen(!open)}
              className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg md:hidden"
            >
              <span className="sr-only">Toggle menu</span>
              {open ? <ChevronLeft className="h-5 w-5" /> : <ChevronRight className="h-5 w-5" />}
            </button>
            <span className="font-semibold text-gray-900 hidden md:block">
              {user?.role === "admin" ? "SuperAdmin Operations Console" : "Smart EV Customer Portal"}
            </span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-gray-500 hidden sm:block">{user?.email}</span>
            <span
              className={`text-xs px-2.5 py-1 rounded-full font-semibold uppercase ${
                user?.role === "admin" ? "bg-indigo-100 text-indigo-700" : "bg-emerald-100 text-emerald-700"
              }`}
            >
              {user?.role}
            </span>
          </div>
        </header>
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
