import { useEffect, useState } from "react";
import API from "@/services/api";
import type { BatteryStatus, EV } from "@/types";
import { BatteryCharging, Battery, Thermometer, RefreshCw, Edit2, Plus, AlertCircle, CheckCircle2, Loader2, X, Activity } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/hooks/useAuth";

export default function BatteryStatusPage() {
  const [items, setItems] = useState<BatteryStatus[]>([]);
  const [evs, setEvs] = useState<EV[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [openModal, setOpenModal] = useState(false);
  const [isNewRecord, setIsNewRecord] = useState(false);
  const [editingItem, setEditingItem] = useState<BatteryStatus | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const [formData, setFormData] = useState({
    ev_id: "",
    current_level: 80,
    charging_level: 80,
    health_status: "Good",
    temperature_c: 28.5,
  });

  const { user } = useAuth();
  const isAdmin = user?.role === "admin";

  const loadData = async () => {
    setLoading(true);
    setError("");
    try {
      const [bRes, evRes] = await Promise.all([
        API.get<{ items: BatteryStatus[] }>("/battery-status"),
        API.get<{ items: EV[] }>("/evs"),
      ]);
      setItems(bRes.data.items || []);
      setEvs(evRes.data.items || []);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load EV battery status");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleOpenAddModal = (defaultEvId?: string) => {
    setIsNewRecord(true);
    setEditingItem(null);
    setFormData({
      ev_id: defaultEvId || (evs.length > 0 ? evs[0].id : ""),
      current_level: 80,
      charging_level: 80,
      health_status: "Good",
      temperature_c: 28.5,
    });
    setError("");
    setSuccess("");
    setOpenModal(true);
  };

  const handleOpenEditModal = (item: BatteryStatus) => {
    setIsNewRecord(false);
    setEditingItem(item);
    setFormData({
      ev_id: item.ev_id,
      current_level: item.current_level ?? item.battery_percentage ?? 80,
      charging_level: item.charging_level ?? item.current_level ?? 80,
      health_status: item.health_status || "Good",
      temperature_c: item.temperature_c ?? 28.5,
    });
    setError("");
    setSuccess("");
    setOpenModal(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.ev_id) {
      setError("Please select an EV.");
      return;
    }
    setError("");
    setSuccess("");
    setSubmitting(true);

    try {
      if (isNewRecord) {
        await API.post("/battery-status", {
          ev_id: formData.ev_id,
          current_level: Number(formData.current_level),
          battery_percentage: Number(formData.current_level),
          charging_level: Number(formData.charging_level),
          health_status: formData.health_status,
          temperature_c: Number(formData.temperature_c),
        });
        setSuccess("Battery telemetry record created successfully!");
      } else if (editingItem) {
        await API.put(`/battery-status/${editingItem.id}`, {
          current_level: Number(formData.current_level),
          battery_percentage: Number(formData.current_level),
          charging_level: Number(formData.charging_level),
          health_status: formData.health_status,
          temperature_c: Number(formData.temperature_c),
        });
        setSuccess("Battery telemetry updated successfully!");
      }
      setOpenModal(false);
      setEditingItem(null);
      loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to save battery telemetry");
    } finally {
      setSubmitting(false);
    }
  };

  const getEVInfo = (evId: string) => {
    const found = evs.find((e) => e.id === evId || (e as any)._id === evId || String(e.ev_id) === evId);
    return found ? `${found.manufacturer || found.brand || found.model} (${found.registration_number || (found as any).vehicle_number})` : `EV #${String(evId).slice(-6)}`;
  };

  const getHealthBadge = (health?: string) => {
    const h = health?.toUpperCase();
    if (h === "GOOD" || h === "EXCELLENT") {
      return "bg-emerald-50 text-emerald-700 border-emerald-200";
    }
    if (h === "FAIR") {
      return "bg-amber-50 text-amber-700 border-amber-200";
    }
    return "bg-red-50 text-red-700 border-red-200";
  };

  // Find EVs that don't have a telemetry record yet
  const evsWithoutTelemetry = evs.filter((e) => !items.some((b) => b.ev_id === e.id || b.ev_id === (e as any)._id));

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900">EV Battery Telemetry</h1>
          <p className="text-sm text-gray-500">Live battery state of charge (SoC), health status, and thermal monitoring</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={loadData}
            className="flex items-center gap-2 border border-gray-300 bg-white hover:bg-gray-50 text-gray-700 px-3 py-2 rounded-xl text-sm font-medium transition shadow-sm"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} /> Refresh
          </button>
          <button
            onClick={() => handleOpenAddModal()}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-3.5 py-2 rounded-xl text-sm font-medium transition shadow-sm"
          >
            <Plus className="h-4 w-4" /> Add Telemetry
          </button>
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

      {/* Untracked EVs prompt */}
      {evsWithoutTelemetry.length > 0 && !loading && (
        <div className="p-4 rounded-xl bg-blue-50 border border-blue-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-sm text-blue-900">
            <Activity className="h-5 w-5 text-blue-600 shrink-0" />
            <span>
              You have <strong>{evsWithoutTelemetry.length}</strong> vehicle(s) without telemetry initialized.
            </span>
          </div>
          <button
            onClick={() => handleOpenAddModal(evsWithoutTelemetry[0].id)}
            className="bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold px-3 py-1.5 rounded-lg transition"
          >
            Initialize for {evsWithoutTelemetry[0].model}
          </button>
        </div>
      )}

      {/* Telemetry Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {items.map((b) => {
          const pct = Math.min(100, Math.max(0, b.current_level != null ? b.current_level : b.battery_percentage || 0));
          return (
            <Card key={b.id} className="shadow-sm hover:shadow-md transition border-gray-200/80 rounded-2xl overflow-hidden">
              <CardHeader className="pb-3 border-b border-gray-100 flex flex-row items-center justify-between bg-gray-50/50">
                <div>
                  <CardTitle className="text-sm font-bold text-gray-900">{getEVInfo(b.ev_id)}</CardTitle>
                  <p className="text-xs text-gray-400 mt-0.5">
                    Last updated: {b.last_updated ? new Date(b.last_updated).toLocaleString() : "Real-time"}
                  </p>
                </div>
                <button
                  onClick={() => handleOpenEditModal(b)}
                  className="p-1.5 rounded-lg text-gray-400 hover:text-blue-600 hover:bg-blue-50 transition"
                  title="Update telemetry"
                >
                  <Edit2 className="h-4 w-4" />
                </button>
              </CardHeader>

              <CardContent className="pt-4 space-y-4">
                {/* State of Charge Bar */}
                <div>
                  <div className="flex justify-between items-center text-xs font-semibold mb-1.5">
                    <span className="text-gray-600 flex items-center gap-1.5">
                      <BatteryCharging className="h-4 w-4 text-emerald-600" /> State of Charge
                    </span>
                    <span className="text-gray-900 font-bold text-sm">{pct}%</span>
                  </div>
                  <div className="w-full bg-gray-100 rounded-full h-3 overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        pct > 60 ? "bg-emerald-500" : pct > 20 ? "bg-amber-500" : "bg-red-500"
                      }`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>

                {/* Metrics Details */}
                <div className="grid grid-cols-2 gap-3 pt-2 border-t border-gray-100 text-xs">
                  <div>
                    <span className="text-gray-400 block mb-0.5">Health State</span>
                    <span className={`px-2 py-0.5 rounded-md font-semibold border ${getHealthBadge(b.health_status)}`}>
                      {b.health_status || "Good"}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-400 block mb-0.5">Pack Temp</span>
                    <span className="font-semibold text-gray-700 flex items-center gap-1">
                      <Thermometer className="h-3.5 w-3.5 text-amber-500" />
                      {b.temperature_c != null ? `${b.temperature_c}°C` : "28.0°C"}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}

        {items.length === 0 && !loading && (
          <div className="col-span-full text-center py-12 bg-white rounded-2xl border border-gray-200">
            <Battery className="h-12 w-12 text-gray-300 mx-auto mb-3" />
            <h3 className="text-base font-semibold text-gray-800">No battery telemetry records found</h3>
            <p className="text-xs text-gray-500 mt-1 mb-4">
              {evs.length > 0
                ? "Click below to initialize live telemetry for your registered electric vehicles."
                : "Register an electric vehicle first to begin tracking battery telemetry."}
            </p>
            {evs.length > 0 && (
              <button
                onClick={() => handleOpenAddModal()}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-xl text-sm font-medium inline-flex items-center gap-2"
              >
                <Plus className="h-4 w-4" /> Add Initial Telemetry
              </button>
            )}
          </div>
        )}
      </div>

      {/* Add / Edit Telemetry Modal */}
      {openModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm transition-opacity" onClick={() => setOpenModal(false)} />
          <div className="relative z-10 bg-white rounded-2xl shadow-2xl w-full max-w-md border border-gray-100 p-6 space-y-4">
            <div className="flex items-center justify-between border-b pb-3 border-gray-100">
              <h2 className="text-lg font-bold text-gray-900">
                {isNewRecord ? "Record Battery Telemetry" : "Update Battery Telemetry"}
              </h2>
              <button onClick={() => setOpenModal(false)} className="text-gray-400 hover:text-gray-600 p-1 rounded-lg">
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              {isNewRecord && (
                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-1">Select Electric Vehicle *</label>
                  <select
                    required
                    className="w-full border border-gray-300 rounded-xl px-3 py-2 text-sm bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                    value={formData.ev_id}
                    onChange={(e) => setFormData({ ...formData, ev_id: e.target.value })}
                  >
                    <option value="">-- Choose vehicle --</option>
                    {evsWithoutTelemetry.map((e) => (
                      <option key={e.id} value={e.id}>
                        {e.model} ({e.registration_number || (e as any).vehicle_number})
                      </option>
                    ))}
                  </select>
                </div>
              )}

              <div>
                <div className="flex justify-between text-xs font-semibold text-gray-700 mb-1">
                  <span>Current Charge (SoC %)</span>
                  <span className="text-blue-600 font-bold">{formData.current_level}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                  value={formData.current_level}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      current_level: Number(e.target.value),
                      charging_level: Number(e.target.value),
                    })
                  }
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-1">Battery Health *</label>
                  <select
                    className="w-full border border-gray-300 rounded-xl px-3 py-2 text-sm bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                    value={formData.health_status}
                    onChange={(e) => setFormData({ ...formData, health_status: e.target.value })}
                  >
                    <option value="Good">Good</option>
                    <option value="Fair">Fair</option>
                    <option value="Degraded">Degraded</option>
                    <option value="Critical">Critical</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-1">Temperature (°C)</label>
                  <input
                    type="number"
                    step="0.5"
                    className="w-full border border-gray-300 rounded-xl px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                    value={formData.temperature_c}
                    onChange={(e) => setFormData({ ...formData, temperature_c: Number(e.target.value) })}
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-gray-100">
                <button
                  type="button"
                  onClick={() => setOpenModal(false)}
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
                    "Save Telemetry"
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
