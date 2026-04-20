"use client"

import React, { useState } from "react";
import { enhancedApiClient } from "../../../lib/api-client-enhanced";
import styles from "./page.module.css";

interface PresignResponse {
  key: string;
  method: "put" | "backend";
  upload_url: string;
}

interface ManualRequestResponse {
  status: string;
}

export default function ManualRequestPage() {
  const [file, setFile] = useState<File | null>(null);
  const [tier, setTier] = useState("pro");
  const [notes, setNotes] = useState("");
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
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
      const presign = await enhancedApiClient.post<PresignResponse>("/billing/manual/presign", {
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
        // Fallback: upload via backend multiparty endpoint using enhanced client upload helper
        setStatus("Uploading file through backend...");
        const fd = new FormData();
        fd.append("file", file);
        const uploadResp = await enhancedApiClient.upload<{ key?: string; filename?: string }>(
          '/uploads',
          fd
        );
        key = uploadResp?.key ?? uploadResp?.filename ?? key;
      }

      setStatus("Submitting manual activation request...");

      const req = await enhancedApiClient.post<ManualRequestResponse>("/billing/manual/request", {
        requested_tier: tier,
        proof_key: key,
        notes,
      });

      setStatus(req?.status === "success" ? "Request submitted successfully" : "Request failed");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      setStatus("Error: " + message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={styles.container}>
      <h2>Request Manual Activation</h2>
      <p>If payments are unavailable, upload proof and request approval.</p>
      <form className={styles.form} onSubmit={handleSubmit}>
        <div className={styles.field}>
          <label htmlFor="proofFile">Proof file</label>
          <input
            id="proofFile"
            className={styles.input}
            type="file"
            accept="image/*,application/pdf"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
        </div>

        <div className={styles.field}>
          <label htmlFor="requestedTier">Requested Tier</label>
          <select
            id="requestedTier"
            className={styles.input}
            value={tier}
            onChange={(e) => setTier(e.target.value)}
          >
            <option value="pro">Pro</option>
            <option value="elite">Elite</option>
          </select>
        </div>

        <div className={styles.field}>
          <label htmlFor="notes">Notes</label>
          <textarea
            id="notes"
            className={styles.textarea}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={4}
          />
        </div>

        <div className={styles.actionRow}>
          <button className={styles.button} type="submit" disabled={loading || !file}>
            {loading ? "Submitting..." : "Submit Request"}
          </button>
        </div>
      </form>

      <div className={styles.status}>
        <strong>Status:</strong> {status}
      </div>
    </div>
  );
}
