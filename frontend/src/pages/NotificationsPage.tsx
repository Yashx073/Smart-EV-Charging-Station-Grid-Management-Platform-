import { useEffect, useState } from "react";
import API from "@/services/api";
import type { Notification, User } from "@/types";
import { Bell, Check, Trash2, Plus, Filter } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/hooks/useAuth";

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filterType, setFilterType] = useState<string>("ALL");
  const [openModal, setOpenModal] = useState(false);

  const [formData, setFormData] = useState({
    user_id: "",
    message: "",
    notification_type: "INFO",
  });

  const { user } = useAuth();
  const isAdmin = user?.role === "admin";

  const loadData = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await API.get<{ items: Notification[] }>("/notifications");
      setNotifications(res.data.items);
      if (isAdmin) {
        const uRes = await API.get<{ items: User[] }>("/users");
        setUsers(uRes.data.items);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load notifications");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleMarkRead = async (id: string) => {
    try {
      await API.post(`/notifications/${id}/read`);
      setNotifications(
        notifications.map((n) => (n.id === id ? { ...n, is_read: true, read_status: "READ" } : n))
      );
    } catch (err: any) {
      setError("Failed to mark notification as read");
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await API.delete(`/notifications/${id}`);
      setNotifications(notifications.filter((n) => n.id !== id));
    } catch (err: any) {
      setError("Failed to delete notification");
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await API.post("/notifications", {
        user_id: formData.user_id || user?.id,
        message: formData.message,
        notification_type: formData.notification_type,
      });
      setOpenModal(false);
      setFormData({ user_id: "", message: "", notification_type: "INFO" });
      loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to dispatch notification");
    }
  };

  const filtered = filterType === "ALL"
    ? notifications
    : filterType === "UNREAD"
    ? notifications.filter((n) => !n.is_read)
    : notifications.filter((n) => n.notification_type === filterType);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900">Notifications</h1>
          <p className="text-sm text-gray-500">System alerts, booking updates, charging milestones, and battery warnings</p>
        </div>
        {isAdmin && (
          <button
            onClick={() => {
              setFormData({ user_id: users[0]?.id || "", message: "", notification_type: "INFO" });
              setOpenModal(true);
            }}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition shadow-sm"
          >
            <Plus className="h-4 w-4" /> Dispatch Notification
          </button>
        )}
      </div>

      {error && <div className="p-4 rounded-lg bg-red-50 text-red-700 text-sm border border-red-200">{error}</div>}

      <div className="flex flex-wrap items-center gap-2 pb-2">
        <Filter className="h-4 w-4 text-gray-400 mr-1" />
        {["ALL", "UNREAD", "INFO", "WELCOME", "BOOKING_CONFIRMED", "SESSION_COMPLETE", "BATTERY_WARNING", "ALERT"].map(
          (t) => (
            <button
              key={t}
              onClick={() => setFilterType(t)}
              className={`px-3 py-1 rounded-full text-xs font-semibold transition ${
                filterType === t ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              {t}
            </button>
          )
        )}
      </div>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base font-medium flex items-center gap-2">
            <Bell className="h-5 w-5 text-blue-600" /> Notifications Feed (Entity 17)
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="h-40 flex items-center justify-center text-gray-500">Loading notifications...</div>
          ) : (
            <div className="divide-y divide-gray-100">
              {filtered.map((n) => (
                <div
                  key={n.id}
                  className={`py-4 px-2 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 transition rounded-lg ${
                    n.is_read ? "opacity-75" : "bg-blue-50/40"
                  }`}
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span
                        className={`px-2 py-0.5 rounded text-xs font-semibold ${
                          n.notification_type?.includes("WARNING") || n.notification_type === "ALERT"
                            ? "bg-red-100 text-red-800"
                            : n.notification_type === "BOOKING_CONFIRMED"
                            ? "bg-green-100 text-green-800"
                            : "bg-blue-100 text-blue-800"
                        }`}
                      >
                        {n.notification_type || "INFO"}
                      </span>
                      <span className="text-xs text-gray-400">
                        {n.created_at ? new Date(n.created_at).toLocaleString() : ""}
                      </span>
                      {!n.is_read && (
                        <span className="inline-block w-2 h-2 rounded-full bg-blue-600" title="Unread" />
                      )}
                    </div>
                    <p className={`text-sm ${n.is_read ? "text-gray-600" : "font-medium text-gray-900"}`}>
                      {n.message}
                    </p>
                  </div>

                  <div className="flex items-center gap-2 self-end sm:self-center">
                    {!n.is_read && (
                      <button
                        onClick={() => handleMarkRead(n.id)}
                        className="flex items-center gap-1 px-2.5 py-1 text-xs border border-blue-300 text-blue-700 bg-white hover:bg-blue-50 rounded-md font-medium transition"
                      >
                        <Check className="h-3.5 w-3.5" /> Mark read
                      </button>
                    )}
                    <button
                      onClick={() => handleDelete(n.id)}
                      className="text-gray-400 hover:text-red-600 p-1 rounded transition"
                      title="Delete"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              ))}
              {filtered.length === 0 && (
                <div className="text-center py-8 text-gray-500">No notifications in this view.</div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Modal */}
      {openModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6 space-y-4">
            <h2 className="text-lg font-bold">Dispatch New Notification</h2>
            <form onSubmit={handleCreate} className="space-y-3">
              <div>
                <label className="text-xs font-medium text-gray-700">Target User</label>
                <select
                  value={formData.user_id}
                  onChange={(e) => setFormData({ ...formData, user_id: e.target.value })}
                  className="w-full border rounded-lg p-2 text-sm mt-1"
                  required
                >
                  <option value="">Select recipient...</option>
                  {users.map((u) => (
                    <option key={u.id} value={u.id}>
                      {u.full_name} ({u.email})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-xs font-medium text-gray-700">Notification Type</label>
                <select
                  value={formData.notification_type}
                  onChange={(e) => setFormData({ ...formData, notification_type: e.target.value })}
                  className="w-full border rounded-lg p-2 text-sm mt-1"
                >
                  <option value="INFO">INFO</option>
                  <option value="ALERT">ALERT</option>
                  <option value="BOOKING_CONFIRMED">BOOKING_CONFIRMED</option>
                  <option value="SESSION_COMPLETE">SESSION_COMPLETE</option>
                  <option value="BATTERY_WARNING">BATTERY_WARNING</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-medium text-gray-700">Message Content</label>
                <textarea
                  required
                  rows={3}
                  value={formData.message}
                  onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                  className="w-full border rounded-lg p-2 text-sm mt-1"
                  placeholder="Enter notification message..."
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setOpenModal(false)}
                  className="px-4 py-2 border rounded-lg text-sm text-gray-600 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700"
                >
                  Send
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
