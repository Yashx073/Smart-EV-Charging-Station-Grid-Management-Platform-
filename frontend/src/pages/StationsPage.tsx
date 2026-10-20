import { useEffect, useState } from "react";
import API from "@/services/api";
import type { Station } from "@/types";
import { Plus, Trash2, AlertTriangle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/hooks/useAuth";

export default function StationsPage() {
  const [items, setItems] = useState<Station[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({ name: "", station_code: "", address: "", city: "", latitude: "", longitude: "" });
  const { user } = useAuth();

  useEffect(() => {
    API.get<{ items: Station[] }>("/stations")
      .then((r) => setItems(r.data.items))
      .catch(() => setError("Failed to load stations"))
      .finally(() => setLoading(false));
  }, []);

  const isAdmin = user?.role === "admin";

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await API.post("/stations", { ...form, latitude: Number(form.latitude), longitude: Number(form.longitude) });
      setCreating(false);
      setForm({ name: "", station_code: "", address: "", city: "", latitude: "", longitude: "" });
      window.location.reload();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Create failed");
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this station?")) return;
    try {
      await API.delete(`/stations/${id}`);
      window.location.reload();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Delete failed");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <h1 className="text-2xl font-bold">Charging Stations</h1>
        {isAdmin && (
          <button
            onClick={() => setCreating(!creating)}
            className="bg-blue-600 text-white px-3 py-2 rounded-lg text-sm font-medium flex items-center gap-2 hover:bg-blue-700"
          >
            <Plus className="h-4 w-4" /> {creating ? "Cancel" : "Add Station"}
          </button>
        )}
      </div>
      {error && <div className="p-3 rounded bg-red-50 text-red-700 text-sm border border-red-100">{error}</div>}
      <Card>
        <CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Station list</CardTitle></CardHeader>
        <CardContent>
          {loading ? (
            <div className="h-40 flex items-center justify-center">Loading...</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left pb-2 text-gray-500">Name</th>
                    <th className="text-left pb-2 text-gray-500">Code</th>
                    <th className="text-left pb-2 text-gray-500">Address</th>
                    <th className="text-left pb-2 text-gray-500">City</th>
                    <th className="text-left pb-2 text-gray-500">Status</th>
                    {isAdmin && <th className="text-left pb-2 text-gray-500 w-20">Actions</th>}
                  </tr>
                </thead>
                <tbody>
                  {items.map((s) => (
                    <tr key={s.id} className="border-b">
                      <td className="py-2">{s.name}</td>
                      <td className="py-2 text-gray-500">{s.station_code}</td>
                      <td className="py-2">{s.address}</td>
                      <td className="py-2">{s.city}</td>
                      <td className="py-2">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          s.status === "operational" ? "bg-green-100 text-green-700" : "bg-amber-100 text-amber-700"
                        }`}>
                          {s.status}
                        </span>
                      </td>
                      {isAdmin && (
                        <td className="py-2">
                          <button onClick={() => handleDelete(s.id)} className="text-red-600 hover:underline text-sm">
                            <Trash2 className="h-4 w-4 mr-1 inline" /> Delete
                          </button>
                        </td>
                      )}
                    </tr>
                  ))}
                  {items.length === 0 && <tr><td colSpan={6} className="py-4 text-center text-gray-500">No stations</td></tr>}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
      {isAdmin && creating && (
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm font-medium">New station</CardTitle></CardHeader>
          <CardContent>
            <form onSubmit={handleCreate} className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex flex-col gap-1">
                <label className="text-xs font-medium text-gray-500">Name</label>
                <input className="border rounded-lg px-3 py-2" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-xs font-medium text-gray-500">Station code</label>
                <input className="border rounded-lg px-3 py-2" value={form.station_code} onChange={(e) => setForm({ ...form, station_code: e.target.value })} required />
              </div>
              <div className="flex flex-col gap-1 md:col-span-2">
                <label className="text-xs font-medium text-gray-500">Address</label>
                <input className="border rounded-lg px-3 py-2" value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} required />
              </div>
              <div className="flex flex-col gap-1 md:col-span-2">
                <label className="text-xs font-medium text-gray-500">City</label>
                <input className="border rounded-lg px-3 py-2" value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} required />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-xs font-medium text-gray-500">Latitude</label>
                <input className="border rounded-lg px-3 py-2" type="number" step="any" value={form.latitude} onChange={(e) => setForm({ ...form, latitude: e.target.value })} required />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-xs font-medium text-gray-500">Longitude</label>
                <input className="border rounded-lg px-3 py-2" type="number" step="any" value={form.longitude} onChange={(e) => setForm({ ...form, longitude: e.target.value })} required />
              </div>
              <button className="md:col-span-2 bg-blue-600 text-white px-4 py-2 rounded-lg font-medium">Create</button>
            </form>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
