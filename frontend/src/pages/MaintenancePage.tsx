import { useEffect, useState } from "react";
import API from "@/services/api";
import type { Maintenance, PreventiveMaintenance, CorrectiveMaintenance, Station, Admin } from "@/types";
import { Plus, Trash2, Wrench, ShieldAlert, CheckCircle2, Edit2, Calendar } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/hooks/useAuth";

export default function MaintenancePage() {
  const [tab, setTab] = useState<"all" | "preventive" | "corrective">("all");
  const [items, setItems] = useState<Maintenance[]>([]);
  const [prevItems, setPrevItems] = useState<PreventiveMaintenance[]>([]);
  const [corrItems, setCorrItems] = useState<CorrectiveMaintenance[]>([]);
  const [stations, setStations] = useState<Station[]>([]);
  const [admins, setAdmins] = useState<Admin[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [openModal, setOpenModal] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    station_id: "",
    admin_id: "",
    maintenance_type: "PREVENTIVE",
    title: "",
    description: "",
    cost: 100,
    status: "planned",
    scheduled_date: new Date().toISOString().split("T")[0],
    // Preventive
    maintenance_interval: 30,
    next_due_date: new Date(Date.now() + 30 * 86400000).toISOString().split("T")[0],
    checklist: "Visual inspection; Insulation test; RCD check",
    inspection_result: "PASSED",
    // Corrective
    fault_description: "",
    repair_action: "",
    severity: "MEDIUM",
    downtime: 2.0,
    resolution_status: "IN_PROGRESS",
  });

  const { user } = useAuth();
  const isAdmin = user?.role === "admin";

  const loadData = async () => {
    setLoading(true);
    setError("");
    try {
      const [mRes, pRes, cRes, stnRes, admRes] = await Promise.all([
        API.get<{ items: Maintenance[] }>("/maintenance"),
        API.get<{ items: PreventiveMaintenance[] }>("/preventive-maintenance"),
        API.get<{ items: CorrectiveMaintenance[] }>("/corrective-maintenance"),
        API.get<{ items: Station[] }>("/stations"),
        API.get<{ items: Admin[] }>("/admins").catch(() => ({ data: { items: [] } })),
      ]);
      setItems(mRes.data.items);
      setPrevItems(pRes.data.items);
      setCorrItems(cRes.data.items);
      setStations(stnRes.data.items);
      setAdmins(admRes.data.items);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load maintenance records");
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
          station_id: formData.station_id || stations[0]?.id,
          admin_id: formData.admin_id || undefined,
          maintenance_type: formData.maintenance_type,
          title: formData.title,
          description: formData.description,
          cost: Number(formData.cost),
          status: formData.status,
          scheduled_date: formData.scheduled_date ? new Date(formData.scheduled_date).toISOString() : undefined,
        };
        if (editingId) {
          await API.put(`/maintenance/${editingId}`, payload);
        } else {
          await API.post("/maintenance", payload);
        }
      } else if (tab === "preventive") {
        const payload = {
          maintenance_id: editingId || items[0]?.id || "",
          station_id: formData.station_id || stations[0]?.id,
          maintenance_interval: Number(formData.maintenance_interval),
          next_due_date: formData.next_due_date,
          checklist: formData.checklist,
          inspection_result: formData.inspection_result,
          title: formData.title,
          description: formData.description,
          status: formData.status,
        };
        if (editingId) {
          await API.put(`/preventive-maintenance/${editingId}`, payload);
        } else {
          await API.post("/preventive-maintenance", payload);
        }
      } else if (tab === "corrective") {
        const payload = {
          maintenance_id: editingId || items[0]?.id || "",
          station_id: formData.station_id || stations[0]?.id,
          fault_title: formData.title,
          fault_description: formData.fault_description || formData.description,
          repair_action: formData.repair_action,
          severity: formData.severity,
          downtime: Number(formData.downtime),
          resolution_status: formData.resolution_status,
          status: formData.status,
        };
        if (editingId) {
          await API.put(`/corrective-maintenance/${editingId}`, payload);
        } else {
          await API.post("/corrective-maintenance", payload);
        }
      }
      setOpenModal(false);
      setEditingId(null);
      loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Save operation failed");
    }
  };

  const handleDelete = async (id: string, endpoint: "maintenance" | "preventive-maintenance" | "corrective-maintenance") => {
    if (!confirm("Delete this maintenance record?")) return;
    try {
      await API.delete(`/${endpoint}/${id}`);
      loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Delete operation failed");
    }
  };

  const getStationCode = (sid?: string | null) => {
    if (!sid) return "Station";
    const s = stations.find((st) => st.id === sid);
    return s ? `${s.name} (${s.station_code})` : sid;
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900">Station Maintenance</h1>
          <p className="text-sm text-gray-500">Track routine inspections, preventive checklists, and corrective repairs</p>
        </div>
        {isAdmin && (
          <button
            onClick={() => {
              setEditingId(null);
              setFormData({
                station_id: stations[0]?.id || "",
                admin_id: admins[0]?.id || "",
                maintenance_type: tab === "corrective" ? "CORRECTIVE" : "PREVENTIVE",
                title: "",
                description: "",
                cost: 150,
                status: "planned",
                scheduled_date: new Date().toISOString().split("T")[0],
                maintenance_interval: 30,
                next_due_date: new Date(Date.now() + 30 * 86400000).toISOString().split("T")[0],
                checklist: "Visual check; ground continuity; RCD test",
                inspection_result: "PASSED",
                fault_description: "",
                repair_action: "",
                severity: "MEDIUM",
                downtime: 2.0,
                resolution_status: "IN_PROGRESS",
              });
              setOpenModal(true);
            }}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition shadow-sm"
          >
            <Plus className="h-4 w-4" /> Add {tab === "preventive" ? "Preventive Log" : tab === "corrective" ? "Corrective Repair" : "Maintenance Order"}
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
          <Wrench className="h-4 w-4" /> Maintenance Orders (Entity 16) ({items.length})
        </button>
        <button
          onClick={() => setTab("preventive")}
          className={`pb-3 text-sm font-semibold border-b-2 flex items-center gap-2 transition ${
            tab === "preventive" ? "border-emerald-600 text-emerald-600" : "border-transparent text-gray-500 hover:text-gray-700"
          }`}
        >
          <CheckCircle2 className="h-4 w-4 text-emerald-600" /> Preventive Subtypes (Entity 21) ({prevItems.length})
        </button>
        <button
          onClick={() => setTab("corrective")}
          className={`pb-3 text-sm font-semibold border-b-2 flex items-center gap-2 transition ${
            tab === "corrective" ? "border-rose-600 text-rose-600" : "border-transparent text-gray-500 hover:text-gray-700"
          }`}
        >
          <ShieldAlert className="h-4 w-4 text-rose-600" /> Corrective Subtypes (Entity 22) ({corrItems.length})
        </button>
      </div>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base font-medium">
            {tab === "all" && "All Station Maintenance Records"}
            {tab === "preventive" && "Scheduled Preventive Maintenance Checklists"}
            {tab === "corrective" && "Corrective Fault Reports & Repair Downtimes"}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="h-40 flex items-center justify-center text-gray-500">Loading maintenance data...</div>
          ) : (
            <div className="overflow-x-auto">
              {tab === "all" && (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b text-gray-500">
                      <th className="text-left pb-3 font-medium">Station</th>
                      <th className="text-left pb-3 font-medium">Title</th>
                      <th className="text-left pb-3 font-medium">Type</th>
                      <th className="text-left pb-3 font-medium">Scheduled Date</th>
                      <th className="text-left pb-3 font-medium">Cost</th>
                      <th className="text-left pb-3 font-medium">Status</th>
                      {isAdmin && <th className="text-right pb-3 font-medium">Actions</th>}
                    </tr>
                  </thead>
                  <tbody>
                    {items.map((m) => (
                      <tr key={m.id} className="border-b hover:bg-gray-50 transition">
                        <td className="py-3 font-medium text-gray-900">{getStationCode(m.station_id)}</td>
                        <td className="py-3 text-gray-900 font-medium">{m.title || m.description}</td>
                        <td className="py-3">
                          <span className={`px-2 py-0.5 rounded text-xs font-semibold ${m.maintenance_type === "CORRECTIVE" ? "bg-rose-100 text-rose-800" : "bg-emerald-100 text-emerald-800"}`}>
                            {m.maintenance_type}
                          </span>
                        </td>
                        <td className="py-3 text-gray-600">
                          {m.scheduled_date ? m.scheduled_date.split("T")[0] : m.maintenance_date || "—"}
                        </td>
                        <td className="py-3 font-mono font-semibold text-gray-900">₹{m.cost || 0}</td>
                        <td className="py-3">
                          <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-800">
                            {m.status}
                          </span>
                        </td>
                        {isAdmin && (
                          <td className="py-3 text-right space-x-2">
                            <button
                              onClick={() => {
                                setEditingId(m.id);
                                setFormData({
                                  ...formData,
                                  station_id: m.station_id || "",
                                  admin_id: m.admin_id || "",
                                  maintenance_type: m.maintenance_type,
                                  title: m.title || "",
                                  description: m.description || "",
                                  cost: m.cost || 0,
                                  status: m.status,
                                });
                                setOpenModal(true);
                              }}
                              className="text-gray-500 hover:text-blue-600 p-1"
                            >
                              <Edit2 className="h-4 w-4" />
                            </button>
                            <button
                              onClick={() => handleDelete(m.id, "maintenance")}
                              className="text-gray-500 hover:text-red-600 p-1"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </td>
                        )}
                      </tr>
                    ))}
                    {items.length === 0 && (
                      <tr>
                        <td colSpan={7} className="text-center py-6 text-gray-500">No maintenance records found.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              )}

              {tab === "preventive" && (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b text-gray-500">
                      <th className="text-left pb-3 font-medium">Station</th>
                      <th className="text-left pb-3 font-medium">Interval</th>
                      <th className="text-left pb-3 font-medium">Next Due Date</th>
                      <th className="text-left pb-3 font-medium">Checklist</th>
                      <th className="text-left pb-3 font-medium">Result</th>
                      <th className="text-left pb-3 font-medium">Status</th>
                      {isAdmin && <th className="text-right pb-3 font-medium">Actions</th>}
                    </tr>
                  </thead>
                  <tbody>
                    {prevItems.map((p) => (
                      <tr key={p.id} className="border-b hover:bg-gray-50 transition">
                        <td className="py-3 font-medium text-gray-900">{getStationCode(p.station_id)}</td>
                        <td className="py-3 font-mono">{p.maintenance_interval || 30} days</td>
                        <td className="py-3 font-mono text-gray-700">{p.next_due_date || "Scheduled"}</td>
                        <td className="py-3 text-xs text-gray-600 max-w-xs truncate">{p.checklist || "Standard check"}</td>
                        <td className="py-3">
                          <span className="px-2 py-0.5 rounded text-xs font-semibold bg-emerald-100 text-emerald-800">
                            {p.inspection_result || "PASSED"}
                          </span>
                        </td>
                        <td className="py-3">
                          <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-gray-100 text-gray-800">
                            {p.status}
                          </span>
                        </td>
                        {isAdmin && (
                          <td className="py-3 text-right">
                            <button
                              onClick={() => handleDelete(p.id, "preventive-maintenance")}
                              className="text-gray-500 hover:text-red-600 p-1"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </td>
                        )}
                      </tr>
                    ))}
                    {prevItems.length === 0 && (
                      <tr>
                        <td colSpan={7} className="text-center py-6 text-gray-500">No preventive maintenance records.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              )}

              {tab === "corrective" && (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b text-gray-500">
                      <th className="text-left pb-3 font-medium">Station</th>
                      <th className="text-left pb-3 font-medium">Fault Title</th>
                      <th className="text-left pb-3 font-medium">Severity</th>
                      <th className="text-left pb-3 font-medium">Repair Action</th>
                      <th className="text-left pb-3 font-medium">Downtime</th>
                      <th className="text-left pb-3 font-medium">Resolution</th>
                      {isAdmin && <th className="text-right pb-3 font-medium">Actions</th>}
                    </tr>
                  </thead>
                  <tbody>
                    {corrItems.map((c) => (
                      <tr key={c.id} className="border-b hover:bg-gray-50 transition">
                        <td className="py-3 font-medium text-gray-900">{getStationCode(c.station_id)}</td>
                        <td className="py-3 font-medium text-rose-700">{c.fault_title || c.fault_description}</td>
                        <td className="py-3">
                          <span className={`px-2 py-0.5 rounded text-xs font-semibold ${c.severity === "HIGH" ? "bg-red-100 text-red-800" : "bg-amber-100 text-amber-800"}`}>
                            {c.severity || "MEDIUM"}
                          </span>
                        </td>
                        <td className="py-3 text-xs text-gray-600 max-w-xs truncate">{c.repair_action || "Under evaluation"}</td>
                        <td className="py-3 font-mono">{c.downtime || 0} hrs</td>
                        <td className="py-3">
                          <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-gray-100 text-gray-800">
                            {c.resolution_status || c.status}
                          </span>
                        </td>
                        {isAdmin && (
                          <td className="py-3 text-right">
                            <button
                              onClick={() => handleDelete(c.id, "corrective-maintenance")}
                              className="text-gray-500 hover:text-red-600 p-1"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </td>
                        )}
                      </tr>
                    ))}
                    {corrItems.length === 0 && (
                      <tr>
                        <td colSpan={7} className="text-center py-6 text-gray-500">No corrective repair records.</td>
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
              {editingId ? "Edit Maintenance" : `Create ${tab === "preventive" ? "Preventive Task" : tab === "corrective" ? "Corrective Repair" : "Maintenance Order"}`}
            </h2>
            <form onSubmit={handleSave} className="space-y-3">
              <div>
                <label className="text-xs font-medium text-gray-700">Station</label>
                <select
                  value={formData.station_id}
                  onChange={(e) => setFormData({ ...formData, station_id: e.target.value })}
                  className="w-full border rounded-lg p-2 text-sm mt-1"
                  required
                >
                  <option value="">Select Station...</option>
                  {stations.map((st) => (
                    <option key={st.id} value={st.id}>
                      {st.name} ({st.station_code})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-xs font-medium text-gray-700">Title</label>
                <input
                  type="text"
                  required
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className="w-full border rounded-lg p-2 text-sm mt-1"
                  placeholder="e.g. Cable insulation test"
                />
              </div>

              {tab === "all" && (
                <>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="text-xs font-medium text-gray-700">Type</label>
                      <select
                        value={formData.maintenance_type}
                        onChange={(e) => setFormData({ ...formData, maintenance_type: e.target.value })}
                        className="w-full border rounded-lg p-2 text-sm mt-1"
                      >
                        <option value="PREVENTIVE">PREVENTIVE</option>
                        <option value="CORRECTIVE">CORRECTIVE</option>
                      </select>
                    </div>
                    <div>
                      <label className="text-xs font-medium text-gray-700">Cost (₹)</label>
                      <input
                        type="number"
                        min="0"
                        value={formData.cost}
                        onChange={(e) => setFormData({ ...formData, cost: Number(e.target.value) })}
                        className="w-full border rounded-lg p-2 text-sm mt-1"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="text-xs font-medium text-gray-700">Description</label>
                    <textarea
                      rows={2}
                      value={formData.description}
                      onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                      className="w-full border rounded-lg p-2 text-sm mt-1"
                    />
                  </div>
                </>
              )}

              {tab === "preventive" && (
                <>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="text-xs font-medium text-gray-700">Interval (days)</label>
                      <input
                        type="number"
                        min="1"
                        value={formData.maintenance_interval}
                        onChange={(e) => setFormData({ ...formData, maintenance_interval: Number(e.target.value) })}
                        className="w-full border rounded-lg p-2 text-sm mt-1"
                      />
                    </div>
                    <div>
                      <label className="text-xs font-medium text-gray-700">Next Due Date</label>
                      <input
                        type="date"
                        value={formData.next_due_date}
                        onChange={(e) => setFormData({ ...formData, next_due_date: e.target.value })}
                        className="w-full border rounded-lg p-2 text-sm mt-1"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="text-xs font-medium text-gray-700">Inspection Checklist</label>
                    <input
                      type="text"
                      value={formData.checklist}
                      onChange={(e) => setFormData({ ...formData, checklist: e.target.value })}
                      className="w-full border rounded-lg p-2 text-sm mt-1"
                    />
                  </div>
                </>
              )}

              {tab === "corrective" && (
                <>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="text-xs font-medium text-gray-700">Severity</label>
                      <select
                        value={formData.severity}
                        onChange={(e) => setFormData({ ...formData, severity: e.target.value })}
                        className="w-full border rounded-lg p-2 text-sm mt-1"
                      >
                        <option value="LOW">LOW</option>
                        <option value="MEDIUM">MEDIUM</option>
                        <option value="HIGH">HIGH</option>
                        <option value="CRITICAL">CRITICAL</option>
                      </select>
                    </div>
                    <div>
                      <label className="text-xs font-medium text-gray-700">Downtime (hrs)</label>
                      <input
                        type="number"
                        step="0.5"
                        value={formData.downtime}
                        onChange={(e) => setFormData({ ...formData, downtime: Number(e.target.value) })}
                        className="w-full border rounded-lg p-2 text-sm mt-1"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="text-xs font-medium text-gray-700">Repair Action</label>
                    <input
                      type="text"
                      value={formData.repair_action}
                      onChange={(e) => setFormData({ ...formData, repair_action: e.target.value })}
                      className="w-full border rounded-lg p-2 text-sm mt-1"
                    />
                  </div>
                </>
              )}

              <div>
                <label className="text-xs font-medium text-gray-700">Status</label>
                <select
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                  className="w-full border rounded-lg p-2 text-sm mt-1"
                >
                  <option value="planned">planned</option>
                  <option value="in_progress">in_progress</option>
                  <option value="completed">completed</option>
                  <option value="cancelled">cancelled</option>
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
