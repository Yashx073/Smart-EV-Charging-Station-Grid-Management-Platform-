import { useEffect, useState } from "react";
import API from "@/services/api";
import type { Session, Port, EV } from "@/types";
import { PlugZap, Battery, Trash2, RefreshCw, AlertCircle, CheckCircle2, Loader2, X, Play, Square, Check, Info } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/hooks/useAuth";

export default function SessionsPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";

  const [items, setItems] = useState<Session[]>([]);
  const [ports, setPorts] = useState<Port[]>([]);
  const [evs, setEvs] = useState<EV[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // Start modal
  const [startOpen, setStartOpen] = useState(false);
  const [startForm, setStartForm] = useState({
    port_id: "",
    ev_id: "",
  });

  // End modal
  const [endOpen, setEndOpen] = useState(false);
  const [endSessionItem, setEndSessionItem] = useState<Session | null>(null);
  const [energyDelivered, setEnergyDelivered] = useState(20.0);

  const loadData = async () => {
    setLoading(true);
    setError("");
    try {
      const [sRes, pRes, eRes] = await Promise.all([
        API.get<{ items: Session[] }>("/sessions"),
        API.get<{ items: Port[] }>("/ports"),
        API.get<{ items: EV[] }>("/evs"),
      ]);

      const sess = sRes.data.items || [];
      setItems(isAdmin ? sess : sess.filter((s) => s.user_id === user?.id || (s as any).owner_id === user?.id));
      setPorts(pRes.data.items || []);
      setEvs(eRes.data.items || []);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load charging sessions");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [isAdmin, user?.id]);

  const handleOpenStart = () => {
    const operationalPorts = ports.filter((p) => p.status === "operational");
    const defaultPort = operationalPorts.length > 0 ? operationalPorts[0].id : "";
    const defaultEv = evs.length > 0 ? evs[0].id : "";
    setStartForm({
      port_id: defaultPort,
      ev_id: defaultEv,
    });
    setError("");
    setSuccess("");
    setStartOpen(true);
  };

  const handleStartSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!startForm.port_id) {
      setError("Please select an operational charging port.");
      return;
    }
    setError("");
    setSuccess("");
    setSubmitting(true);

    try {
      await API.post("/sessions/start", {
        port_id: startForm.port_id,
        ev_id: startForm.ev_id || undefined,
      });
      setSuccess("Charging session successfully started!");
      setStartOpen(false);
      loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to start charging session. The port may already be busy.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleOpenEnd = (session: Session) => {
    setEndSessionItem(session);
    setEnergyDelivered(20.0);
    setError("");
    setSuccess("");
    setEndOpen(true);
  };

  const handleEndSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!endSessionItem) return;
    if (energyDelivered <= 0) {
      setError("Delivered energy must be greater than 0 kWh.");
      return;
    }

    setError("");
    setSuccess("");
    setSubmitting(true);

    try {
      await API.post(`/sessions/${endSessionItem.id}/end`, {
        energy_delivered_kwh: Number(energyDelivered),
        energy_consumed: Number(energyDelivered),
      });
      setSuccess(`Session finalized! Billing calculation applied (${energyDelivered} kWh metered).`);
      setEndOpen(false);
      setEndSessionItem(null);
      loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to complete charging session.");
    } finally {
      setSubmitting(false);
    }
  };

  const getPortLabel = (ptId?: string) => {
    if (!ptId) return "Unknown Port";
    const found = ports.find((p) => p.id === ptId || (p as any)._id === ptId);
    return found ? `Port ${found.port_number} (${found.connector_type})` : `Port #${String(ptId).slice(-6)}`;
  };

  const getEVLabel = (evId?: string | null) => {
    if (!evId) return "-";
    const found = evs.find((e) => e.id === evId || (e as any)._id === evId);
    return found ? `${found.model} (${found.registration_number || (found as any).vehicle_number})` : `EV #${String(evId).slice(-6)}`;
  };

  const activeSessions = items.filter((s) => s.status === "active");
  const pastSessions = items.filter((s) => s.status !== "active");

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900">Charging Sessions</h1>
          <p className="text-sm text-gray-500">Live energy dispensing telemetry and metered session billing</p>
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
              onClick={handleOpenStart}
              className="bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white px-4 py-2 rounded-xl text-sm font-medium flex items-center gap-2 shadow-sm transition"
            >
              <PlugZap className="h-4 w-4" /> Start Session
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

      {/* Active Sessions Card */}
      <Card className="shadow-sm border-blue-100">
        <CardHeader className="pb-3 border-b border-gray-100 flex flex-row items-center justify-between bg-blue-50/40">
          <CardTitle className="text-base font-semibold text-gray-900 flex items-center gap-2">
            <span className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
            </span>
            Active Charging Sessions ({activeSessions.length})
          </CardTitle>
          {!isAdmin && activeSessions.length === 0 && (
            <button onClick={handleOpenStart} className="text-xs text-blue-600 font-semibold hover:underline">
              Plug in and start
            </button>
          )}
        </CardHeader>
        <CardContent className="pt-4">
          {loading ? (
            <div className="h-28 flex items-center justify-center text-gray-400">Checking active sessions...</div>
          ) : activeSessions.length === 0 ? (
            <div className="text-center py-8 text-gray-400 text-sm">
              <PlugZap className="h-10 w-10 text-gray-300 mx-auto mb-2" />
              No active charging sessions right now.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead>
                  <tr className="border-b border-gray-100 text-gray-400 text-xs font-semibold uppercase tracking-wider">
                    <th className="pb-3">Dispensing Port</th>
                    <th className="pb-3">Vehicle</th>
                    <th className="pb-3">Started At</th>
                    <th className="pb-3">Status</th>
                    <th className="pb-3 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {activeSessions.map((s) => (
                    <tr key={s.id} className="hover:bg-gray-50/70 transition">
                      <td className="py-3.5 font-medium text-gray-900">{getPortLabel(s.port_id)}</td>
                      <td className="py-3.5 text-gray-700">{getEVLabel(s.ev_id)}</td>
                      <td className="py-3.5 text-xs text-gray-600">
                        {s.started_at ? new Date(s.started_at).toLocaleTimeString() : "Just now"}
                      </td>
                      <td className="py-3.5">
                        <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                          Charging
                        </span>
                      </td>
                      <td className="py-3.5 text-right">
                        {!isAdmin ? (
                          <button
                            onClick={() => handleOpenEnd(s)}
                            className="bg-red-600 hover:bg-red-700 text-white text-xs font-medium px-3 py-1.5 rounded-lg flex items-center gap-1.5 ml-auto transition shadow-sm"
                          >
                            <Square className="h-3.5 w-3.5" /> Stop & Bill
                          </button>
                        ) : (
                          <span className="text-xs text-gray-400">Supervised</span>
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

      {/* Completed / Historical Sessions */}
      <Card className="shadow-sm">
        <CardHeader className="pb-3 border-b border-gray-100 flex flex-row items-center justify-between">
          <CardTitle className="text-base font-semibold text-gray-900 flex items-center gap-2">
            <Check className="h-5 w-5 text-purple-600" /> Completed Charging History ({pastSessions.length})
          </CardTitle>
          <span className="text-xs text-gray-400">Business Logic B: Rate × Energy Calculation</span>
        </CardHeader>
        <CardContent className="pt-4">
          {loading ? (
            <div className="h-32 flex items-center justify-center text-gray-400">Loading history...</div>
          ) : pastSessions.length === 0 ? (
            <div className="text-center py-8 text-gray-400 text-sm">No completed session records.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead>
                  <tr className="border-b border-gray-100 text-gray-400 text-xs font-semibold uppercase tracking-wider">
                    <th className="pb-3">Port</th>
                    <th className="pb-3">Vehicle</th>
                    <th className="pb-3">Delivered</th>
                    <th className="pb-3">Rate</th>
                    <th className="pb-3">Billed Amount</th>
                    <th className="pb-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {pastSessions.map((s) => (
                    <tr key={s.id} className="hover:bg-gray-50/70 transition">
                      <td className="py-3.5 font-medium text-gray-900">{getPortLabel(s.port_id)}</td>
                      <td className="py-3.5 text-gray-600">{getEVLabel(s.ev_id)}</td>
                      <td className="py-3.5 text-gray-800 font-semibold">
                        {s.energy_delivered_kwh ?? (s as any).energy_consumed_kwh ?? "-"} kWh
                      </td>
                      <td className="py-3.5 text-xs text-gray-500">
                        {s.tariff_price_per_kwh != null ? `₹${s.tariff_price_per_kwh}/kWh` : "Standard"}
                      </td>
                      <td className="py-3.5 font-bold text-gray-900">
                        {s.total_amount != null ? (
                          <span className="bg-purple-50 text-purple-700 px-2.5 py-1 rounded-md border border-purple-200">
                            ₹{s.total_amount.toFixed(2)}
                          </span>
                        ) : (
                          "-"
                        )}
                      </td>
                      <td className="py-3.5">
                        <span className="px-2.5 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-700 border border-gray-200 capitalize">
                          {s.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Start Session Modal */}
      {startOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm transition-opacity" onClick={() => setStartOpen(false)} />
          <div className="relative z-10 bg-white rounded-2xl shadow-2xl w-full max-w-md border border-gray-100 p-6 space-y-4">
            <div className="flex items-center justify-between border-b pb-3 border-gray-100">
              <div className="flex items-center gap-2">
                <div className="p-2 bg-blue-50 text-blue-600 rounded-xl">
                  <PlugZap className="h-5 w-5" />
                </div>
                <h2 className="text-lg font-bold text-gray-900">Start Charging Session</h2>
              </div>
              <button onClick={() => setStartOpen(false)} className="text-gray-400 hover:text-gray-600 p-1 rounded-lg">
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleStartSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Select Available Port *</label>
                <select
                  required
                  className="w-full border border-gray-300 rounded-xl px-3 py-2 text-sm bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                  value={startForm.port_id}
                  onChange={(e) => setStartForm({ ...startForm, port_id: e.target.value })}
                >
                  <option value="">-- Choose port --</option>
                  {ports
                    .filter((p) => p.status === "operational")
                    .map((p) => (
                      <option key={p.id} value={p.id}>
                        Port {p.port_number} · {p.connector_type} · {p.rated_power_kw} kW
                      </option>
                    ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Select Vehicle (Optional)</label>
                <select
                  className="w-full border border-gray-300 rounded-xl px-3 py-2 text-sm bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                  value={startForm.ev_id}
                  onChange={(e) => setStartForm({ ...startForm, ev_id: e.target.value })}
                >
                  <option value="">-- No vehicle selected --</option>
                  {evs.map((e) => (
                    <option key={e.id} value={e.id}>
                      {e.model} ({e.registration_number || (e as any).vehicle_number})
                    </option>
                  ))}
                </select>
              </div>

              <div className="p-3 bg-blue-50 rounded-xl text-xs text-blue-800 flex items-start gap-2">
                <Info className="h-4 w-4 shrink-0 mt-0.5 text-blue-600" />
                <span>Active tariff rates will be locked when session starts and calculated upon stopping.</span>
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-gray-100">
                <button
                  type="button"
                  onClick={() => setStartOpen(false)}
                  className="px-4 py-2 rounded-xl text-sm font-medium text-gray-600 hover:bg-gray-100 transition"
                  disabled={submitting}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting || !startForm.port_id}
                  className="bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white px-5 py-2 rounded-xl text-sm font-medium flex items-center gap-2 shadow-sm transition disabled:opacity-60"
                >
                  {submitting ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" /> Starting...
                    </>
                  ) : (
                    "Begin Charging"
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* End Session & Billing Modal */}
      {endOpen && endSessionItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm transition-opacity" onClick={() => setEndOpen(false)} />
          <div className="relative z-10 bg-white rounded-2xl shadow-2xl w-full max-w-md border border-gray-100 p-6 space-y-4">
            <div className="flex items-center justify-between border-b pb-3 border-gray-100">
              <div className="flex items-center gap-2">
                <div className="p-2 bg-purple-50 text-purple-600 rounded-xl">
                  <Square className="h-5 w-5 text-purple-600" />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-gray-900">Stop & Bill Session</h2>
                  <p className="text-xs text-gray-400">Business Logic B — Metered calculation</p>
                </div>
              </div>
              <button onClick={() => setEndOpen(false)} className="text-gray-400 hover:text-gray-600 p-1 rounded-lg">
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleEndSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  Metered Energy Delivered (kWh) *
                </label>
                <input
                  type="number"
                  step="0.1"
                  min="0.1"
                  required
                  className="w-full border border-gray-300 rounded-xl px-3 py-2 text-sm focus:ring-2 focus:ring-purple-500 focus:border-purple-500 outline-none"
                  value={energyDelivered}
                  onChange={(e) => setEnergyDelivered(Number(e.target.value))}
                />
              </div>

              {/* Billing Preview */}
              <div className="p-3 bg-purple-50 rounded-xl border border-purple-100 text-xs text-purple-900 space-y-1">
                <div className="flex justify-between font-medium">
                  <span>Unit Price Standard:</span>
                  <span>₹12.00 / kWh</span>
                </div>
                <div className="flex justify-between font-bold text-sm text-purple-950 pt-1 border-t border-purple-200">
                  <span>Estimated Total Amount:</span>
                  <span>₹{(energyDelivered * 12).toFixed(2)}</span>
                </div>
                <p className="text-[11px] text-purple-600 pt-1">
                  Formula: {energyDelivered} kWh × ₹12.00 = ₹{(energyDelivered * 12).toFixed(2)}
                </p>
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-gray-100">
                <button
                  type="button"
                  onClick={() => setEndOpen(false)}
                  className="px-4 py-2 rounded-xl text-sm font-medium text-gray-600 hover:bg-gray-100 transition"
                  disabled={submitting}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="bg-purple-600 hover:bg-purple-700 active:bg-purple-800 text-white px-5 py-2 rounded-xl text-sm font-medium flex items-center gap-2 shadow-sm transition disabled:opacity-60"
                >
                  {submitting ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" /> Finalizing...
                    </>
                  ) : (
                    "Complete & Generate Bill"
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
