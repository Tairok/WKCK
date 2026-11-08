import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./client";

const poll = (ms) => ({ refetchInterval: ms, refetchIntervalInBackground: false, staleTime: ms / 2 });

export const useInfo = () =>
  useQuery({ queryKey: ["info"], queryFn: () => api("/api/info"), ...poll(30000) });

export const useInventory = () =>
  useQuery({ queryKey: ["inventory"], queryFn: () => api("/api/inventory"), ...poll(10000) });

export const useSensors = () =>
  useQuery({ queryKey: ["sensors"], queryFn: () => api("/api/sensors/latest"), ...poll(3000) });

export const useHealthSummary = () =>
  useQuery({ queryKey: ["health", "summary"], queryFn: () => api("/api/health/summary"), ...poll(10000) });

export const useHealthAnalysis = () =>
  useQuery({ queryKey: ["health", "analysis"], queryFn: () => api("/api/health/analysis"), ...poll(10000) });

export const useAlertHistory = () =>
  useQuery({
    queryKey: ["health", "history"],
    queryFn: async () => {
      const data = await api("/api/health/history?limit=50");
      return { ...data, history: data.history.slice(0, 50) };
    },
    ...poll(30000),
  });

export const useUsers = () =>
  useQuery({
    queryKey: ["users"],
    queryFn: async () => ({ users: await api("/api/users") }),
    ...poll(30000),
  });

export const useCreateUser = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body) => ({
      user: await api("/api/users", {
        method: "POST",
        body: {
          username: body.username.trim(),
          email: body.email.trim(),
          last_login: null,
        },
      }),
    }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["users"] }),
  });
};
