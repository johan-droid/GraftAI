import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { Team } from "@/types/api";
import { toast } from "react-hot-toast";

export function useTeams() {
  const queryClient = useQueryClient();

  const { data: teams = [], isLoading, error } = useQuery({
    queryKey: ["teams"],
    queryFn: () => apiClient.get<Team[]>("/teams"),
    initialData: [],
  });

  const createTeamMutation = useMutation({
    mutationFn: (newTeam: Partial<Team>) => apiClient.post<Team>("/teams", newTeam),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["teams"] });
      toast.success("Team created successfully");
    },
    onError: () => {
      toast.error("Failed to create team");
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
