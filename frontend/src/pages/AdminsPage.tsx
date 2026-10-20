import { useEffect, useState } from "react";
import API from "@/services/api";
import type { Admin } from "@/types";
import { Plus, Trash2, Shield, Edit2, Key } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/hooks/useAuth";

export default function AdminsPage() {
  const [admins, setAdmins] = useState<Admin[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [openModal, setOpenModal] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    email: "",
    admin_name: "",
    phone_no: "",
    role: "ADMIN",
    experience: 3,
    password: "AdminPass123!",
  });

  const { user } = useAuth();
  const isAdmin = user?.role === "admin";

  const loadData = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await API.get<{ items: Admin[] }>("/admins");
      setAdmins(res.data.items);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load system administrators");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload = {
        email: formData.email,
        admin_name: formData.admin_name,
        full_name: formData.admin_name,
        phone_no: formData.phone_no,
        phone: formData.phone_no,
        role: formData.role,
        experience: Number(formData.experience),
        password: formData.password || undefined,
        privileges: ["manage_users", "manage_stations", "manage_tariffs", "manage_maintenance"],
      };

      if (editingId) {
        await API.put(`/admins/${editingId}`, payload);
      } else {
        await API.post("/admins", payload);
      }
      setOpenModal(false);
      setEditingId(null);
      loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to save administrator");
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Remove this administrator?")) return;
    try {
      await API.delete(`/admins/${id}`);
      loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to delete administrator");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900">System Administrators</h1>
          <p className="text-sm text-gray-500">Manage administrative privileges, maintenance oversight, and operator roles</p>
        </div>
        {isAdmin && (
          <button
            onClick={() => {
              setEditingId(null);
              setFormData({
                email: "",
                admin_name: "",
                phone_no: "",
                role: "ADMIN",
                experience: 3,
                password: "AdminPass123!",
              });
              setOpenModal(true);
            }}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition shadow-sm"
          >
            <Plus className="h-4 w-4" /> Add Administrator
          </button>
        )}
      </div>

      {error && <div className="p-4 rounded-lg bg-red-50 text-red-700 text-sm border border-red-200">{error}</div>}

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base font-medium flex items-center gap-2">
            <Shield className="h-5 w-5 text-indigo-600" /> Administrator Directory (Entity 2)
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="h-40 flex items-center justify-center text-gray-500">Loading administrators...</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-gray-500">
                    <th className="text-left pb-3 font-medium">Admin Name</th>
                    <th className="text-left pb-3 font-medium">Email</th>
                    <th className="text-left pb-3 font-medium">Phone</th>
                    <th className="text-left pb-3 font-medium">Role</th>
                    <th className="text-left pb-3 font-medium">Experience</th>
                    <th className="text-left pb-3 font-medium">Privileges</th>
                    {isAdmin && <th className="text-right pb-3 font-medium">Actions</th>}
                  </tr>
                </thead>
                <tbody>
                  {admins.map((a) => (
                    <tr key={a.id} className="border-b hover:bg-gray-50 transition">
                      <td className="py-3 font-medium text-gray-900">{a.admin_name || a.full_name || "Admin"}</td>
                      <td className="py-3 font-mono text-gray-600">{a.email}</td>
                      <td className="py-3">{a.phone_no || a.phone || "—"}</td>
                      <td className="py-3">
                        <span className="px-2 py-0.5 rounded text-xs font-semibold bg-indigo-100 text-indigo-800">
                          {a.role}
                        </span>
                      </td>
                      <td className="py-3 font-mono">{a.experience} yr(s)</td>
                      <td className="py-3 text-xs text-gray-500 max-w-xs truncate">
                        {Array.isArray(a.privileges) ? a.privileges.join(", ") : "All"}
                      </td>
                      {isAdmin && (
                        <td className="py-3 text-right space-x-2">
                          <button
                            onClick={() => {
                              setEditingId(a.id);
                              setFormData({
                                email: a.email,
                                admin_name: a.admin_name || a.full_name || "",
                                phone_no: a.phone_no || a.phone || "",
                                role: a.role || "ADMIN",
                                experience: a.experience || 0,
                                password: "",
                              });
                              setOpenModal(true);
                            }}
                            className="text-gray-500 hover:text-blue-600 p-1"
                          >
                            <Edit2 className="h-4 w-4" />
                          </button>
                          {a.email !== user?.email && (
                            <button
                              onClick={() => handleDelete(a.id)}
                              className="text-gray-500 hover:text-red-600 p-1"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          )}
                        </td>
                      )}
                    </tr>
                  ))}
                  {admins.length === 0 && (
                    <tr>
                      <td colSpan={7} className="text-center py-6 text-gray-500">No administrators registered.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Modal */}
      {openModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6 space-y-4">
            <h2 className="text-lg font-bold">{editingId ? "Edit Administrator" : "Create Administrator"}</h2>
            <form onSubmit={handleSave} className="space-y-3">
              <div>
                <label className="text-xs font-medium text-gray-700">Administrator Name</label>
                <input
                  type="text"
                  required
                  value={formData.admin_name}
                  onChange={(e) => setFormData({ ...formData, admin_name: e.target.value })}
                  className="w-full border rounded-lg p-2 text-sm mt-1"
                  placeholder="e.g. John Doe"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-gray-700">Email Address</label>
                <input
                  type="email"
                  required
                  disabled={!!editingId}
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full border rounded-lg p-2 text-sm mt-1 disabled:bg-gray-100"
                  placeholder="admin@example.com"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-gray-700">Phone Number</label>
                <input
                  type="text"
                  value={formData.phone_no}
                  onChange={(e) => setFormData({ ...formData, phone_no: e.target.value })}
                  className="w-full border rounded-lg p-2 text-sm mt-1"
                  placeholder="+1-555-0100"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium text-gray-700">Role</label>
                  <select
                    value={formData.role}
                    onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                    className="w-full border rounded-lg p-2 text-sm mt-1"
                  >
                    <option value="ADMIN">ADMIN</option>
                    <option value="SUPER_ADMIN">SUPER_ADMIN</option>
                    <option value="OPERATIONS">OPERATIONS</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-700">Experience (Years)</label>
                  <input
                    type="number"
                    min="0"
                    required
                    value={formData.experience}
                    onChange={(e) => setFormData({ ...formData, experience: Number(e.target.value) })}
                    className="w-full border rounded-lg p-2 text-sm mt-1"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-medium text-gray-700">Password {editingId && "(Leave empty to keep current)"}</label>
                <input
                  type="password"
                  required={!editingId}
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className="w-full border rounded-lg p-2 text-sm mt-1"
                  placeholder="••••••••"
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
                  Save
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
