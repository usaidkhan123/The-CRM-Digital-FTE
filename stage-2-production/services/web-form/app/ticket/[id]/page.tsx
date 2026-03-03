"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

export default function TicketStatusPage() {
  const params = useParams();
  const ticketId = params.id as string;
  const [ticket, setTicket] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchTicket() {
      try {
        const res = await fetch(`/api/support/ticket/${ticketId}`);
        if (!res.ok) throw new Error("Ticket not found");
        const data = await res.json();
        setTicket(data);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    fetchTicket();
  }, [ticketId]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="max-w-md p-6 bg-white rounded-lg shadow-md text-center">
          <h2 className="text-xl font-bold text-gray-900 mb-2">
            Ticket Not Found
          </h2>
          <p className="text-gray-600 mb-4">
            Ticket <span className="font-mono">{ticketId}</span> could not be
            found.
          </p>
          <a
            href="/"
            className="text-blue-600 hover:underline"
          >
            Submit a new request
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen py-12 px-4">
      <div className="max-w-2xl mx-auto bg-white rounded-lg shadow-md p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">
          Ticket Status
        </h1>

        <div className="space-y-4">
          <div className="flex justify-between items-center p-4 bg-gray-50 rounded-lg">
            <span className="text-sm text-gray-500">Ticket Number</span>
            <span className="font-mono font-bold">
              {ticket.ticket_number || ticketId}
            </span>
          </div>

          <div className="flex justify-between items-center p-4 bg-gray-50 rounded-lg">
            <span className="text-sm text-gray-500">Status</span>
            <span
              className={`px-3 py-1 rounded-full text-sm font-medium ${
                ticket.status === "open"
                  ? "bg-yellow-100 text-yellow-800"
                  : ticket.status === "closed"
                  ? "bg-green-100 text-green-800"
                  : "bg-blue-100 text-blue-800"
              }`}
            >
              {ticket.status}
            </span>
          </div>

          <div className="flex justify-between items-center p-4 bg-gray-50 rounded-lg">
            <span className="text-sm text-gray-500">Priority</span>
            <span className="font-medium">{ticket.priority}</span>
          </div>

          <div className="p-4 bg-gray-50 rounded-lg">
            <span className="text-sm text-gray-500 block mb-2">Issue</span>
            <p className="text-gray-900">{ticket.issue}</p>
          </div>

          <div className="flex justify-between items-center p-4 bg-gray-50 rounded-lg">
            <span className="text-sm text-gray-500">Created</span>
            <span className="text-gray-900">
              {new Date(ticket.created_at).toLocaleString()}
            </span>
          </div>
        </div>

        <div className="mt-6 text-center">
          <a
            href="/"
            className="text-blue-600 hover:underline"
          >
            Submit another request
          </a>
        </div>
      </div>
    </div>
  );
}
