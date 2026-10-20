import { useEffect, useState } from "react";
import API from "@/services/api";
import type { Port, ACPort, DCFastPort, Station, Tariff } from "@/types";
import { Plus, Trash2, PlugZap, Zap, BatteryCharging, Edit2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/hooks/useAuth";

export default function PortsPage() {
  const [tab, setTab] = useState<"ports" | "ac" | "dc">("ports");
  const [ports, setPorts] = useState<Port[]>([]);
  const [acPorts, setAcPorts] = useState<ACPort[]>([]);
  const [dcPorts, setDcPorts] = useState<DCFastPort[]>([]);
  const [stations, setStations] = useState<Station[]>([]);
  const [tariffs, setTariffs] = useState<Tariff[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [openModal, setOpenModal] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    station_id: "",
    port_number: 1,
    charger_type: "DC_FAST",
    connector_type: "CCS",
    rated_power_kw: 50.0,
    status: "operational",
    tariff_id: "",
    // AC port subtype
    connector_standard: "TYPE_2",
    ac_phase: "SINGLE",
    ac_power_kw: 22.0,
    voltage: 230.0,
    current: 32.0,
    // DC port subtype
    dc_voltage: 400.0,
    maximum_current: 125.0,
    dc_power_kw: 50.0,
    supported_standard: "CCS2",
  });

  const { user } = useAuth();
  const isAdmin = user?.role === "admin";

  const loadData = async () => {
    setLoading(true);
    setError("");
    try {
      const [pRes, acRes, dcRes, stnRes, tfRes] = await Promise.all([
        API.get<{ items: Port[] }>("/ports"),
        API.get<{ items: ACPort[] }>("/ac-ports"),
        API.get<{ items: DCFastPort[] }>("/dc-fast-ports"),
        API.get<{ items: Station[] }>("/stations"),
        API.get<{ items: Tariff[] }>("/tariffs"),
      ]);
      setPorts(pRes.data.items);
      setAcPorts(acRes.data.items);
      setDcPorts(dcRes.data.items);
      setStations(stnRes.data.items);
      setTariffs(tfRes.data.items);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load port data");
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
      if (tab === "ports") {
        const payload = {
          station_id: formData.station_id || stations[0]?.id,
          port_number: Number(formData.port_number),
          charger_type: formData.charger_type,
          connector_type: formData.connector_type,
          rated_power_kw: Number(formData.rated_power_kw),
          power_output: Number(formData.rated_power_kw),
          status: formData.status,
          availability_status: formData.status === "operational" ? "AVAILABLE" : "MAINTENANCE",
          tariff_id: formData.tariff_id || undefined,
        };
        if (editingId) {
          await API.put(`/ports/${editingId}`, payload);
        } else {
          await API.post("/ports", payload);
        }
      } else if (tab === "ac") {
        const payload = {
          station_id: formData.station_id || stations[0]?.id,
          port_number: Number(formData.port_number),
          connector_standard: formData.connector_standard,
          ac_phase: formData.ac_phase,
          ac_power_kw: Number(formData.ac_power_kw),
          voltage: Number(formData.voltage),
          current: Number(formData.current),
        };
        if (editingId) {
          await API.put(`/ac-ports/${editingId}`, payload);
        } else {
          await API.post("/ac-ports", payload);
        }
      } else if (tab === "dc") {
        const payload = {
          station_id: formData.station_id || stations[0]?.id,
          port_number: Number(formData.port_number),
          dc_voltage: Number(formData.dc_voltage),
          maximum_current: Number(formData.maximum_current),
          dc_power_kw: Number(formData.dc_power_kw),
          supported_standard: formData.supported_standard,
        };
        if (editingId) {
          await API.put(`/dc-fast-ports/${editingId}`, payload);
        } else {
          await API.post("/dc-fast-ports", payload);
        }
      }
      setOpenModal(false);
      setEditingId(null);
      loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Save failed");
    }
  };

  const handleDelete = async (id: string, endpoint: "ports" | "ac-ports" | "dc-fast-ports") => {
    if (!confirm("Delete this port record?")) return;
    try {
      await API.delete(`/${endpoint}/${id}`);
      loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Delete failed");
    }
  };

  const getStationCode = (sid: string) => {
    const s = stations.find((st) => st.id === sid);
    return s ? `${s.name} (${s.station_code})` : sid;
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900">Charging Ports & Hardware</h1>
          <p className="text-sm text-gray-500">Manage charging ports, AC Level 2 configurations, and DC Fast charging hardware</p>
        </div>
        {isAdmin && (
          <button
            onClick={() => {
              setEditingId(null);
              setFormData({
                station_id: stations[0]?.id || "",
                port_number: (ports.length % 10) + 1,
                charger_type: tab === "ac" ? "AC" : "DC_FAST",
                connector_type: tab === "ac" ? "Type 2" : "CCS",
                rated_power_kw: tab === "ac" ? 22.0 : 150.0,
                status: "operational",
                tariff_id: tariffs[0]?.id || "",
                connector_standard: "TYPE_2",
                ac_phase: "SINGLE",
                ac_power_kw: 22.0,
                voltage: 230.0,
                current: 32.0,
                dc_voltage: 400.0,
                maximum_current: 125.0,
                dc_power_kw: 150.0,
                supported_standard: "CCS2",
              });
              setOpenModal(true);
            }}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition shadow-sm"
          >
            <Plus className="h-4 w-4" /> Add {tab === "ac" ? "AC Port Spec" : tab === "dc" ? "DC Fast Port Spec" : "Charging Port"}
          </button>
        )}
      </div>

      {error && <div className="p-4 rounded-lg bg-red-50 text-red-700 text-sm border border-red-200">{error}</div>}

      {/* Tabs */}
      <div className="flex border-b border-gray-200 gap-6">
        <button
          onClick={() => setTab("ports")}
          className={`pb-3 text-sm font-semibold border-b-2 flex items-center gap-2 transition ${
            tab === "ports" ? "border-blue-600 text-blue-600" : "border-transparent text-gray-500 hover:text-gray-700"
          }`}
        >
          <PlugZap className="h-4 w-4" /> Charging Ports (Entity 9) ({ports.length})
        </button>
        <button
          onClick={() => setTab("ac")}
          className={`pb-3 text-sm font-semibold border-b-2 flex items-center gap-2 transition ${
            tab === "ac" ? "border-green-600 text-green-600" : "border-transparent text-gray-500 hover:text-gray-700"
          }`}
        >
          <Zap className="h-4 w-4 text-green-600" /> AC Port Subtypes (Entity 10) ({acPorts.length})
        </button>
        <button
          onClick={() => setTab("dc")}
          className={`pb-3 text-sm font-semibold border-b-2 flex items-center gap-2 transition ${
            tab === "dc" ? "border-amber-600 text-amber-600" : "border-transparent text-gray-500 hover:text-gray-700"
          }`}
        >
          <BatteryCharging className="h-4 w-4 text-amber-600" /> DC Fast Subtypes (Entity 11) ({dcPorts.length})
        </button>
      </div>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base font-medium">
            {tab === "ports" && "Station Port Directory"}
            {tab === "ac" && "AC Port Electrical Specifications"}
            {tab === "dc" && "DC Fast Charging Electrical Specifications"}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="h-40 flex items-center justify-center text-gray-500">Loading ports...</div>
          ) : (
            <div className="overflow-x-auto">
              {tab === "ports" && (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b text-gray-500">
                      <th className="text-left pb-3 font-medium">Station</th>
                      <th className="text-left pb-3 font-medium">Port #</th>
                      <th className="text-left pb-3 font-medium">Hardware Class</th>
                      <th className="text-left pb-3 font-medium">Connector</th>
                      <th className="text-left pb-3 font-medium">Rated Power</th>
                      <th className="text-left pb-3 font-medium">Status</th>
                      {isAdmin && <th className="text-right pb-3 font-medium">Actions</th>}
                    </tr>
                  </thead>
                  <tbody>
                    {ports.map((p) => (
                      <tr key={p.id} className="border-b hover:bg-gray-50 transition">
                        <td className="py-3 font-medium text-gray-900">{p.station_code || getStationCode(p.station_id)}</td>
                        <td className="py-3 font-mono font-bold text-blue-600">Port {p.port_number}</td>
                        <td className="py-3">
                          <span className={`px-2 py-0.5 rounded text-xs font-semibold ${p.charger_type === "AC" ? "bg-green-100 text-green-800" : "bg-purple-100 text-purple-800"}`}>
                            {p.charger_type || (p.connector_type.includes("CCS") ? "DC_FAST" : "AC")}
                          </span>
                        </td>
                        <td className="py-3">{p.connector_type}</td>
                        <td className="py-3 font-mono">{p.rated_power_kw || p.power_output} kW</td>
                        <td className="py-3">
                          <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${p.status === "operational" ? "bg-emerald-100 text-emerald-800" : "bg-amber-100 text-amber-800"}`}>
                            {p.status}
                          </span>
                        </td>
                        {isAdmin && (
                          <td className="py-3 text-right space-x-2">
                            <button
                              onClick={() => {
                                setEditingId(p.id);
                                setFormData({
                                  ...formData,
                                  station_id: p.station_id,
                                  port_number: p.port_number,
                                  charger_type: p.charger_type || "DC_FAST",
                                  connector_type: p.connector_type,
                                  rated_power_kw: p.rated_power_kw,
                                  status: p.status,
                                  tariff_id: p.tariff_id || "",
                                });
                                setOpenModal(true);
                              }}
                              className="text-gray-500 hover:text-blue-600 p-1"
                            >
                              <Edit2 className="h-4 w-4" />
                            </button>
                            <button
                              onClick={() => handleDelete(p.id, "ports")}
                              className="text-gray-500 hover:text-red-600 p-1"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </td>
                        )}
                      </tr>
                    ))}
                    {ports.length === 0 && (
                      <tr>
                        <td colSpan={7} className="text-center py-6 text-gray-500">No charging ports found.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              )}

              {tab === "ac" && (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b text-gray-500">
                      <th className="text-left pb-3 font-medium">Station</th>
                      <th className="text-left pb-3 font-medium">Port #</th>
                      <th className="text-left pb-3 font-medium">Standard</th>
                      <th className="text-left pb-3 font-medium">AC Phase</th>
                      <th className="text-left pb-3 font-medium">Rated AC Power</th>
                      <th className="text-left pb-3 font-medium">Voltage / Current</th>
                      {isAdmin && <th className="text-right pb-3 font-medium">Actions</th>}
                    </tr>
                  </thead>
                  <tbody>
                    {acPorts.map((ac) => (
                      <tr key={ac.id} className="border-b hover:bg-gray-50 transition">
                        <td className="py-3 font-medium text-gray-900">{getStationCode(ac.station_id)}</td>
                        <td className="py-3 font-mono font-bold text-green-600">Port {ac.port_number}</td>
                        <td className="py-3">
                          <span className="px-2 py-0.5 rounded text-xs font-semibold bg-gray-100 text-gray-800">
                            {ac.connector_standard}
                          </span>
                        </td>
                        <td className="py-3 font-semibold text-gray-700">{ac.ac_phase} PHASE</td>
                        <td className="py-3 font-mono">{ac.ac_power_kw != null ? `${ac.ac_power_kw} kW` : "22 kW"}</td>
                        <td className="py-3 font-mono text-gray-600">
                          {ac.voltage || 230}V / {ac.current || 32}A
                        </td>
                        {isAdmin && (
                          <td className="py-3 text-right">
                            <button
                              onClick={() => handleDelete(ac.id, "ac-ports")}
                              className="text-gray-500 hover:text-red-600 p-1"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </td>
                        )}
                      </tr>
                    ))}
                    {acPorts.length === 0 && (
                      <tr>
                        <td colSpan={7} className="text-center py-6 text-gray-500">No AC port subtypes configured.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              )}

              {tab === "dc" && (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b text-gray-500">
                      <th className="text-left pb-3 font-medium">Station</th>
                      <th className="text-left pb-3 font-medium">Port #</th>
                      <th className="text-left pb-3 font-medium">Standard</th>
                      <th className="text-left pb-3 font-medium">DC Voltage</th>
                      <th className="text-left pb-3 font-medium">Max Current</th>
                      <th className="text-left pb-3 font-medium">DC Output Power</th>
                      {isAdmin && <th className="text-right pb-3 font-medium">Actions</th>}
                    </tr>
                  </thead>
                  <tbody>
                    {dcPorts.map((dc) => (
                      <tr key={dc.id} className="border-b hover:bg-gray-50 transition">
                        <td className="py-3 font-medium text-gray-900">{getStationCode(dc.station_id)}</td>
                        <td className="py-3 font-mono font-bold text-purple-600">Port {dc.port_number}</td>
                        <td className="py-3">
                          <span className="px-2 py-0.5 rounded text-xs font-semibold bg-purple-100 text-purple-800">
                            {dc.supported_standard || "CCS2"}
                          </span>
                        </td>
                        <td className="py-3 font-mono text-gray-800">{dc.dc_voltage} V</td>
                        <td className="py-3 font-mono text-gray-800">{dc.maximum_current} A</td>
                        <td className="py-3 font-mono font-bold text-gray-900">
                          {dc.dc_power_kw ? `${dc.dc_power_kw} kW` : `${Math.round((dc.dc_voltage * dc.maximum_current) / 1000)} kW`}
                        </td>
                        {isAdmin && (
                          <td className="py-3 text-right">
                            <button
                              onClick={() => handleDelete(dc.id, "dc-fast-ports")}
                              className="text-gray-500 hover:text-red-600 p-1"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </td>
                        )}
                      </tr>
                    ))}
                    {dcPorts.length === 0 && (
                      <tr>
                        <td colSpan={7} className="text-center py-6 text-gray-500">No DC Fast port subtypes configured.</td>
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
              {editingId ? "Edit Configuration" : `Add ${tab === "ac" ? "AC Port Subtype" : tab === "dc" ? "DC Fast Port Subtype" : "Charging Port"}`}
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
                <label className="text-xs font-medium text-gray-700">Port Number</label>
                <input
                  type="number"
                  min="1"
                  required
                  value={formData.port_number}
                  onChange={(e) => setFormData({ ...formData, port_number: Number(e.target.value) })}
                  className="w-full border rounded-lg p-2 text-sm mt-1 font-mono"
                />
              </div>

              {tab === "ports" && (
                <>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="text-xs font-medium text-gray-700">Charger Type</label>
                      <select
                        value={formData.charger_type}
                        onChange={(e) => setFormData({ ...formData, charger_type: e.target.value })}
                        className="w-full border rounded-lg p-2 text-sm mt-1"
                      >
                        <option value="DC_FAST">DC_FAST</option>
                        <option value="AC">AC</option>
                      </select>
                    </div>
                    <div>
                      <label className="text-xs font-medium text-gray-700">Connector</label>
                      <input
                        type="text"
                        required
                        value={formData.connector_type}
                        onChange={(e) => setFormData({ ...formData, connector_type: e.target.value })}
                        className="w-full border rounded-lg p-2 text-sm mt-1"
                        placeholder="CCS, Type 2, CHAdeMO"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="text-xs font-medium text-gray-700">Rated Power (kW)</label>
                    <input
                      type="number"
                      min="1"
                      required
                      value={formData.rated_power_kw}
                      onChange={(e) => setFormData({ ...formData, rated_power_kw: Number(e.target.value) })}
                      className="w-full border rounded-lg p-2 text-sm mt-1"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-medium text-gray-700">Applicable Tariff</label>
                    <select
                      value={formData.tariff_id}
                      onChange={(e) => setFormData({ ...formData, tariff_id: e.target.value })}
                      className="w-full border rounded-lg p-2 text-sm mt-1"
                    >
                      <option value="">Select tariff...</option>
                      {tariffs.map((t) => (
                        <option key={t.id} value={t.id}>
                          {t.name} (₹{t.price_per_kwh}/kWh)
                        </option>
                      ))}
                    </select>
                  </div>
                </>
              )}

              {tab === "ac" && (
                <>
                  <div>
                    <label className="text-xs font-medium text-gray-700">Connector Standard</label>
                    <input
                      type="text"
                      required
                      value={formData.connector_standard}
                      onChange={(e) => setFormData({ ...formData, connector_standard: e.target.value })}
                      className="w-full border rounded-lg p-2 text-sm mt-1"
                      placeholder="TYPE_2, TYPE_1"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="text-xs font-medium text-gray-700">AC Phase</label>
                      <select
                        value={formData.ac_phase}
                        onChange={(e) => setFormData({ ...formData, ac_phase: e.target.value })}
                        className="w-full border rounded-lg p-2 text-sm mt-1"
                      >
                        <option value="SINGLE">SINGLE</option>
                        <option value="THREE">THREE</option>
                      </select>
                    </div>
                    <div>
                      <label className="text-xs font-medium text-gray-700">AC Power (kW)</label>
                      <input
                        type="number"
                        min="1"
                        required
                        value={formData.ac_power_kw}
                        onChange={(e) => setFormData({ ...formData, ac_power_kw: Number(e.target.value) })}
                        className="w-full border rounded-lg p-2 text-sm mt-1"
                      />
                    </div>
                  </div>
                </>
              )}

              {tab === "dc" && (
                <>
                  <div>
                    <label className="text-xs font-medium text-gray-700">Supported Standard</label>
                    <input
                      type="text"
                      required
                      value={formData.supported_standard}
                      onChange={(e) => setFormData({ ...formData, supported_standard: e.target.value })}
                      className="w-full border rounded-lg p-2 text-sm mt-1"
                      placeholder="CCS2, CHAdeMO"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="text-xs font-medium text-gray-700">DC Voltage (V)</label>
                      <input
                        type="number"
                        min="1"
                        required
                        value={formData.dc_voltage}
                        onChange={(e) => setFormData({ ...formData, dc_voltage: Number(e.target.value) })}
                        className="w-full border rounded-lg p-2 text-sm mt-1"
                      />
                    </div>
                    <div>
                      <label className="text-xs font-medium text-gray-700">Maximum Current (A)</label>
                      <input
                        type="number"
                        min="1"
                        required
                        value={formData.maximum_current}
                        onChange={(e) => setFormData({ ...formData, maximum_current: Number(e.target.value) })}
                        className="w-full border rounded-lg p-2 text-sm mt-1"
                      />
                    </div>
                  </div>
                </>
              )}

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
