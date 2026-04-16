import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { AutomationRule } from "@/types/api";
import { toast } from "react-hot-toast";

export function useAutomations() {
  const queryClient = useQueryClient();

  const { data: automations = [], isLoading, error } = useQuery<AutomationRule[]>({
    queryKey: ["automations"],
    queryFn: () => apiClient.get<AutomationRule[]>("/automations"),
    initialData: [],
  });

  const toggleMutation = useMutation({
    mutationFn: ({ id, active }: { id: string; active: boolean }) =>
      apiClient.patch(`/automations/${id}`, { active }),
    onMutate: async (variables: { id: string; active: boolean }) => {
      await queryClient.cancelQueries({ queryKey: ["automations"] });
      const previous = queryClient.getQueryData<AutomationRule[]>(["automations"]);

      queryClient.setQueryData<AutomationRule[]>(["automations"], (old) =>
        old?.map((rule) =>
          rule.id === variables.id ? { ...rule, active: variables.active } : rule
        )
      );

      return { previous };
    },
    onError: (err, variables, context) => {
      toast.error("Failed to update workflow.");
      if (context?.previous) {
        queryClient.setQueryData(["automations"], context.previous);
      }
    },
    onSuccess: () => {
      toast.success("Workflow updated");
      queryClient.invalidateQueries({ queryKey: ["automations"] });
    },
  });

  return {
    automations,
    isLoading,
    error,
    toggleAutomation: (id: string, active: boolean) =>
      toggleMutation.mutate({ id, active }),
  };
}
