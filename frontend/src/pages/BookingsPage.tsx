import { useEffect, useState } from "react";
import API from "@/services/api";
import type { Station, Port, EV, Booking } from "@/types";
import { Calendar, Plus, Trash2, RefreshCw, AlertCircle, CheckCircle2, Loader2, X, Clock, MapPin, Zap } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/hooks/useAuth";

export default function BookingsPage() {
  const { user, loading: authLoading } = useAuth();
  const isAdmin = user?.role === "admin";

  const [stations, setStations] = useState<Station[]>([]);
  const [ports, setPorts] = useState<Port[]>([]);
  const [evs, setEvs] = useState<EV[]>([]);
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [open, setOpen] = useState(false);

  // Form states
  const [form, setForm] = useState({
    ev_id: "",
    station_id: "",
    port_id: "",
    start_time: "",
    end_time: "",
  });

  const loadData = async () => {
    setLoading(true);
    setError("");
    try {
      const [sRes, eRes, pRes, bRes] = await Promise.all([
        API.get<{ items: Station[] }>("/stations"),
        API.get<{ items: EV[] }>("/evs"),
        API.get<{ items: Port[] }>("/ports"),
        API.get<{ items: Booking[] }>("/bookings"),
      ]);

      const stList = sRes.data.items || [];
      const evList = eRes.data.items || [];
      const ptList = pRes.data.items || [];
      const bkList = bRes.data.items || [];

      setStations(stList);
      setEvs(evList);
      setPorts(ptList);

      if (isAdmin) {
        setBookings(bkList);
      } else {
        setBookings(bkList.filter((b) => b.user_id === user?.id || (b as any).owner_id === user?.id));
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load bookings data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!authLoading) {
      loadData();
    }
  }, [authLoading, isAdmin, user?.id]);

  const handleOpenModal = () => {
    // Generate default times: start in 30 mins, end in 90 mins
    const now = new Date();
    const start = new Date(now.getTime() + 30 * 60 * 1000);
    const end = new Date(now.getTime() + 90 * 60 * 1000);

    const pad = (n: number) => String(n).padStart(2, "0");
    const formatLocal = (d: Date) =>
      `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;

    const defaultStation = stations.length > 0 ? stations[0].id : "";
    const filteredPorts = ports.filter((p) => !defaultStation || p.station_id === defaultStation);
    const defaultPort = filteredPorts.length > 0 ? filteredPorts[0].id : "";
    const defaultEv = evs.length > 0 ? evs[0].id : "";

    setForm({
      ev_id: defaultEv,
      station_id: defaultStation,
      port_id: defaultPort,
      start_time: formatLocal(start),
      end_time: formatLocal(end),
    });
    setError("");
    setSuccess("");
    setOpen(true);
  };

  const handleStationChange = (stId: string) => {
    const stationPorts = ports.filter((p) => p.station_id === stId);
    setForm({
      ...form,
      station_id: stId,
      port_id: stationPorts.length > 0 ? stationPorts[0].id : "",
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess("");

    if (!form.ev_id) {
      setError("Please select your electric vehicle.");
      return;
    }
    if (!form.station_id) {
      setError("Please select a charging station.");
      return;
    }
    if (!form.port_id) {
      setError("Please select a port at the station.");
      return;
    }
    if (!form.start_time || !form.end_time) {
      setError("Please specify both start and end times.");
      return;
    }
    if (new Date(form.end_time) <= new Date(form.start_time)) {
      setError("Reservation end time must be after start time.");
      return;
    }

    setSubmitting(true);
    try {
      // Send ISO string in UTC
      const startIso = new Date(form.start_time).toISOString();
      const endIso = new Date(form.end_time).toISOString();

      await API.post("/bookings", {
        ev_id: form.ev_id,
        station_id: form.station_id,
        port_id: form.port_id,
        start_time: startIso,
        end_time: endIso,
      });

      setSuccess("Charging slot successfully reserved!");
      setOpen(false);
      loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Booking failed. The selected port may already be reserved for this slot.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleCancel = async (id: string) => {
    if (!confirm("Are you sure you want to cancel this booking?")) return;
    setError("");
    setSuccess("");
    try {
      await API.post(`/bookings/${id}/cancel`);
      setSuccess("Booking cancelled");
      loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to cancel booking");
    }
  };

  const handleStatus = async (id: string, newStatus: string) => {
    setError("");
    setSuccess("");
    try {
      await API.put(`/bookings/${id}/status`, { status: newStatus });
      setSuccess(`Booking status updated to ${newStatus}`);
      loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Status update failed");
    }
  };

  // Resolvers for human-friendly names
  const getEVLabel = (evId?: string) => {
    if (!evId) return "Unknown EV";
    const found = evs.find((e) => e.id === evId || (e as any)._id === evId);
    return found ? `${found.model} (${found.registration_number || (found as any).vehicle_number})` : `EV #${String(evId).slice(-6)}`;
  };

  const getStationLabel = (stId?: string) => {
    if (!stId) return "Unknown Station";
    const found = stations.find((s) => s.id === stId || (s as any)._id === stId);
    return found ? `${found.name} (${found.station_code})` : `Station #${String(stId).slice(-6)}`;
  };

  const getPortLabel = (ptId?: string) => {
    if (!ptId) return "Unknown Port";
    const found = ports.find((p) => p.id === ptId || (p as any)._id === ptId);
    return found ? `Port ${found.port_number} (${found.connector_type})` : `Port #${String(ptId).slice(-6)}`;
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "confirmed":
        return "bg-blue-50 text-blue-700 border-blue-200";
      case "active":
        return "bg-emerald-50 text-emerald-700 border-emerald-200";
      case "completed":
        return "bg-purple-50 text-purple-700 border-purple-200";
      case "cancelled":
        return "bg-red-50 text-red-700 border-red-200";
      default:
        return "bg-gray-100 text-gray-700 border-gray-200";
    }
  };

  const availablePortsForStation = ports.filter((p) => !form.station_id || p.station_id === form.station_id);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900">Charging Slot Reservations</h1>
          <p className="text-sm text-gray-500">
            {isAdmin ? "Manage and monitor all station slot bookings" : "Book charging ports and view your scheduled reservations"}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={loadData}
            className="flex items-center gap-2 border border-gray-300 bg-white hover:bg-gray-50 text-gray-700 px-3.5 py-2 rounded-xl text-sm font-medium transition shadow-sm"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} /> Refresh
          </button>
          {!isAdmin && (
            <button
              onClick={handleOpenModal}
              className="bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white px-4 py-2 rounded-xl text-sm font-medium flex items-center gap-2 shadow-sm transition"
            >
              <Calendar className="h-4 w-4" /> New Booking
            </button>
          )}
        </div>
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
            <Calendar className="h-5 w-5 text-blue-600" /> {isAdmin ? "All Reservation Records" : "My Bookings"}
          </CardTitle>
          <span className="text-xs font-medium text-gray-400">{bookings.length} reservations</span>
        </CardHeader>
        <CardContent className="pt-4">
          {loading ? (
            <div className="h-40 flex items-center justify-center text-gray-400">Loading bookings...</div>
          ) : bookings.length === 0 ? (
            <div className="text-center py-12">
              <Calendar className="h-12 w-12 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500 font-medium">No bookings found.</p>
              <p className="text-xs text-gray-400 mt-1 mb-4">
                {isAdmin ? "No bookings have been made yet." : "Reserve a port to ensure charging availability when you arrive."}
              </p>
              {!isAdmin && (
                <button
                  onClick={handleOpenModal}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-xl text-sm font-medium inline-flex items-center gap-2"
                >
                  <Plus className="h-4 w-4" /> Reserve a port
                </button>
              )}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead>
                  <tr className="border-b border-gray-100 text-gray-400 text-xs font-semibold uppercase tracking-wider">
                    <th className="pb-3">Vehicle</th>
                    <th className="pb-3">Station</th>
                    <th className="pb-3">Port</th>
                    <th className="pb-3">Start Time</th>
                    <th className="pb-3">End Time</th>
                    <th className="pb-3">Status</th>
                    <th className="pb-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {bookings.map((b) => (
                    <tr key={b.id} className="hover:bg-gray-50/70 transition">
                      <td className="py-3.5 font-medium text-gray-900">{getEVLabel(b.ev_id)}</td>
                      <td className="py-3.5 text-gray-700">{getStationLabel(b.station_id)}</td>
                      <td className="py-3.5 text-gray-600">
                        <span className="px-2 py-0.5 rounded text-xs bg-slate-100 text-slate-800 font-semibold border border-slate-200">
                          {getPortLabel(b.port_id)}
                        </span>
                      </td>
                      <td className="py-3.5 text-xs text-gray-600">
                        {b.start_time ? new Date(b.start_time).toLocaleString() : "-"}
                      </td>
                      <td className="py-3.5 text-xs text-gray-600">
                        {b.end_time ? new Date(b.end_time).toLocaleString() : "-"}
                      </td>
                      <td className="py-3.5">
                        <span className={`px-2.5 py-1 rounded-full text-xs font-semibold border ${getStatusBadge(b.status)}`}>
                          {b.status}
                        </span>
                      </td>
                      <td className="py-3.5 text-right">
                        {!isAdmin && (b.status === "confirmed" || b.status === "pending") ? (
                          <button
                            onClick={() => handleCancel(b.id)}
                            className="text-red-600 hover:text-red-700 hover:underline text-xs font-semibold"
                          >
                            Cancel
                          </button>
                        ) : isAdmin ? (
                          <select
                            value={b.status}
                            onChange={(e) => handleStatus(b.id, e.target.value)}
                            className="text-xs border border-gray-300 rounded-lg px-2 py-1 bg-white focus:ring-1 focus:ring-blue-500 outline-none"
                          >
                            <option value="confirmed">confirmed</option>
                            <option value="active">active</option>
                            <option value="completed">completed</option>
                            <option value="cancelled">cancelled</option>
                          </select>
                        ) : (
                          <span className="text-xs text-gray-400 capitalize">{b.status}</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* New Booking Modal */}
      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm transition-opacity" onClick={() => setOpen(false)} />
          <div className="relative z-10 bg-white rounded-2xl shadow-2xl w-full max-w-lg border border-gray-100 p-6 space-y-4">
            <div className="flex items-center justify-between border-b pb-3 border-gray-100">
              <div className="flex items-center gap-2">
                <div className="p-2 bg-blue-50 text-blue-600 rounded-xl">
                  <Calendar className="h-5 w-5" />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-gray-900">Reserve Charging Port</h2>
                  <p className="text-xs text-gray-400">Guaranteed slot conflict prevention (Business Logic A)</p>
                </div>
              </div>
              <button onClick={() => setOpen(false)} className="text-gray-400 hover:text-gray-600 p-1 rounded-lg">
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Select Your Vehicle *</label>
                {evs.length === 0 ? (
                  <div className="p-3 bg-amber-50 rounded-xl text-xs text-amber-800 border border-amber-200">
                    No vehicles found. Please register an electric vehicle first under the "My EVs" menu.
                  </div>
                ) : (
                  <select
                    required
                    className="w-full border border-gray-300 rounded-xl px-3 py-2 text-sm bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                    value={form.ev_id}
                    onChange={(e) => setForm({ ...form, ev_id: e.target.value })}
                  >
                    <option value="">-- Choose vehicle --</option>
                    {evs.map((e) => (
                      <option key={e.id} value={e.id}>
                        {e.model} ({e.registration_number || (e as any).vehicle_number})
                      </option>
                    ))}
                  </select>
                )}
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Charging Station *</label>
                <select
                  required
                  className="w-full border border-gray-300 rounded-xl px-3 py-2 text-sm bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                  value={form.station_id}
                  onChange={(e) => handleStationChange(e.target.value)}
                >
                  <option value="">-- Choose station --</option>
                  {stations.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name} ({s.station_code}) - {s.city}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Charging Port *</label>
                <select
                  required
                  className="w-full border border-gray-300 rounded-xl px-3 py-2 text-sm bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                  value={form.port_id}
                  onChange={(e) => setForm({ ...form, port_id: e.target.value })}
                >
                  <option value="">-- Choose port --</option>
                  {availablePortsForStation.map((p) => (
                    <option key={p.id} value={p.id}>
                      Port {p.port_number} · {p.connector_type} · {p.rated_power_kw} kW ({p.status})
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-1">Start Time *</label>
                  <input
                    type="datetime-local"
                    required
                    className="w-full border border-gray-300 rounded-xl px-3 py-2 text-xs focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                    value={form.start_time}
                    onChange={(e) => setForm({ ...form, start_time: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-1">End Time *</label>
                  <input
                    type="datetime-local"
                    required
                    className="w-full border border-gray-300 rounded-xl px-3 py-2 text-xs focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                    value={form.end_time}
                    onChange={(e) => setForm({ ...form, end_time: e.target.value })}
                  />
                </div>
              </div>

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
                  disabled={submitting || evs.length === 0}
                  className="bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white px-5 py-2 rounded-xl text-sm font-medium flex items-center gap-2 shadow-sm transition disabled:opacity-60"
                >
                  {submitting ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" /> Reserving...
                    </>
                  ) : (
                    "Confirm Booking"
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
