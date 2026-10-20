import { useEffect, useState } from "react";
import API from "@/services/api";
import type { Schedule, Station } from "@/types";
import { Plus, Trash2, Calendar, Clock, Edit2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/hooks/useAuth";

export default function SchedulesPage() {
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [stations, setStations] = useState<Station[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [openModal, setOpenModal] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    station_id: "",
    schedule_date: new Date().toISOString().split("T")[0],
    start_time: "08:00",
    end_time: "18:00",
    available_slots: 10,
    schedule_type: "REGULAR",
    is_available: true,
    note: "Standard daily operating hours",
  });

  const { user } = useAuth();
  const isAdmin = user?.role === "admin";

  const loadData = async () => {
    setLoading(true);
    setError("");
    try {
      const [schRes, stnRes] = await Promise.all([
        API.get<{ items: Schedule[] }>("/schedules"),
        API.get<{ items: Station[] }>("/stations"),
      ]);
      setSchedules(schRes.data.items);
      setStations(stnRes.data.items);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load station schedules");
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
      const startDateTime = new Date(`${formData.schedule_date}T${formData.start_time}:00Z`).toISOString();
      const endDateTime = new Date(`${formData.schedule_date}T${formData.end_time}:00Z`).toISOString();

      const payload = {
        station_id: formData.station_id || stations[0]?.id,
        schedule_date: formData.schedule_date,
        start_time: startDateTime,
        end_time: endDateTime,
        available_slots: Number(formData.available_slots),
        schedule_type: formData.schedule_type,
        is_available: formData.is_available,
        note: formData.note,
        description: formData.note,
      };

      if (editingId) {
        await API.put(`/schedules/${editingId}`, payload);
      } else {
        await API.post("/schedules", payload);
      }
      setOpenModal(false);
      setEditingId(null);
      loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to save schedule");
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this schedule?")) return;
    try {
      await API.delete(`/schedules/${id}`);
      loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to delete schedule");
    }
  };

  const getStationName = (sid: string) => {
    const s = stations.find((st) => st.id === sid);
    return s ? `${s.name} (${s.station_code})` : sid;
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900">Station Schedules</h1>
          <p className="text-sm text-gray-500">Manage station operating slots, availability windows, and schedule types</p>
        </div>
        {isAdmin && (
          <button
            onClick={() => {
              setEditingId(null);
              setFormData({
                station_id: stations[0]?.id || "",
                schedule_date: new Date().toISOString().split("T")[0],
                start_time: "08:00",
                end_time: "18:00",
                available_slots: 10,
                schedule_type: "REGULAR",
                is_available: true,
                note: "",
              });
              setOpenModal(true);
            }}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition shadow-sm"
          >
            <Plus className="h-4 w-4" /> Add Schedule Window
          </button>
        )}
      </div>

      {error && <div className="p-4 rounded-lg bg-red-50 text-red-700 text-sm border border-red-200">{error}</div>}

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base font-medium flex items-center gap-2">
            <Calendar className="h-5 w-5 text-blue-600" /> Operational Schedules (Entity 15)
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="h-40 flex items-center justify-center text-gray-500">Loading schedules...</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-gray-500">
                    <th className="text-left pb-3 font-medium">Station</th>
                    <th className="text-left pb-3 font-medium">Date</th>
                    <th className="text-left pb-3 font-medium">Time Window</th>
                    <th className="text-left pb-3 font-medium">Slots</th>
                    <th className="text-left pb-3 font-medium">Type</th>
                    <th className="text-left pb-3 font-medium">Status</th>
                    <th className="text-left pb-3 font-medium">Notes</th>
                    {isAdmin && <th className="text-right pb-3 font-medium">Actions</th>}
                  </tr>
                </thead>
                <tbody>
                  {schedules.map((s) => (
                    <tr key={s.id} className="border-b hover:bg-gray-50 transition">
                      <td className="py-3 font-medium text-gray-900">{getStationName(s.station_id)}</td>
                      <td className="py-3 font-mono">{s.schedule_date || s.start_time.split("T")[0]}</td>
                      <td className="py-3 text-gray-600 flex items-center gap-1">
                        <Clock className="h-3.5 w-3.5 text-gray-400" />
                        {s.start_time.substring(11, 16)} – {s.end_time.substring(11, 16)} UTC
                      </td>
                      <td className="py-3 font-mono">{s.available_slots} slots</td>
                      <td className="py-3">
                        <span className="px-2 py-0.5 rounded text-xs font-semibold bg-blue-50 text-blue-700">
                          {s.schedule_type || "REGULAR"}
                        </span>
                      </td>
                      <td className="py-3">
                        <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${s.is_available ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}`}>
                          {s.is_available ? "Available" : "Closed"}
                        </span>
                      </td>
                      <td className="py-3 text-gray-500 max-w-xs truncate">{s.note || s.description || "—"}</td>
                      {isAdmin && (
                        <td className="py-3 text-right space-x-2">
                          <button
                            onClick={() => {
                              setEditingId(s.id);
                              setFormData({
                                station_id: s.station_id,
                                schedule_date: s.schedule_date || s.start_time.split("T")[0],
                                start_time: s.start_time.substring(11, 16),
                                end_time: s.end_time.substring(11, 16),
                                available_slots: s.available_slots,
                                schedule_type: s.schedule_type || "REGULAR",
                                is_available: s.is_available,
                                note: s.note || "",
                              });
                              setOpenModal(true);
                            }}
                            className="text-gray-500 hover:text-blue-600 p-1"
                          >
                            <Edit2 className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleDelete(s.id)}
                            className="text-gray-500 hover:text-red-600 p-1"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </td>
                      )}
                    </tr>
                  ))}
                  {schedules.length === 0 && (
                    <tr>
                      <td colSpan={8} className="text-center py-6 text-gray-500">No schedules created yet.</td>
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
            <h2 className="text-lg font-bold">{editingId ? "Edit Schedule" : "Add Station Schedule"}</h2>
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
                <label className="text-xs font-medium text-gray-700">Schedule Date</label>
                <input
                  type="date"
                  required
                  value={formData.schedule_date}
                  onChange={(e) => setFormData({ ...formData, schedule_date: e.target.value })}
                  className="w-full border rounded-lg p-2 text-sm mt-1"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium text-gray-700">Start Time (UTC)</label>
                  <input
                    type="time"
                    required
                    value={formData.start_time}
                    onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
                    className="w-full border rounded-lg p-2 text-sm mt-1"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-700">End Time (UTC)</label>
                  <input
                    type="time"
                    required
                    value={formData.end_time}
                    onChange={(e) => setFormData({ ...formData, end_time: e.target.value })}
                    className="w-full border rounded-lg p-2 text-sm mt-1"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium text-gray-700">Available Slots</label>
                  <input
                    type="number"
                    min="1"
                    required
                    value={formData.available_slots}
                    onChange={(e) => setFormData({ ...formData, available_slots: Number(e.target.value) })}
                    className="w-full border rounded-lg p-2 text-sm mt-1"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-700">Schedule Type</label>
                  <select
                    value={formData.schedule_type}
                    onChange={(e) => setFormData({ ...formData, schedule_type: e.target.value })}
                    className="w-full border rounded-lg p-2 text-sm mt-1"
                  >
                    <option value="REGULAR">REGULAR</option>
                    <option value="PEAK_HOURS">PEAK_HOURS</option>
                    <option value="MAINTENANCE_WINDOW">MAINTENANCE_WINDOW</option>
                    <option value="SPECIAL_EVENT">SPECIAL_EVENT</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="text-xs font-medium text-gray-700">Notes / Operating Notes</label>
                <input
                  type="text"
                  value={formData.note}
                  onChange={(e) => setFormData({ ...formData, note: e.target.value })}
                  className="w-full border rounded-lg p-2 text-sm mt-1"
                  placeholder="e.g. Regular station schedule"
                />
              </div>

              <div className="flex items-center gap-2 pt-2">
                <input
                  type="checkbox"
                  id="avail_chk"
                  checked={formData.is_available}
                  onChange={(e) => setFormData({ ...formData, is_available: e.target.checked })}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <label htmlFor="avail_chk" className="text-xs font-medium text-gray-700">Is Station Available for Charging</label>
              </div>

              <div className="flex justify-end gap-2 pt-3">
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
