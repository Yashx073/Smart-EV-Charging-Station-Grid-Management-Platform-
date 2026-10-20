import { useEffect, useState } from "react";
import API from "@/services/api";
import type { Grid, Source } from "@/types";
import { Plus, Trash2, Network, Edit2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/hooks/useAuth";

export default function GridsPage() {
  const [grids, setGrids] = useState<Grid[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [openModal, setOpenModal] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    name: "",
    voltage_level: "400kV",
    capacity_kw: 10000,
    current_load_kw: 2500,
    location: "Metroville North",
    status: "ACTIVE",
    source_id: "",
  });

  const { user } = useAuth();
  const isAdmin = user?.role === "admin";

  const loadData = async () => {
    setLoading(true);
    setError("");
    try {
      const [gRes, sRes] = await Promise.all([
        API.get<{ items: Grid[] }>("/grids"),
        API.get<{ items: Source[] }>("/sources"),
      ]);
      setGrids(gRes.data.items);
      setSources(sRes.data.items);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load power grids");
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
        name: formData.name,
        voltage_level: formData.voltage_level,
        capacity_kw: Number(formData.capacity_kw),
        current_load_kw: Number(formData.current_load_kw),
        location: formData.location,
        status: formData.status,
        source_id: formData.source_id || undefined,
      };

      if (editingId) {
        await API.put(`/grids/${editingId}`, payload);
      } else {
        await API.post("/grids", payload);
      }
      setOpenModal(false);
      setEditingId(null);
      loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to save power grid");
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this power grid?")) return;
    try {
      await API.delete(`/grids/${id}`);
      loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to delete power grid");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900">Power Grids</h1>
          <p className="text-sm text-gray-500">Manage electrical distribution grids, voltage levels, and capacity loads</p>
        </div>
        {isAdmin && (
          <button
            onClick={() => {
              setEditingId(null);
              setFormData({
                name: "",
                voltage_level: "400kV",
                capacity_kw: 10000,
                current_load_kw: 2500,
                location: "",
                status: "ACTIVE",
                source_id: sources[0]?.id || "",
              });
              setOpenModal(true);
            }}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition shadow-sm"
          >
            <Plus className="h-4 w-4" /> Add Power Grid
          </button>
        )}
      </div>

      {error && <div className="p-4 rounded-lg bg-red-50 text-red-700 text-sm border border-red-200">{error}</div>}

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base font-medium flex items-center gap-2">
            <Network className="h-5 w-5 text-blue-600" /> Regional Electrical Grids (Entity 8)
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="h-40 flex items-center justify-center text-gray-500">Loading grids...</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-gray-500">
                    <th className="text-left pb-3 font-medium">Grid Name</th>
                    <th className="text-left pb-3 font-medium">Voltage Level</th>
                    <th className="text-left pb-3 font-medium">Capacity</th>
                    <th className="text-left pb-3 font-medium">Current Load</th>
                    <th className="text-left pb-3 font-medium">Load %</th>
                    <th className="text-left pb-3 font-medium">Status</th>
                    <th className="text-left pb-3 font-medium">Location</th>
                    {isAdmin && <th className="text-right pb-3 font-medium">Actions</th>}
                  </tr>
                </thead>
                <tbody>
                  {grids.map((g) => {
                    const loadPct = g.capacity_kw > 0 ? Math.round((g.current_load_kw / g.capacity_kw) * 100) : 0;
                    return (
                      <tr key={g.id} className="border-b hover:bg-gray-50 transition">
                        <td className="py-3 font-medium text-gray-900">{g.name || g.grid_name}</td>
                        <td className="py-3 font-mono">{g.voltage_level || "400kV"}</td>
                        <td className="py-3 font-mono">{g.capacity_kw || g.capacity} kW</td>
                        <td className="py-3 font-mono">{g.current_load_kw || g.current_load} kW</td>
                        <td className="py-3">
                          <div className="flex items-center gap-2">
                            <div className="w-16 bg-gray-200 rounded-full h-2 overflow-hidden">
                              <div
                                className={`h-2 rounded-full ${loadPct > 85 ? "bg-red-500" : loadPct > 65 ? "bg-amber-500" : "bg-emerald-500"}`}
                                style={{ width: `${Math.min(loadPct, 100)}%` }}
                              />
                            </div>
                            <span className="text-xs font-mono">{loadPct}%</span>
                          </div>
                        </td>
                        <td className="py-3">
                          <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${g.status === "ACTIVE" ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-800"}`}>
                            {g.status}
                          </span>
                        </td>
                        <td className="py-3 text-gray-500">{g.location || "Central"}</td>
                        {isAdmin && (
                          <td className="py-3 text-right space-x-2">
                            <button
                              onClick={() => {
                                setEditingId(g.id);
                                setFormData({
                                  name: g.name,
                                  voltage_level: g.voltage_level || "400kV",
                                  capacity_kw: g.capacity_kw,
                                  current_load_kw: g.current_load_kw,
                                  location: g.location || "",
                                  status: g.status,
                                  source_id: g.source_id || "",
                                });
                                setOpenModal(true);
                              }}
                              className="text-gray-500 hover:text-blue-600 p-1"
                            >
                              <Edit2 className="h-4 w-4" />
                            </button>
                            <button
                              onClick={() => handleDelete(g.id)}
                              className="text-gray-500 hover:text-red-600 p-1"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </td>
                        )}
                      </tr>
                    );
                  })}
                  {grids.length === 0 && (
                    <tr>
                      <td colSpan={8} className="text-center py-6 text-gray-500">No power grids configured.</td>
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
            <h2 className="text-lg font-bold">{editingId ? "Edit Power Grid" : "Add Power Grid"}</h2>
            <form onSubmit={handleSave} className="space-y-3">
              <div>
                <label className="text-xs font-medium text-gray-700">Grid Name</label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full border rounded-lg p-2 text-sm mt-1"
                  placeholder="e.g. Metro South Grid"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-gray-700">Voltage Level</label>
                <input
                  type="text"
                  required
                  value={formData.voltage_level}
                  onChange={(e) => setFormData({ ...formData, voltage_level: e.target.value })}
                  className="w-full border rounded-lg p-2 text-sm mt-1"
                  placeholder="e.g. 400kV, 220kV, 33kV"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium text-gray-700">Capacity (kW)</label>
                  <input
                    type="number"
                    min="0"
                    required
                    value={formData.capacity_kw}
                    onChange={(e) => setFormData({ ...formData, capacity_kw: Number(e.target.value) })}
                    className="w-full border rounded-lg p-2 text-sm mt-1"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-700">Current Load (kW)</label>
                  <input
                    type="number"
                    min="0"
                    required
                    value={formData.current_load_kw}
                    onChange={(e) => setFormData({ ...formData, current_load_kw: Number(e.target.value) })}
                    className="w-full border rounded-lg p-2 text-sm mt-1"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-medium text-gray-700">Supplying Source (Entity 4 Ref)</label>
                <select
                  value={formData.source_id}
                  onChange={(e) => setFormData({ ...formData, source_id: e.target.value })}
                  className="w-full border rounded-lg p-2 text-sm mt-1"
                >
                  <option value="">Select an energy source...</option>
                  {sources.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name} ({s.source_type} - {s.capacity_kw}kW)
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-xs font-medium text-gray-700">Location / Region</label>
                <input
                  type="text"
                  value={formData.location}
                  onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                  className="w-full border rounded-lg p-2 text-sm mt-1"
                  placeholder="e.g. Sector 5 Industrial"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-gray-700">Status</label>
                <select
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                  className="w-full border rounded-lg p-2 text-sm mt-1"
                >
                  <option value="ACTIVE">ACTIVE</option>
                  <option value="INACTIVE">INACTIVE</option>
                  <option value="MAINTENANCE">MAINTENANCE</option>
                </select>
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
