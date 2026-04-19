"use client";

import { motion } from "framer-motion";
import { Users, Plus, Shuffle, Layers, ShieldAlert, Link as LinkIcon, MoreVertical, Copy } from "lucide-react";
import { useTeams } from "@/hooks/useTeams";
import { toast } from "react-hot-toast";
import { Team, TeamMember } from "@/types/api";
import AddMemberModal from "@/components/Teams/AddMemberModal";
import TeamMembersList from "@/components/Teams/TeamMembersList";
import { useState } from "react";

type TeamMemberUi = TeamMember & {
  name?: string;
  initial?: string;
  color?: string;
};

type UiTeam = Omit<Team, "members"> & {
  members: TeamMemberUi[];
};

export default function TeamsPage() {
  const { teams, isLoading, createTeam, isCreating } = useTeams();
  const [openTeamToAdd, setOpenTeamToAdd] = useState<string | null>(null);
  const [expandedMembersTeam, setExpandedMembersTeam] = useState<string | null>(null);
  const displayTeams: UiTeam[] = teams as UiTeam[];

  const copyTeamLink = async (slug: string) => {
    const url = `${typeof window !== "undefined" ? window.location.origin : "https://graftai.com"}/${slug}`;
    try {
      if (!navigator?.clipboard) {
        throw new Error("Clipboard API not available");
      }
      await navigator.clipboard.writeText(url);
      toast.success("Team link copied to clipboard!");
    } catch (err) {
      console.error("Failed to copy team link:", err);
      toast.error("Unable to copy link. Please copy manually: " + url);
    }
  };

  const handleCreateTeam = () => {
    createTeam({
      name: `New Team ${Date.now()}`,
      slug: `team-${Date.now()}`,
      routing_logic: "round_robin",
    });
  };

  if (isLoading) {
    return (
      <div className="p-6 md:p-10 max-w-6xl mx-auto w-full">
        <div className="rounded-3xl border border-[#DADCE0] bg-white p-8 shadow-sm">
          <p className="text-sm text-[#5F6368]">Loading teams...</p>
        </div>
      </div>
    );
  }

  if (displayTeams.length === 0) {
    return (
      <div className="p-6 md:p-10 max-w-6xl mx-auto w-full">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-10 pb-6 border-b border-[#DADCE0]">
          <div>
            <h1 className="text-3xl font-medium text-[#202124] tracking-tight mb-2 flex items-center gap-3">
              Teams & Resources
            </h1>
            <p className="text-[#5F6368] text-base max-w-xl">
              Manage collective availability and distribute meetings intelligently across your organization.
            </p>
          </div>
          <button
            type="button"
            onClick={handleCreateTeam}
            disabled={isCreating}
            className="inline-flex items-center justify-center gap-2 bg-[#1A73E8] text-white hover:bg-[#1557B0] px-6 py-2.5 rounded-full text-sm font-medium transition-colors shadow-sm shrink-0 disabled:cursor-not-allowed disabled:opacity-70"
          >
            <Plus size={18} />
            {isCreating ? "Creating..." : "New Team"}
          </button>
        </div>

        <div className="rounded-3xl border border-[#DADCE0] bg-white p-8 shadow-sm text-center">
          <Users size={28} className="mx-auto mb-4 text-[#5F6368]" />
          <h2 className="text-xl font-semibold text-[#202124] mb-2">No teams yet</h2>
          <p className="text-sm text-[#5F6368] max-w-md mx-auto mb-6">
            Create your first team to start routing meetings across shared availability instead of assigning them manually.
          </p>
          <button
            type="button"
            onClick={handleCreateTeam}
            disabled={isCreating}
            className="inline-flex items-center justify-center gap-2 bg-[#1A73E8] text-white hover:bg-[#1557B0] px-6 py-2.5 rounded-full text-sm font-medium transition-colors shadow-sm disabled:cursor-not-allowed disabled:opacity-70"
          >
            <Plus size={18} />
            {isCreating ? "Creating..." : "Create your first team"}
          </button>
        </div>
      </div>
    );
  }

  const getRoutingDisplay = (logic: string) => {
    switch (logic) {
      case "round_robin":
        return {
          icon: <Shuffle size={14} />,
          label: "Round Robin",
          desc: "Distributes meetings evenly",
          color: "text-[#1A73E8] bg-[#E8F0FE]",
        };
      case "collective":
        return {
          icon: <Layers size={14} />,
          label: "Collective",
          desc: "Requires all members to be free",
          color: "text-[#137333] bg-[#E6F4EA]",
        };
      default:
        return {
          icon: <ShieldAlert size={14} />,
          label: "Strict",
          desc: "Manual assignment",
          color: "text-[#5F6368] bg-[#F1F3F4]",
        };
    }
  };

  

  return (
    <>
      <div className="p-6 md:p-10 max-w-6xl mx-auto w-full">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-10 pb-6 border-b border-[#DADCE0]">
        <div>
          <h1 className="text-3xl font-medium text-[#202124] tracking-tight mb-2 flex items-center gap-3">
            Teams & Resources
          </h1>
          <p className="text-[#5F6368] text-base max-w-xl">
            Manage collective availability and distribute meetings intelligently across your organization.
          </p>
        </div>
        <button
          type="button"
          onClick={handleCreateTeam}
          disabled={isCreating}
          className="inline-flex items-center justify-center gap-2 bg-[#1A73E8] text-white hover:bg-[#1557B0] px-6 py-2.5 rounded-full text-sm font-medium transition-colors shadow-sm shrink-0 disabled:cursor-not-allowed disabled:opacity-70"
        >
          <Plus size={18} />
          {isCreating ? "Creating..." : "New Team"}
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {displayTeams.map((team, i) => {
          const routing = getRoutingDisplay(team.routing_logic);

          return (
            <motion.div
              key={team.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              className="bg-white border border-[#DADCE0] rounded-3xl p-6 shadow-sm hover:shadow-md transition-all flex flex-col"
            >
              <div className="flex items-start justify-between mb-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-2xl bg-[#F8F9FA] border border-[#DADCE0] flex items-center justify-center text-[#5F6368]">
                    <Users size={24} />
                  </div>
                  <div>
                    <h2 className="text-xl font-semibold text-[#202124]">{team.name}</h2>
                    <p className="text-sm text-[#5F6368]">graftai.com/{team.slug}</p>
                  </div>
                </div>
                <button
                  type="button"
                  aria-label="Team actions"
                  title="Team actions"
                  className="text-[#5F6368] hover:bg-[#F1F3F4] p-2 rounded-full transition-colors"
                >
                  <MoreVertical size={20} />
                </button>
              </div>

              <div className="bg-[#F8F9FA] border border-[#DADCE0] rounded-2xl p-4 mb-6 flex items-center gap-4">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${routing.color}`}>
                  {routing.icon}
                </div>
                <div>
                  <p className="text-sm font-semibold text-[#202124]">{routing.label} Routing</p>
                  <p className="text-xs text-[#5F6368]">{routing.desc}</p>
                </div>
              </div>

              <div className="flex-1 mb-6">
                <div className="flex items-center justify-between mb-3">
                  <p className="text-xs font-semibold text-[#5F6368] uppercase tracking-wider">
                    Team Members ({team.members?.length ?? 0})
                  </p>
                  <button
                    type="button"
                    onClick={() => setExpandedMembersTeam(expandedMembersTeam === String(team.id) ? null : String(team.id))}
                    className="text-sm text-[#1A73E8] hover:underline"
                  >
                    {expandedMembersTeam === String(team.id) ? "Hide" : "Manage"}
                  </button>
                </div>
                <div className="flex items-center gap-2">
                  <div className="flex -space-x-3">
                    {team.members?.map((member, idx) => {
                      const memberName = member.name ?? member.user_id;
                      const initial = member.initial ?? memberName.charAt(0).toUpperCase();
                      const memberColor = member.color ?? (member.role === "admin" ? "bg-[#E8F0FE] text-[#1A73E8]" : "bg-[#F8F9FA] text-[#5F6368]");

                      return (
                        <div
                          key={member.user_id + idx}
                          className={`w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold border-2 border-white ring-1 ring-[#DADCE0] shadow-sm ${memberColor}`}
                          title={`${memberName} (${member.role})`}
                        >
                          {initial}
                        </div>
                      );
                    })}
                  </div>
                  <button
                    type="button"
                    aria-label="Add team member"
                    title="Add team member"
                    onClick={() => setOpenTeamToAdd(String(team.id))}
                    className="w-9 h-9 rounded-full border border-dashed border-[#DADCE0] flex items-center justify-center text-[#5F6368] hover:bg-[#F8F9FA] hover:text-[#1A73E8] transition-colors ml-2 shadow-sm"
                  >
                    <Plus size={16} />
                  </button>
                </div>
                {expandedMembersTeam === String(team.id) ? <TeamMembersList teamId={String(team.id)} /> : null}
              </div>

              <div className="pt-4 border-t border-[#F1F3F4] flex items-center justify-between mt-auto">
                <button
                  type="button"
                  onClick={() => copyTeamLink(team.slug)}
                  className="flex items-center gap-2 text-sm font-medium text-[#1A73E8] hover:bg-[#E8F0FE] px-4 py-2 rounded-full transition-colors"
                >
                  <LinkIcon size={16} />
                  Copy Team Link
                </button>
                <button
                  type="button"
                  aria-label="Copy team link"
                  title="Copy team link"
                  onClick={() => copyTeamLink(team.slug)}
                  className="text-sm font-medium text-[#5F6368] hover:text-[#202124] hover:bg-[#F1F3F4] px-4 py-2 rounded-full transition-colors"
                >
                  <Copy size={16} />
                </button>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
    {openTeamToAdd ? (
      <AddMemberModal open={!!openTeamToAdd} onClose={() => setOpenTeamToAdd(null)} teamId={openTeamToAdd!} />
    ) : null}
  </>
  );
}
