import { useEffect, useState } from "react";
import API from "@/services/api";
import type { Payment } from "@/types";
import { CreditCard } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/hooks/useAuth";

export default function PaymentsPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";
  const [items, setItems] = useState<Payment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    API.get<{ items: Payment[] }>("/payments")
      .then((r) => setItems(isAdmin ? r.data.items : r.data.items.filter((p) => p.user_id === user!.id)))
      .catch(() => setError("Failed to load payments"))
      .finally(() => setLoading(false));
  }, [isAdmin, user?.id]);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <CreditCard className="h-5 w-5" />
        <h1 className="text-2xl font-bold">Payments</h1>
      </div>
      {error && <div className="p-3 rounded bg-red-50 text-red-700 text-sm border border-red-100">{error}</div>}
      <Card>
        <CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Payment history</CardTitle></CardHeader>
        <CardContent>
          {loading ? (
            <div className="h-40 flex items-center justify-center">Loading...</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left pb-2 text-gray-500">Session</th>
                    <th className="text-left pb-2 text-gray-500">Amount (₹)</th>
                    <th className="text-left pb-2 text-gray-500">Method</th>
                    <th className="text-left pb-2 text-gray-500">Reference</th>
                    <th className="text-left pb-2 text-gray-500">Status</th>
                    <th className="text-left pb-2 text-gray-500">Date</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((p) => (
                    <tr key={p.id} className="border-b">
                      <td className="py-2 font-mono">{p.session_id.slice(-6)}</td>
                      <td className="py-2 font-medium">{p.amount}</td>
                      <td className="py-2">{p.payment_method}</td>
                      <td className="py-2 text-xs font-mono">{p.transaction_reference}</td>
                      <td className="py-2">{p.status}</td>
                      <td className="py-2 text-xs text-gray-500">{new Date(p.created_at).toLocaleString()}</td>
                    </tr>
                  ))}
                  {items.length === 0 && <tr><td colSpan={6} className="py-4 text-center text-gray-500">No payments</td></tr>}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
