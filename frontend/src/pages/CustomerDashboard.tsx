import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import API from "@/services/api";
import type { DashboardStats } from "@/types";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line } from "recharts";
import { DollarSign, PlugZap, Calendar, Users, Building, AlertTriangle } from "lucide-react";

export default function CustomerDashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [trends, setTrends] = useState<any>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    API.get<DashboardStats>("/dashboard/stats")
      .then((r) => setStats(r.data))
      .catch(() => setError("Failed to load stats"));
    API.get("/dashboard/trends?days=7")
      .then((r) => setTrends(r.data))
      .catch(() => {});
  }, []);

  const stat = [
    { label: "Total Users", value: stats?.total_users ?? 0, icon: Users, color: "text-blue-600" },
    { label: "Stations", value: stats?.total_stations ?? 0, icon: Building, color: "text-indigo-600" },
    { label: "Ports", value: stats?.total_ports ?? 0, icon: PlugZap, color: "text-green-600" },
    { label: "Bookings", value: stats?.total_bookings ?? 0, icon: Calendar, color: "text-purple-600" },
    { label: "Sessions", value: stats?.total_sessions ?? 0, icon: DollarSign, color: "text-orange-600" },
    { label: "Revenue (₹)", value: stats?.total_revenue ?? 0, icon: DollarSign, color: "text-emerald-600" },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        {error && <AlertTriangle className="h-5 w-5 text-red-500" />}
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {stat.map((s) => (
          <Card key={s.label}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-gray-500">{s.label}</CardTitle>
              <s.icon className={`h-5 w-5 ${s.color}`} />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{typeof s.value === "number" ? s.value.toLocaleString() : s.value}</div>
            </CardContent>
          </Card>
        ))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="col-span-2 lg:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Bookings trend</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={trends?.booking_trend || []}>
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="#4f46e5" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Revenue trend</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={trends?.revenue_trend || []}>
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Line dataKey="amount" stroke="#4f46e5" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
