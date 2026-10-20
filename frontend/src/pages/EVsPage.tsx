import { useEffect, useState } from "react";
import API from "@/services/api";
import type { EV, User } from "@/types";
import { Plus, Trash2, Car, BatteryCharging, AlertCircle, CheckCircle2, Loader2, X } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/hooks/useAuth";

const CONNECTOR_OPTIONS = ["CCS2", "Type2", "CHAdeMO", "GB/T"];

export default function EVsPage() {
  const [items, setItems] = useState<EV[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [open, setOpen] = useState(false);
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";

  const [form, setForm] = useState({
    model: "",
    manufacturer: "",
    registration_number: "",
    battery_capacity_kwh: 50,
    connector_type: "CCS2",
    owner_id: "",
  });

  const loadData = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await API.get<{ items: EV[] }>("/evs");
      setItems(res.data.items || []);
      if (isAdmin) {
        try {
          const uRes = await API.get<{ items: User[] }>("/users");
          setUsers(uRes.data.items || []);
        } catch {
          // ignore user list fail for non-admins
        }
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load electric vehicles");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleOpenModal = () => {
    setForm({
      model: "",
      manufacturer: "",
      registration_number: "",
      battery_capacity_kwh: 50,
      connector_type: "CCS2",
      owner_id: user?.id || "",
    });
    setError("");
    setSuccess("");
    setOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess("");

    if (!form.model.trim()) {
      setError("Please specify the vehicle model.");
      return;
    }
    if (!form.registration_number.trim()) {
      setError("Please specify the registration number (license plate).");
      return;
    }
    if (!form.battery_capacity_kwh || form.battery_capacity_kwh <= 0) {
      setError("Battery capacity must be greater than 0 kWh.");
      return;
    }

    setSubmitting(true);
    try {
      const payload: any = {
        model: form.model.trim(),
        brand: form.manufacturer.trim() || form.model.split(" ")[0],
        manufacturer: form.manufacturer.trim() || form.model.split(" ")[0],
        registration_number: form.registration_number.trim().toUpperCase(),
        battery_capacity: Number(form.battery_capacity_kwh),
        battery_capacity_kwh: Number(form.battery_capacity_kwh),
        battery_capacity_kw: Number(form.battery_capacity_kwh),
        connector_type: form.connector_type,
      };
      if (isAdmin && form.owner_id) {
        payload.owner_id = form.owner_id;
        payload.user_id = form.owner_id;
      }

      await API.post("/evs", payload);
      setSuccess("Electric vehicle successfully registered with initial battery telemetry!");
      setOpen(false);
      loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to add EV. Please check the details.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this EV?")) return;
    setError("");
    setSuccess("");
    try {
      await API.delete(`/evs/${id}`);
      setSuccess("EV successfully removed");
      loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Delete failed");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900">Electric Vehicles</h1>
          <p className="text-sm text-gray-500">
            {isAdmin ? "Manage all registered EV fleet in the system" : "Manage your registered electric vehicles and telemetry"}
          </p>
        </div>
        <button
          onClick={handleOpenModal}
          className="bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white px-4 py-2 rounded-xl text-sm font-medium flex items-center gap-2 shadow-sm transition"
        >
          <Plus className="h-4 w-4" /> Add EV
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-50 text-red-700 text-sm border border-red-200 flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0 text-red-500" />
          <span>{error}</span>
        </div>
      )}

      {success && (
        <div className="p-4 rounded-xl bg-green-50 text-green-700 text-sm border border-green-200 flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4 shrink-0 text-green-500" />
          <span>{success}</span>
        </div>
      )}

      <Card className="shadow-sm">
        <CardHeader className="pb-3 border-b border-gray-100 flex flex-row items-center justify-between">
          <CardTitle className="text-base font-semibold text-gray-900 flex items-center gap-2">
            <Car className="h-5 w-5 text-blue-600" /> {isAdmin ? "Registered Fleet" : "My Vehicles"}
          </CardTitle>
          <span className="text-xs font-medium text-gray-400">{items.length} vehicles registered</span>
        </CardHeader>
        <CardContent className="pt-4">
          {loading ? (
            <div className="h-40 flex items-center justify-center text-gray-400">Loading vehicles...</div>
          ) : items.length === 0 ? (
            <div className="text-center py-12">
              <Car className="h-12 w-12 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500 font-medium">No electric vehicles found.</p>
              <p className="text-xs text-gray-400 mt-1 mb-4">Add your EV to schedule charging sessions and track battery health.</p>
              <button
                onClick={handleOpenModal}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-xl text-sm font-medium inline-flex items-center gap-2"
              >
                <Plus className="h-4 w-4" /> Add your first EV
              </button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead>
                  <tr className="border-b border-gray-100 text-gray-400 text-xs font-semibold uppercase tracking-wider">
                    <th className="pb-3">Model & Brand</th>
                    <th className="pb-3">License Plate</th>
                    <th className="pb-3">Battery Capacity</th>
                    <th className="pb-3">Connector</th>
                    <th className="pb-3">Status</th>
                    {isAdmin && <th className="pb-3 text-right">Actions</th>}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {items.map((e) => (
                    <tr key={e.id} className="hover:bg-gray-50/70 transition">
                      <td className="py-3.5 font-medium text-gray-900">
                        {e.manufacturer || e.brand ? `${e.manufacturer || e.brand} ` : ""}
                        {e.model}
                      </td>
                      <td className="py-3.5 font-mono text-xs font-semibold text-blue-700">
                        <span className="bg-blue-50 px-2 py-1 rounded-md border border-blue-100">
                          {e.registration_number || (e as any).vehicle_number}
                        </span>
                      </td>
                      <td className="py-3.5 text-gray-600">
                        <span className="flex items-center gap-1 font-medium">
                          <BatteryCharging className="h-4 w-4 text-emerald-600" />
                          {e.battery_capacity_kwh ?? e.battery_capacity ?? "-"} kWh
                        </span>
                      </td>
                      <td className="py-3.5 text-gray-600">
                        <span className="px-2 py-0.5 rounded text-xs bg-slate-100 text-slate-700 font-medium border border-slate-200">
                          {e.connector_type}
                        </span>
                      </td>
                      <td className="py-3.5">
                        <span
                          className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                            e.is_active !== false ? "bg-emerald-50 text-emerald-700 border border-emerald-200" : "bg-gray-100 text-gray-600"
                          }`}
                        >
                          {e.is_active !== false ? "Active" : "Inactive"}
                        </span>
                      </td>
                      {isAdmin && (
                        <td className="py-3.5 text-right">
                          <button
                            onClick={() => handleDelete(e.id)}
                            className="text-red-600 hover:text-red-700 p-1.5 rounded-lg hover:bg-red-50 transition"
                            title="Delete vehicle"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Add EV Modal Dialog */}
      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm transition-opacity" onClick={() => setOpen(false)} />
          <div className="relative z-10 bg-white rounded-2xl shadow-2xl w-full max-w-md border border-gray-100 p-6 space-y-5">
            <div className="flex items-center justify-between border-b pb-3 border-gray-100">
              <div className="flex items-center gap-2">
                <div className="p-2 bg-blue-50 text-blue-600 rounded-xl">
                  <Car className="h-5 w-5" />
                </div>
                <h2 className="text-lg font-bold text-gray-900">Register Electric Vehicle</h2>
              </div>
              <button onClick={() => setOpen(false)} className="text-gray-400 hover:text-gray-600 p-1 rounded-lg">
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Vehicle Model *</label>
                <input
                  required
                  className="w-full border border-gray-300 rounded-xl px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                  value={form.model}
                  onChange={(e) => setForm({ ...form, model: e.target.value })}
                  placeholder="e.g. Nexon EV, Model 3, Kona Electric"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Manufacturer / Make</label>
                <input
                  className="w-full border border-gray-300 rounded-xl px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                  value={form.manufacturer}
                  onChange={(e) => setForm({ ...form, manufacturer: e.target.value })}
                  placeholder="e.g. Tata, Tesla, Hyundai"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Registration Number (License Plate) *</label>
                <input
                  required
                  className="w-full border border-gray-300 rounded-xl px-3 py-2 text-sm uppercase font-mono tracking-wider focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                  value={form.registration_number}
                  onChange={(e) => setForm({ ...form, registration_number: e.target.value })}
                  placeholder="e.g. MH-02-AB-1234"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-1">Battery (kWh) *</label>
                  <input
                    type="number"
                    step="0.1"
                    min="1"
                    max="300"
                    required
                    className="w-full border border-gray-300 rounded-xl px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                    value={form.battery_capacity_kwh}
                    onChange={(e) => setForm({ ...form, battery_capacity_kwh: Number(e.target.value) })}
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-1">Connector *</label>
                  <select
                    className="w-full border border-gray-300 rounded-xl px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none bg-white"
                    value={form.connector_type}
                    onChange={(e) => setForm({ ...form, connector_type: e.target.value })}
                  >
                    {CONNECTOR_OPTIONS.map((c) => (
                      <option key={c} value={c}>
                        {c}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {isAdmin && users.length > 0 && (
                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-1">Assign to Owner</label>
                  <select
                    className="w-full border border-gray-300 rounded-xl px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none bg-white"
                    value={form.owner_id}
                    onChange={(e) => setForm({ ...form, owner_id: e.target.value })}
                  >
                    {users.map((u) => (
                      <option key={u.id} value={u.id}>
                        {u.full_name} ({u.email})
                      </option>
                    ))}
                  </select>
                </div>
              )}

              <div className="flex justify-end gap-2 pt-2 border-t border-gray-100">
                <button
                  type="button"
                  onClick={() => setOpen(false)}
                  className="px-4 py-2 rounded-xl text-sm font-medium text-gray-600 hover:bg-gray-100 transition"
                  disabled={submitting}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white px-5 py-2 rounded-xl text-sm font-medium flex items-center gap-2 shadow-sm transition disabled:opacity-60"
                >
                  {submitting ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" /> Saving...
                    </>
                  ) : (
                    "Save EV"
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
