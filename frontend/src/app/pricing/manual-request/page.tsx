"use client"

import React, { useState } from "react";
import { apiClient, API_BASE_URL } from "../../../lib/api-client";

export default function ManualRequestPage() {
  const [file, setFile] = useState<File | null>(null);
  const [tier, setTier] = useState("pro");
  const [notes, setNotes] = useState("");
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (loading) {
      return;
    }

    if (!file) {
      setStatus("Please choose a proof file before submitting.");
      return;
    }

    setLoading(true);
    setStatus("Generating upload URL...");

    try {
      const presign = await apiClient.post<any>("/billing/manual/presign", {
        filename: file.name,
        content_type: file.type || "application/octet-stream",
      });

      let key = presign.key;

      if (presign.method === "put") {
        setStatus("Uploading file to storage...");
        const putResp = await fetch(presign.upload_url, {
          method: "PUT",
          headers: { "Content-Type": file.type || "application/octet-stream" },
          body: file,
        });
        if (!putResp.ok) throw new Error("Upload failed");
      } else if (presign.method === "backend") {
        // Fallback: upload via backend multiparty endpoint
        setStatus("Uploading file through backend...");
        const fd = new FormData();
        fd.append("file", file);
        const uploadResp = await fetch(`${API_BASE_URL}/uploads`, {
          method: "POST",
          body: fd,
          credentials: "include",
        });
        if (!uploadResp.ok) throw new Error("Backend upload failed");
        const json = await uploadResp.json();
        key = json.key || json.filename || key;
      }

      setStatus("Submitting manual activation request...");

      const req = await apiClient.post<any>("/billing/manual/request", {
        requested_tier: tier,
        proof_key: key,
        notes,
      });

      setStatus(req?.status === "success" ? "Request submitted successfully" : "Request failed");
    } catch (err: any) {
      setStatus("Error: " + (err?.message || String(err)));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{maxWidth: 720, margin: '0 auto', padding: 20}}>
      <h2>Request Manual Activation</h2>
      <p>If payments are unavailable, upload proof and request approval.</p>
      <form onSubmit={handleSubmit}>
        <div style={{marginBottom: 12}}>
          <label>Proof file</label><br />
          <input type="file" accept="image/*,application/pdf" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
        </div>
        <div style={{marginBottom: 12}}>
          <label>Requested Tier</label><br />
          <select value={tier} onChange={(e) => setTier(e.target.value)}>
            <option value="pro">Pro</option>
            <option value="elite">Elite</option>
          </select>
        </div>
        <div style={{marginBottom: 12}}>
          <label>Notes</label><br />
          <textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={4} style={{width: '100%'}} />
        </div>
        <div>
          <button type="submit" disabled={loading || !file}>
            {loading ? "Submitting..." : "Submit Request"}
          </button>
        </div>
      </form>
      <div style={{marginTop: 12}}>
        <strong>Status:</strong> {status}
      </div>
    </div>
  );
}
