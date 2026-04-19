"use client";

import React, { useState } from "react";
import { addTeamMember } from "@/lib/api";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "react-hot-toast";
import { Team, TeamMemberFull } from "@/types/api";

export default function AddMemberModal({
  open,
  onClose,
  teamId,
}: {
  open: boolean;
  onClose: () => void;
  teamId: string;
}) {
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<"member" | "admin">("member");
  const [loading, setLoading] = useState(false);
  const qc = useQueryClient();

  if (!open) return null;

  const submit = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!email || !email.includes("@")) {
      toast.error("Please enter a valid email address");
      return;
    }

    setLoading(true);
    try {
      const result = await addTeamMember(teamId, { email, role });

      // Optimistically add member to teams cache if present
      qc.setQueryData<Team[] | undefined>(["teams"], (old = []) => {
        if (!old) return old;
        return old.map((t) => {
          if (String(t.id) !== String(teamId)) return t;
          const members = (t as any).members || [];
          const newMember = {
            id: result.id,
            user_id: result.user_id,
            email,
            role: result.role,
            joined_at: new Date().toISOString(),
          };
          return { ...t, members: [...members, newMember] } as Team;
        });
      });

      // Also update the per-team members cache so lists refresh immediately
      qc.setQueryData<TeamMemberFull[] | undefined>(["team-members", teamId], (old = []) => {
        const newMember = {
          id: result.id,
          user_id: result.user_id,
          email,
          role: result.role,
          is_active: true,
          joined_at: new Date().toISOString(),
        } as TeamMemberFull;
        return [...(old || []), newMember];
      });

      toast.success("Member added");
      setEmail("");
      setRole("member");
      onClose();
    } catch (err: any) {
      const msg = err?.message || String(err || "Failed to add member");
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={() => onClose()} />
      <div className="relative bg-white rounded-2xl shadow-xl w-full max-w-md p-6">
        <h3 className="text-lg font-semibold mb-3">Add Team Member</h3>
        <form onSubmit={submit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Email</label>
            <input
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              type="email"
              placeholder="name@example.com"
              className="mt-1 block w-full rounded-lg border border-gray-200 p-2"
              required
            />
          </div>

          <div>
            <label htmlFor="team-member-role" className="block text-sm font-medium text-gray-700">Role</label>
            <select
              id="team-member-role"
              value={role}
              onChange={(e) => setRole(e.target.value as any)}
              className="mt-1 block w-full rounded-lg border border-gray-200 p-2"
            >
              <option value="member">Member</option>
              <option value="admin">Admin</option>
            </select>
          </div>

          <div className="flex justify-end gap-3">
            <button type="button" onClick={onClose} className="px-4 py-2 rounded-lg border border-gray-200">
              Cancel
            </button>
            <button type="submit" disabled={loading} className={`px-4 py-2 rounded-lg bg-[#1A73E8] text-white ${loading ? 'opacity-60' : ''}`}>
              {loading ? 'Adding…' : 'Add Member'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
