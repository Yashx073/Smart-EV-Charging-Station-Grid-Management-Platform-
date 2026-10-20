import { useEffect, useState } from "react";
import API from "@/services/api";
import type { Tariff } from "@/types";
import { Plus, Trash2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { z } from "zod";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

const schema = z.object({
  name: z.string().min(1),
  price_per_kwh: z.coerce.number().positive(),
  valid_from: z.string().min(1),
  valid_to: z.string().optional(),
  is_active: z.boolean(),
});

export default function TariffsPage() {
  const [items, setItems] = useState<Tariff[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<string | null>(null);

  const form = useForm<z.infer<typeof schema>>({
    resolver: zodResolver(schema),
    defaultValues: { name: "", price_per_kwh: 0, valid_from: "", valid_to: "", is_active: true },
  });

  useEffect(() => {
    API.get<{ items: Tariff[] }>("/tariffs")
      .then((r) => setItems(r.data.items))
      .catch(() => setError("Failed to load tariffs"))
      .finally(() => setLoading(false));
  }, []);

  const handleSubmit = async (values: any) => {
    try {
      if (editing) {
        await API.put(`/tariffs/${editing}`, values);
      } else {
        await API.post("/tariffs", values);
      }
      setOpen(false);
      setEditing(null);
      form.reset();
      window.location.reload();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Save failed");
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this tariff?")) return;
    try {
      await API.delete(`/tariffs/${id}`);
      window.location.reload();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Delete failed");
    }
  };

  const handleToggle = async (id: string, isActive: boolean) => {
    try {
      await API.put(`/tariffs/${id}`, { is_active: !isActive });
      window.location.reload();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Update failed");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <h1 className="text-2xl font-bold">Tariffs</h1>
        <button
          onClick={() => { setEditing(null); form.reset(); setOpen(true); }}
          className="bg-blue-600 text-white px-3 py-2 rounded-lg text-sm font-medium flex items-center gap-2 hover:bg-blue-700"
        >
          <Plus className="h-4 w-4" /> Add Tariff
        </button>
      </div>
      {error && <div className="p-3 rounded bg-red-50 text-red-700 text-sm border border-red-100">{error}</div>}
      <Card>
        <CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Tariff list</CardTitle></CardHeader>
        <CardContent>
          {loading ? (
            <div className="h-40 flex items-center justify-center">Loading...</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left pb-2 text-gray-500">Name</th>
                    <th className="text-left pb-2 text-gray-500">Price (₹/kWh)</th>
                    <th className="text-left pb-2 text-gray-500">Valid from</th>
                    <th className="text-left pb-2 text-gray-500">Active</th>
                    <th className="text-left pb-2 text-gray-500 w-32">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((t) => (
                    <tr key={t.id} className="border-b">
                      <td className="py-2">{t.name}</td>
                      <td className="py-2">{t.price_per_kwh}</td>
                      <td className="py-2 text-sm">{new Date(t.valid_from).toLocaleDateString()}</td>
                      <td className="py-2">
                        <button onClick={() => handleToggle(t.id, t.is_active)} className={`px-2 py-1 rounded-full text-xs font-medium ${
                          t.is_active ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-700"
                        }`}>
                          {t.is_active ? "Active" : "Inactive"}
                        </button>
                      </td>
                      <td className="py-2">
                        <button onClick={() => { setEditing(t.id); form.setValue("name", t.name); form.setValue("price_per_kwh", t.price_per_kwh); form.setValue("valid_from", t.valid_from.slice(0,16)); form.setValue("valid_to", t.valid_to ?? ""); form.setValue("is_active", t.is_active); setOpen(true); }} className="text-blue-600 text-sm hover:underline mr-2">Edit</button>
                        <button onClick={() => handleDelete(t.id)} className="text-red-600 text-sm hover:underline"><Trash2 className="h-4 w-4 mr-1 inline" /></button>
                      </td>
                    </tr>
                  ))}
                  {items.length === 0 && <tr><td colSpan={5} className="py-4 text-center text-gray-500">No tariffs</td></tr>}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      <div className={`fixed inset-0 z-50 ${open ? "flex" : "hidden"} items-center justify-center`}>
        <div className="fixed inset-0 bg-black opacity-50" onClick={() => setOpen(false)} />
        <div className="bg-white p-6 rounded-xl shadow-lg w-full max-w-md border border-gray-200">
          <h2 className="mb-4 text-lg font-bold">{editing ? "Edit" : "New"} tariff</h2>
          <p className="text-xs text-gray-500 mb-4">Billing = energy (kWh) × tariff price.</p>
          <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
            <div className="flex flex-col gap-1">
              <label className="text-xs font-medium text-gray-500">Name</label>
              <input {...form.register("name")} className="border rounded-lg px-3 py-2" />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs font-medium text-gray-500">Price per kWh (₹)</label>
              <input {...form.register("price_per_kwh")} type="number" step="0.01" className="border rounded-lg px-3 py-2" />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs font-medium text-gray-500">Valid from</label>
              <input {...form.register("valid_from")} type="datetime-local" className="border rounded-lg px-3 py-2" />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs font-medium text-gray-500">Valid to (optional)</label>
              <input {...form.register("valid_to")} type="datetime-local" className="border rounded-lg px-3 py-2" />
            </div>
            <div className="flex items-center gap-2">
              <input {...form.register("is_active")} type="checkbox" className="rounded" />
              <label className="text-sm">Active</label>
            </div>
            <div className="flex gap-2">
              <button type="button" onClick={() => setOpen(false)} className="px-4 py-2 rounded-lg text-gray-700 hover:bg-gray-100">Cancel</button>
              <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded-lg font-medium">Save</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
