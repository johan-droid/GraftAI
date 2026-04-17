import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { AutomationRule } from "@/types/api";
import { toast } from "react-hot-toast";

export function useAutomations() {
  const queryClient = useQueryClient();

  const { data: automations = [], isLoading, error } = useQuery<AutomationRule[]>({
    queryKey: ["automation-rules"],
    queryFn: () => apiClient.get<AutomationRule[]>("/automation/rules"),
    initialData: [],
  });

  const toggleMutation = useMutation({
    mutationFn: ({ id, is_enabled }: { id: string; is_enabled: boolean }) =>
      apiClient.fetch<AutomationRule>(`/automation/rules/${id}`, {
        method: "PUT",
        json: { is_enabled },
      }),
    onMutate: async (variables: { id: string; is_enabled: boolean }) => {
      await queryClient.cancelQueries({ queryKey: ["automation-rules"] });
      const previous = queryClient.getQueryData<AutomationRule[]>(["automation-rules"]);

      queryClient.setQueryData<AutomationRule[]>(["automation-rules"], (old) =>
        old?.map((rule) =>
          rule.id === variables.id ? { ...rule, is_enabled: variables.is_enabled } : rule
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
      queryClient.invalidateQueries({ queryKey: ["automation-rules"] });
    },
  });

  return {
    automations,
    isLoading,
    error,
    toggleAutomation: (id: string, is_enabled: boolean) =>
      toggleMutation.mutate({ id, is_enabled }),
  };
}
