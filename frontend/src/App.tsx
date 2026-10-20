import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";
import MainLayout from "@/layouts/MainLayout";
import LoginPage from "@/pages/LoginPage";
import RegisterPage from "@/pages/RegisterPage";
import CustomerDashboard from "@/pages/CustomerDashboard";
import AdminDashboard from "@/pages/AdminDashboard";
import StationsPage from "@/pages/StationsPage";
import PortsPage from "@/pages/PortsPage";
import EVsPage from "@/pages/EVsPage";
import BookingsPage from "@/pages/BookingsPage";
import SessionsPage from "@/pages/SessionsPage";
import PaymentsPage from "@/pages/PaymentsPage";
import TariffsPage from "@/pages/TariffsPage";
import MaintenancePage from "@/pages/MaintenancePage";
import UsersPage from "@/pages/UsersPage";
import AdminsPage from "@/pages/AdminsPage";
import SourcesPage from "@/pages/SourcesPage";
import GridsPage from "@/pages/GridsPage";
import SchedulesPage from "@/pages/SchedulesPage";
import NotificationsPage from "@/pages/NotificationsPage";
import BatteryStatusPage from "@/pages/BatteryStatusPage";

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function AdminOnly({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (!user || user.role !== "admin") return <Navigate to="/customer/dashboard" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        
        {/* Customer Portal */}
        <Route
          path="/customer/*"
          element={
            <ProtectedRoute>
              <MainLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<CustomerDashboard />} />
          <Route path="dashboard" element={<CustomerDashboard />} />
          <Route path="stations" element={<StationsPage />} />
          <Route path="ports" element={<PortsPage />} />
          <Route path="evs" element={<EVsPage />} />
          <Route path="battery-status" element={<BatteryStatusPage />} />
          <Route path="bookings" element={<BookingsPage />} />
          <Route path="sessions" element={<SessionsPage />} />
          <Route path="payments" element={<PaymentsPage />} />
          <Route path="notifications" element={<NotificationsPage />} />
        </Route>

        {/* Administrator Console */}
        <Route
          path="/admin/*"
          element={
            <ProtectedRoute>
              <AdminOnly>
                <MainLayout />
              </AdminOnly>
            </ProtectedRoute>
          }
        >
          <Route index element={<AdminDashboard />} />
          <Route path="dashboard" element={<AdminDashboard />} />
          <Route path="users" element={<UsersPage />} />
          <Route path="admins" element={<AdminsPage />} />
          <Route path="stations" element={<StationsPage />} />
          <Route path="ports" element={<PortsPage />} />
          <Route path="sources" element={<SourcesPage />} />
          <Route path="grids" element={<GridsPage />} />
          <Route path="tariffs" element={<TariffsPage />} />
          <Route path="schedules" element={<SchedulesPage />} />
          <Route path="maintenance" element={<MaintenancePage />} />
          <Route path="bookings" element={<BookingsPage />} />
          <Route path="sessions" element={<SessionsPage />} />
          <Route path="payments" element={<PaymentsPage />} />
          <Route path="evs" element={<EVsPage />} />
          <Route path="battery-status" element={<BatteryStatusPage />} />
          <Route path="notifications" element={<NotificationsPage />} />
        </Route>

        <Route path="/" element={<Navigate to="/customer/dashboard" replace />} />
        <Route path="*" element={<Navigate to="/customer/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
