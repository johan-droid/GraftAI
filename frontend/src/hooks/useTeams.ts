import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { Team } from "@/types/api";
import { toast } from "react-hot-toast";

export function useTeams() {
  const queryClient = useQueryClient();

  const { data: teams = [], isLoading, error } = useQuery({
    queryKey: ["teams"],
    // Use trailing slash to avoid 307 redirects and ensure consistent URL
    queryFn: () => apiClient.get<Team[]>("/teams/"),
    initialData: [],
  });

  const createTeamMutation = useMutation({
    mutationFn: (newTeam: Partial<Team>) =>
      // backend accepts POST /teams/ - include trailing slash to avoid redirect
      apiClient.post<{ id: string; name: string; slug: string }>("/teams/", newTeam),
    onSuccess: (created) => {
      // Optimistically update the cached teams list so UI updates immediately
      queryClient.setQueryData<Team[] | undefined>(["teams"], (old = []) => {
        const newTeam: Team = {
          id: created.id,
          name: created.name,
          slug: created.slug,
          routing_logic: ("strict" as Team["routing_logic"]),
          members: [],
        };
        return [newTeam, ...(old ?? [])];
      });

      // Ensure server-backed refetch to keep data in sync
      queryClient.invalidateQueries({ queryKey: ["teams"] });
      toast.success("Team created successfully");
    },
    onError: (err: unknown) => {
      const msg = err instanceof Error ? err.message : String(err);
      toast.error(msg || "Failed to create team");
    },
  });

  return {
    teams,
    isLoading,
    error,
    createTeam: createTeamMutation.mutate,
    isCreating: createTeamMutation.isPending,
  };
}
