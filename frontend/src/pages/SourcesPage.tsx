import { useEffect, useState } from "react";
import API from "@/services/api";
import type { Source, RenewableSource, NonRenewableSource } from "@/types";
import { Plus, Trash2, Sun, Flame, Zap, Edit2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/hooks/useAuth";

export default function SourcesPage() {
  const [tab, setTab] = useState<"all" | "renewable" | "non_renewable">("all");
  const [sources, setSources] = useState<Source[]>([]);
  const [renewables, setRenewables] = useState<RenewableSource[]>([]);
  const [nonRenewables, setNonRenewables] = useState<NonRenewableSource[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [openModal, setOpenModal] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);

  // Form state
  const [formData, setFormData] = useState({
    name: "",
    source_type: "RENEWABLE",
    capacity_kw: 1000,
    status: "ACTIVE",
    description: "",
    // subtype fields
    renewable_type: "SOLAR",
    generation_efficiency: 25.0,
    fuel_type: "NATURAL_GAS",
    emission_rate: 0.45,
  });

  const { user } = useAuth();
  const isAdmin = user?.role === "admin";

  const loadData = async () => {
    setLoading(true);
    setError("");
    try {
      const [srcRes, renRes, nonRes] = await Promise.all([
        API.get<{ items: Source[] }>("/sources"),
        API.get<{ items: RenewableSource[] }>("/renewable-sources"),
        API.get<{ items: NonRenewableSource[] }>("/non-renewable-sources"),
      ]);
      setSources(srcRes.data.items);
      setRenewables(renRes.data.items);
      setNonRenewables(nonRes.data.items);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load energy sources");
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
      if (tab === "all") {
        const payload = {
          name: formData.name,
          source_type: formData.source_type,
          capacity_kw: Number(formData.capacity_kw),
          status: formData.status,
          description: formData.description,
        };
        if (editingId) {
          await API.put(`/sources/${editingId}`, payload);
        } else {
          await API.post("/sources", payload);
        }
      } else if (tab === "renewable") {
        const payload = {
          source_id: editingId || sources[0]?.id || "",
          renewable_type: formData.renewable_type,
          generation_efficiency: Number(formData.generation_efficiency),
          name: formData.name,
          capacity_kw: Number(formData.capacity_kw),
          status: formData.status,
        };
        if (editingId) {
          await API.put(`/renewable-sources/${editingId}`, payload);
        } else {
          await API.post("/renewable-sources", payload);
        }
      } else if (tab === "non_renewable") {
        const payload = {
          source_id: editingId || sources[0]?.id || "",
          fuel_type: formData.fuel_type,
          emission_rate: Number(formData.emission_rate),
          name: formData.name,
          capacity_kw: Number(formData.capacity_kw),
          status: formData.status,
        };
        if (editingId) {
          await API.put(`/non-renewable-sources/${editingId}`, payload);
        } else {
          await API.post("/non-renewable-sources", payload);
        }
      }
      setOpenModal(false);
      setEditingId(null);
      loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Save operation failed");
    }
  };

  const handleDelete = async (id: string, type: "sources" | "renewable-sources" | "non-renewable-sources") => {
    if (!confirm("Are you sure you want to delete this source record?")) return;
    try {
      await API.delete(`/${type}/${id}`);
      loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Delete operation failed");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900">Energy Sources</h1>
          <p className="text-sm text-gray-500">Manage power generation, renewable assets, and grid supplies</p>
        </div>
        {isAdmin && (
          <button
            onClick={() => {
              setEditingId(null);
              setFormData({
                name: "",
                source_type: tab === "non_renewable" ? "NON_RENEWABLE" : "RENEWABLE",
                capacity_kw: 1000,
                status: "ACTIVE",
                description: "",
                renewable_type: "SOLAR",
                generation_efficiency: 25.0,
                fuel_type: "NATURAL_GAS",
                emission_rate: 0.45,
              });
              setOpenModal(true);
            }}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition shadow-sm"
          >
            <Plus className="h-4 w-4" /> Add {tab === "renewable" ? "Renewable Subtype" : tab === "non_renewable" ? "Non-Renewable Subtype" : "Source"}
          </button>
        )}
      </div>

      {error && <div className="p-4 rounded-lg bg-red-50 text-red-700 text-sm border border-red-200">{error}</div>}

      {/* Tabs */}
      <div className="flex border-b border-gray-200 gap-6">
        <button
          onClick={() => setTab("all")}
          className={`pb-3 text-sm font-semibold border-b-2 flex items-center gap-2 transition ${
            tab === "all" ? "border-blue-600 text-blue-600" : "border-transparent text-gray-500 hover:text-gray-700"
          }`}
        >
          <Zap className="h-4 w-4" /> All Sources ({sources.length})
        </button>
        <button
          onClick={() => setTab("renewable")}
          className={`pb-3 text-sm font-semibold border-b-2 flex items-center gap-2 transition ${
            tab === "renewable" ? "border-green-600 text-green-600" : "border-transparent text-gray-500 hover:text-gray-700"
          }`}
        >
          <Sun className="h-4 w-4 text-green-600" /> Renewable Subtypes ({renewables.length})
        </button>
        <button
          onClick={() => setTab("non_renewable")}
          className={`pb-3 text-sm font-semibold border-b-2 flex items-center gap-2 transition ${
            tab === "non_renewable" ? "border-amber-600 text-amber-600" : "border-transparent text-gray-500 hover:text-gray-700"
          }`}
        >
          <Flame className="h-4 w-4 text-amber-600" /> Non-Renewable Subtypes ({nonRenewables.length})
        </button>
      </div>

      {/* Content */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base font-medium">
            {tab === "all" && "Energy Source Master Registry (Entity 4)"}
            {tab === "renewable" && "Renewable Generation Assets (Entity 19)"}
            {tab === "non_renewable" && "Non-Renewable Power Plants (Entity 20)"}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="h-40 flex items-center justify-center text-gray-500">Loading sources...</div>
          ) : (
            <div className="overflow-x-auto">
              {tab === "all" && (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b text-gray-500">
                      <th className="text-left pb-3 font-medium">Source Name</th>
                      <th className="text-left pb-3 font-medium">Type</th>
                      <th className="text-left pb-3 font-medium">Capacity</th>
                      <th className="text-left pb-3 font-medium">Energy Generated</th>
                      <th className="text-left pb-3 font-medium">Status</th>
                      {isAdmin && <th className="text-right pb-3 font-medium">Actions</th>}
                    </tr>
                  </thead>
                  <tbody>
                    {sources.map((s) => (
                      <tr key={s.id} className="border-b hover:bg-gray-50 transition">
                        <td className="py-3 font-medium text-gray-900">{s.name || s.source_name}</td>
                        <td className="py-3">
                          <span className={`px-2 py-0.5 rounded text-xs font-medium ${s.source_type.toUpperCase().includes("RENEWABLE") ? "bg-green-100 text-green-800" : "bg-amber-100 text-amber-800"}`}>
                            {s.source_type}
                          </span>
                        </td>
                        <td className="py-3 font-mono">{s.capacity_kw || s.capacity} kW</td>
                        <td className="py-3 font-mono">{s.energy_generated_kwh} kWh</td>
                        <td className="py-3">
                          <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-800">
                            {s.status}
                          </span>
                        </td>
                        {isAdmin && (
                          <td className="py-3 text-right space-x-2">
                            <button
                              onClick={() => {
                                setEditingId(s.id);
                                setFormData({
                                  ...formData,
                                  name: s.name,
                                  source_type: s.source_type,
                                  capacity_kw: s.capacity_kw,
                                  status: s.status,
                                  description: s.description || "",
                                });
                                setOpenModal(true);
                              }}
                              className="text-gray-500 hover:text-blue-600 p-1"
                            >
                              <Edit2 className="h-4 w-4" />
                            </button>
                            <button
                              onClick={() => handleDelete(s.id, "sources")}
                              className="text-gray-500 hover:text-red-600 p-1"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </td>
                        )}
                      </tr>
                    ))}
                    {sources.length === 0 && (
                      <tr>
                        <td colSpan={6} className="text-center py-6 text-gray-500">No energy sources registered yet.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              )}

              {tab === "renewable" && (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b text-gray-500">
                      <th className="text-left pb-3 font-medium">Source Ref / Name</th>
                      <th className="text-left pb-3 font-medium">Renewable Technology</th>
                      <th className="text-left pb-3 font-medium">Generation Efficiency</th>
                      <th className="text-left pb-3 font-medium">Capacity</th>
                      <th className="text-left pb-3 font-medium">Status</th>
                      {isAdmin && <th className="text-right pb-3 font-medium">Actions</th>}
                    </tr>
                  </thead>
                  <tbody>
                    {renewables.map((r) => (
                      <tr key={r.id} className="border-b hover:bg-gray-50 transition">
                        <td className="py-3 font-medium text-gray-900">{r.name || r.source_id}</td>
                        <td className="py-3">
                          <span className="px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                            {r.renewable_type}
                          </span>
                        </td>
                        <td className="py-3 font-mono">{r.generation_efficiency != null ? `${r.generation_efficiency}%` : "N/A"}</td>
                        <td className="py-3 font-mono">{r.capacity_kw} kW</td>
                        <td className="py-3">
                          <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
                            {r.status}
                          </span>
                        </td>
                        {isAdmin && (
                          <td className="py-3 text-right">
                            <button
                              onClick={() => handleDelete(r.id, "renewable-sources")}
                              className="text-gray-500 hover:text-red-600 p-1"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </td>
                        )}
                      </tr>
                    ))}
                    {renewables.length === 0 && (
                      <tr>
                        <td colSpan={6} className="text-center py-6 text-gray-500">No renewable sources registered.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              )}

              {tab === "non_renewable" && (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b text-gray-500">
                      <th className="text-left pb-3 font-medium">Source Ref / Name</th>
                      <th className="text-left pb-3 font-medium">Fuel Type</th>
                      <th className="text-left pb-3 font-medium">Emission Rate</th>
                      <th className="text-left pb-3 font-medium">Capacity</th>
                      <th className="text-left pb-3 font-medium">Status</th>
                      {isAdmin && <th className="text-right pb-3 font-medium">Actions</th>}
                    </tr>
                  </thead>
                  <tbody>
                    {nonRenewables.map((nr) => (
                      <tr key={nr.id} className="border-b hover:bg-gray-50 transition">
                        <td className="py-3 font-medium text-gray-900">{nr.name || nr.source_id}</td>
                        <td className="py-3">
                          <span className="px-2 py-0.5 rounded text-xs font-medium bg-amber-100 text-amber-800">
                            {nr.fuel_type}
                          </span>
                        </td>
                        <td className="py-3 font-mono">{nr.emission_rate != null ? `${nr.emission_rate} kg/kWh` : "N/A"}</td>
                        <td className="py-3 font-mono">{nr.capacity_kw} kW</td>
                        <td className="py-3">
                          <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800">
                            {nr.status}
                          </span>
                        </td>
                        {isAdmin && (
                          <td className="py-3 text-right">
                            <button
                              onClick={() => handleDelete(nr.id, "non-renewable-sources")}
                              className="text-gray-500 hover:text-red-600 p-1"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </td>
                        )}
                      </tr>
                    ))}
                    {nonRenewables.length === 0 && (
                      <tr>
                        <td colSpan={6} className="text-center py-6 text-gray-500">No non-renewable sources registered.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Modal */}
      {openModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6 space-y-4">
            <h2 className="text-lg font-bold">
              {editingId ? "Edit Source" : `Create ${tab === "renewable" ? "Renewable Asset" : tab === "non_renewable" ? "Non-Renewable Asset" : "Energy Source"}`}
            </h2>
            <form onSubmit={handleSave} className="space-y-3">
              <div>
                <label className="text-xs font-medium text-gray-700">Source Name</label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full border rounded-lg p-2 text-sm mt-1"
                  placeholder="e.g. Solar Park A"
                />
              </div>

              {tab === "all" && (
                <div>
                  <label className="text-xs font-medium text-gray-700">Source Type</label>
                  <select
                    value={formData.source_type}
                    onChange={(e) => setFormData({ ...formData, source_type: e.target.value })}
                    className="w-full border rounded-lg p-2 text-sm mt-1"
                  >
                    <option value="RENEWABLE">RENEWABLE</option>
                    <option value="NON_RENEWABLE">NON_RENEWABLE</option>
                  </select>
                </div>
              )}

              {tab === "renewable" && (
                <>
                  <div>
                    <label className="text-xs font-medium text-gray-700">Renewable Technology</label>
                    <select
                      value={formData.renewable_type}
                      onChange={(e) => setFormData({ ...formData, renewable_type: e.target.value })}
                      className="w-full border rounded-lg p-2 text-sm mt-1"
                    >
                      <option value="SOLAR">SOLAR</option>
                      <option value="WIND">WIND</option>
                      <option value="HYDRO">HYDRO</option>
                      <option value="BIOMASS">BIOMASS</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-xs font-medium text-gray-700">Generation Efficiency (%)</label>
                    <input
                      type="number"
                      step="0.1"
                      min="0"
                      max="100"
                      value={formData.generation_efficiency}
                      onChange={(e) => setFormData({ ...formData, generation_efficiency: Number(e.target.value) })}
                      className="w-full border rounded-lg p-2 text-sm mt-1"
                    />
                  </div>
                </>
              )}

              {tab === "non_renewable" && (
                <>
                  <div>
                    <label className="text-xs font-medium text-gray-700">Fuel Type</label>
                    <select
                      value={formData.fuel_type}
                      onChange={(e) => setFormData({ ...formData, fuel_type: e.target.value })}
                      className="w-full border rounded-lg p-2 text-sm mt-1"
                    >
                      <option value="NATURAL_GAS">NATURAL_GAS</option>
                      <option value="COAL">COAL</option>
                      <option value="DIESEL">DIESEL</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-xs font-medium text-gray-700">Emission Rate (kg/kWh)</label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={formData.emission_rate}
                      onChange={(e) => setFormData({ ...formData, emission_rate: Number(e.target.value) })}
                      className="w-full border rounded-lg p-2 text-sm mt-1"
                    />
                  </div>
                </>
              )}

              <div>
                <label className="text-xs font-medium text-gray-700">Capacity (kW)</label>
                <input
                  type="number"
                  step="10"
                  min="0"
                  required
                  value={formData.capacity_kw}
                  onChange={(e) => setFormData({ ...formData, capacity_kw: Number(e.target.value) })}
                  className="w-full border rounded-lg p-2 text-sm mt-1"
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
