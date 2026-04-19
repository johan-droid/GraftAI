"use client";

import React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getTeamMembers, removeTeamMember } from "@/lib/api";
import { TeamMemberFull } from "@/types/api";
import { toast } from "react-hot-toast";
import { Trash2, Mail, User } from "lucide-react";

export default function TeamMembersList({ teamId }: { teamId: string }) {
  const qc = useQueryClient();

  const { data: members = [], isLoading, error } = useQuery({
    queryKey: ["team-members", teamId],
    queryFn: () => getTeamMembers(teamId),
    staleTime: 1000 * 60, // 1m
  });

  const removeMutation = useMutation({
    mutationFn: ({ memberId }: { memberId: string }) => removeTeamMember(teamId, memberId),
    onMutate: async ({ memberId }) => {
      await qc.cancelQueries({ queryKey: ["team-members", teamId] });
      const previous = qc.getQueryData<TeamMemberFull[] | undefined>(["team-members", teamId]);
      qc.setQueryData<TeamMemberFull[] | undefined>(["team-members", teamId], (old = []) => (old || []).filter((m) => m.id !== memberId));
      return { previous };
    },
    onError: (err, vars, context: any) => {
      qc.setQueryData(["team-members", teamId], context?.previous);
      const msg = (err as any)?.message || "Failed to remove member";
      toast.error(msg);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["team-members", teamId] });
      qc.invalidateQueries({ queryKey: ["teams"] });
      toast.success("Member removed");
    },
  });

  if (isLoading) return <p className="text-sm text-gray-500">Loading members…</p>;
  if (error) return <p className="text-sm text-red-500">Unable to load members</p>;

  if (!members || members.length === 0) return <p className="text-sm text-gray-500">No members</p>;

  const roleBadge = (role: string) => {
    switch (role) {
      case "owner":
        return <span className="px-2 py-1 text-xs font-semibold rounded-full bg-yellow-100 text-yellow-800">Owner</span>;
      case "admin":
        return <span className="px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">Admin</span>;
      case "viewer":
        return <span className="px-2 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-800">Viewer</span>;
      default:
        return <span className="px-2 py-1 text-xs font-semibold rounded-full bg-gray-50 text-gray-700">Member</span>;
    }
  };

  return (
    <div className="mt-3 space-y-2">
      {members.map((m: TeamMemberFull) => (
        <div key={m.id} className="flex items-center justify-between gap-4 p-3 rounded-lg border border-[#F1F3F4] bg-white">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-[#F8F9FA] flex items-center justify-center text-sm text-[#5F6368]">
              <User size={18} />
            </div>
            <div>
              <div className="text-sm font-medium text-[#202124]">{m.email ?? m.user_id}</div>
              <div className="text-xs text-[#5F6368]">Joined {new Date(m.joined_at).toLocaleDateString()}</div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {roleBadge(m.role)}
            <button
              type="button"
              onClick={() => {
                if (!confirm(`Remove ${m.email ?? m.user_id} from this team?`)) return;
                removeMutation.mutate({ memberId: m.id });
              }}
              className="p-2 rounded-full text-red-600 hover:bg-red-50"
              title="Remove member"
            >
              <Trash2 size={16} />
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
