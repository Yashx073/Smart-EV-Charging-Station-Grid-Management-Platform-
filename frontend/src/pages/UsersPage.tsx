import { useEffect, useState } from "react";
import API from "@/services/api";
import type { User, UserPhone } from "@/types";
import { User as UserIcon, Phone, Plus, Trash2, Edit2, Shield, MapPin, Calendar } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/hooks/useAuth";

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [phones, setPhones] = useState<UserPhone[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [openUserModal, setOpenUserModal] = useState(false);
  const [openPhoneModal, setOpenPhoneModal] = useState(false);

  const [userFormData, setUserFormData] = useState({
    email: "",
    password: "",
    full_name: "",
    first_name: "",
    last_name: "",
    phone: "",
    address: "",
    date_of_birth: "",
  });

  const [phoneFormData, setPhoneFormData] = useState({
    user_id: "",
    number: "",
    label: "Mobile",
    is_primary: false,
  });

  const { user: currentUser } = useAuth();
  const isAdmin = currentUser?.role === "admin";

  const loadData = async () => {
    setLoading(true);
    setError("");
    try {
      const [uRes, pRes] = await Promise.all([
        API.get<{ items: User[] }>("/users"),
        API.get<{ items: UserPhone[] }>("/user-phones"),
      ]);
      setUsers(uRes.data.items);
      setPhones(pRes.data.items);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load users");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleStatus = async (id: string, status: string) => {
    try {
      await API.put(`/users/${id}`, { status });
      setUsers(users.map((u) => (u.id === id ? { ...u, status } : u)));
    } catch (err: any) {
      setError(err.response?.data?.detail || "Update status failed");
    }
  };

  const handleSaveUser = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (selectedUser) {
        await API.put(`/users/${selectedUser.id}`, {
          full_name: userFormData.full_name,
          first_name: userFormData.first_name,
          last_name: userFormData.last_name,
          phone: userFormData.phone,
          address: userFormData.address,
          date_of_birth: userFormData.date_of_birth,
        });
      } else {
        await API.post("/users", userFormData);
      }
      setOpenUserModal(false);
      setSelectedUser(null);
      loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Save user failed");
    }
  };

  const handleAddPhone = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await API.post("/user-phones", {
        user_id: phoneFormData.user_id,
        number: phoneFormData.number,
        phone_no: phoneFormData.number,
        label: phoneFormData.label,
        phone_type: phoneFormData.label,
        is_primary: phoneFormData.is_primary,
      });
      setOpenPhoneModal(false);
      loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to add phone number");
    }
  };

  const handleDeletePhone = async (id: string) => {
    if (!confirm("Delete this phone record?")) return;
    try {
      await API.delete(`/user-phones/${id}`);
      loadData();
    } catch (err: any) {
      setError("Failed to delete phone number");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900">EV Customers & Users</h1>
          <p className="text-sm text-gray-500">Manage EV driver profiles, personal information, and registered phone numbers</p>
        </div>
        {isAdmin && (
          <button
            onClick={() => {
              setSelectedUser(null);
              setUserFormData({
                email: "",
                password: "CustomerPass123!",
                full_name: "",
                first_name: "",
                last_name: "",
                phone: "",
                address: "",
                date_of_birth: "1990-01-01",
              });
              setOpenUserModal(true);
            }}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition shadow-sm"
          >
            <Plus className="h-4 w-4" /> Add Customer
          </button>
        )}
      </div>

      {error && <div className="p-4 rounded-lg bg-red-50 text-red-700 text-sm border border-red-200">{error}</div>}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader className="pb-2">
            <CardTitle className="text-base font-medium flex items-center gap-2">
              <UserIcon className="h-5 w-5 text-blue-600" /> Customer Registry (Entity 1: EV_USER)
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="h-40 flex items-center justify-center text-gray-500">Loading users...</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b text-gray-500">
                      <th className="text-left pb-3 font-medium">Customer</th>
                      <th className="text-left pb-3 font-medium">Email</th>
                      <th className="text-left pb-3 font-medium">Phone</th>
                      <th className="text-left pb-3 font-medium">Role</th>
                      <th className="text-left pb-3 font-medium">Status</th>
                      <th className="text-right pb-3 font-medium">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.map((u) => {
                      const userPhoneCount = phones.filter((p) => p.user_id === u.id).length;
                      return (
                        <tr
                          key={u.id}
                          className={`border-b hover:bg-blue-50/30 cursor-pointer transition ${
                            selectedUser?.id === u.id ? "bg-blue-50" : ""
                          }`}
                          onClick={() => setSelectedUser(u)}
                        >
                          <td className="py-3">
                            <div className="font-medium text-gray-900">{u.full_name}</div>
                            {u.address && (
                              <div className="text-xs text-gray-400 flex items-center gap-1">
                                <MapPin className="h-3 w-3" /> {u.address}
                              </div>
                            )}
                          </td>
                          <td className="py-3 font-mono text-gray-600 text-xs">{u.email}</td>
                          <td className="py-3 text-xs">
                            <div>{u.phone || "—"}</div>
                            {userPhoneCount > 0 && (
                              <span className="text-[10px] text-blue-600 font-semibold">
                                +{userPhoneCount} extra phone(s)
                              </span>
                            )}
                          </td>
                          <td className="py-3">
                            <span className={`px-2 py-0.5 rounded text-xs font-semibold ${u.role === "admin" ? "bg-indigo-100 text-indigo-800" : "bg-gray-100 text-gray-800"}`}>
                              {u.role}
                            </span>
                          </td>
                          <td className="py-3">
                            <select
                              value={u.status}
                              disabled={!isAdmin}
                              onChange={(e) => handleStatus(u.id, e.target.value)}
                              className="text-xs border rounded-md px-2 py-1 font-semibold"
                            >
                              <option value="active">active</option>
                              <option value="suspended">suspended</option>
                              <option value="deleted">deleted</option>
                            </select>
                          </td>
                          <td className="py-3 text-right">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setSelectedUser(u);
                                setUserFormData({
                                  email: u.email,
                                  password: "",
                                  full_name: u.full_name,
                                  first_name: u.first_name || "",
                                  last_name: u.last_name || "",
                                  phone: u.phone || "",
                                  address: u.address || "",
                                  date_of_birth: u.date_of_birth || "",
                                });
                                setOpenUserModal(true);
                              }}
                              className="text-gray-400 hover:text-blue-600 p-1"
                              title="Edit user"
                            >
                              <Edit2 className="h-4 w-4" />
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>

        {/* User Details & Registered Phones Panel (Entity 7: USER_PHONE) */}
        <Card>
          <CardHeader className="pb-2 flex flex-row items-center justify-between">
            <CardTitle className="text-base font-medium flex items-center gap-2">
              <Phone className="h-4 w-4 text-emerald-600" /> User Phones (Entity 7)
            </CardTitle>
            {selectedUser && (
              <button
                onClick={() => {
                  setPhoneFormData({
                    user_id: selectedUser.id,
                    number: "",
                    label: "Mobile",
                    is_primary: false,
                  });
                  setOpenPhoneModal(true);
                }}
                className="text-xs bg-emerald-600 text-white px-2 py-1 rounded hover:bg-emerald-700 font-medium"
              >
                + Add Phone
              </button>
            )}
          </CardHeader>
          <CardContent>
            {selectedUser ? (
              <div className="space-y-4">
                <div className="p-3 rounded-lg bg-gray-50 border border-gray-100 text-xs space-y-1">
                  <div className="font-bold text-gray-900">{selectedUser.full_name}</div>
                  <div className="text-gray-500">{selectedUser.email}</div>
                  {selectedUser.date_of_birth && (
                    <div className="text-gray-400 flex items-center gap-1">
                      <Calendar className="h-3 w-3" /> DOB: {selectedUser.date_of_birth}
                    </div>
                  )}
                  {selectedUser.address && (
                    <div className="text-gray-400 flex items-center gap-1">
                      <MapPin className="h-3 w-3" /> {selectedUser.address}
                    </div>
                  )}
                </div>

                <div className="space-y-2">
                  <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
                    Associated Phone Numbers
                  </h4>
                  {phones
                    .filter((p) => p.user_id === selectedUser.id)
                    .map((p) => (
                      <div
                        key={p.id}
                        className="flex items-center justify-between p-2 rounded-lg border border-gray-100 bg-white text-xs shadow-sm"
                      >
                        <div>
                          <div className="font-mono font-bold text-gray-800">{p.number || p.phone_no}</div>
                          <div className="text-[10px] text-gray-400">
                            {p.label || p.phone_type || "Phone"} {p.is_primary && "• (Primary)"}
                          </div>
                        </div>
                        <button
                          onClick={() => handleDeletePhone(p.id)}
                          className="text-gray-400 hover:text-red-600 p-1"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    ))}
                  {phones.filter((p) => p.user_id === selectedUser.id).length === 0 && (
                    <p className="text-xs text-gray-400 italic py-2">No additional phone records for this user.</p>
                  )}
                </div>
              </div>
            ) : (
              <div className="text-center py-12 text-xs text-gray-400">
                Click a user in the table to view details & phone numbers.
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Edit User Modal */}
      {openUserModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6 space-y-4">
            <h2 className="text-lg font-bold">{selectedUser ? "Edit User Profile" : "Register EV User"}</h2>
            <form onSubmit={handleSaveUser} className="space-y-3">
              <div>
                <label className="text-xs font-medium text-gray-700">Full Name</label>
                <input
                  type="text"
                  required
                  value={userFormData.full_name}
                  onChange={(e) => setUserFormData({ ...userFormData, full_name: e.target.value })}
                  className="w-full border rounded-lg p-2 text-sm mt-1"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium text-gray-700">First Name</label>
                  <input
                    type="text"
                    value={userFormData.first_name}
                    onChange={(e) => setUserFormData({ ...userFormData, first_name: e.target.value })}
                    className="w-full border rounded-lg p-2 text-sm mt-1"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-700">Last Name</label>
                  <input
                    type="text"
                    value={userFormData.last_name}
                    onChange={(e) => setUserFormData({ ...userFormData, last_name: e.target.value })}
                    className="w-full border rounded-lg p-2 text-sm mt-1"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-medium text-gray-700">Email Address</label>
                <input
                  type="email"
                  required
                  disabled={!!selectedUser}
                  value={userFormData.email}
                  onChange={(e) => setUserFormData({ ...userFormData, email: e.target.value })}
                  className="w-full border rounded-lg p-2 text-sm mt-1 disabled:bg-gray-100"
                />
              </div>

              {!selectedUser && (
                <div>
                  <label className="text-xs font-medium text-gray-700">Password</label>
                  <input
                    type="password"
                    required
                    value={userFormData.password}
                    onChange={(e) => setUserFormData({ ...userFormData, password: e.target.value })}
                    className="w-full border rounded-lg p-2 text-sm mt-1"
                  />
                </div>
              )}

              <div>
                <label className="text-xs font-medium text-gray-700">Primary Phone</label>
                <input
                  type="text"
                  value={userFormData.phone}
                  onChange={(e) => setUserFormData({ ...userFormData, phone: e.target.value })}
                  className="w-full border rounded-lg p-2 text-sm mt-1"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-gray-700">Address</label>
                <input
                  type="text"
                  value={userFormData.address}
                  onChange={(e) => setUserFormData({ ...userFormData, address: e.target.value })}
                  className="w-full border rounded-lg p-2 text-sm mt-1"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-gray-700">Date of Birth</label>
                <input
                  type="date"
                  value={userFormData.date_of_birth}
                  onChange={(e) => setUserFormData({ ...userFormData, date_of_birth: e.target.value })}
                  className="w-full border rounded-lg p-2 text-sm mt-1"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setOpenUserModal(false)}
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

      {/* Add Phone Modal */}
      {openPhoneModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-sm p-6 space-y-4">
            <h2 className="text-lg font-bold">Add User Phone Number</h2>
            <form onSubmit={handleAddPhone} className="space-y-3">
              <div>
                <label className="text-xs font-medium text-gray-700">Phone Number</label>
                <input
                  type="text"
                  required
                  value={phoneFormData.number}
                  onChange={(e) => setPhoneFormData({ ...phoneFormData, number: e.target.value })}
                  className="w-full border rounded-lg p-2 text-sm mt-1 font-mono"
                  placeholder="+1-555-0199"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-gray-700">Label / Type</label>
                <select
                  value={phoneFormData.label}
                  onChange={(e) => setPhoneFormData({ ...phoneFormData, label: e.target.value })}
                  className="w-full border rounded-lg p-2 text-sm mt-1"
                >
                  <option value="Mobile">Mobile</option>
                  <option value="Work">Work</option>
                  <option value="Home">Home</option>
                  <option value="Emergency">Emergency</option>
                </select>
              </div>

              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="primary_chk"
                  checked={phoneFormData.is_primary}
                  onChange={(e) => setPhoneFormData({ ...phoneFormData, is_primary: e.target.checked })}
                  className="rounded border-gray-300 text-emerald-600"
                />
                <label htmlFor="primary_chk" className="text-xs text-gray-700">Set as Primary Number</label>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setOpenPhoneModal(false)}
                  className="px-4 py-2 border rounded-lg text-sm text-gray-600 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-700"
                >
                  Add Phone
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
