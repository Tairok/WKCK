import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { api } from "./client";

const poll = (ms) => ({ refetchInterval: ms, refetchIntervalInBackground: false, staleTime: ms / 2 });

export const useInfo = () =>
  useQuery({ queryKey: ["info"], queryFn: () => api("/api/info"), ...poll(30000) });

export const useInventory = () =>
  useQuery({ queryKey: ["inventory"], queryFn: () => api("/api/inventory"), ...poll(10000) });

export const useSensors = () =>
  useQuery({ queryKey: ["sensors"], queryFn: () => api("/api/sensors/latest"), ...poll(3000) });

export const useSensorSeries = (windowSeconds, sensorIds) =>
  useQuery({
    queryKey: ["sensors", "series", windowSeconds, sensorIds],
    queryFn: () => {
      const params = new URLSearchParams({ window: String(windowSeconds) });
      sensorIds.forEach((id) => params.append("sensor", id));
      return api(`/api/sensors/series?${params}`);
    },
    enabled: sensorIds.length > 0,
    placeholderData: keepPreviousData,
    refetchInterval: 1000,
    refetchIntervalInBackground: false,
  });

export const useHealthSummary = () =>
  useQuery({ queryKey: ["health", "summary"], queryFn: () => api("/api/health/summary"), ...poll(10000) });

export const useHealthAnalysis = () =>
  useQuery({ queryKey: ["health", "analysis"], queryFn: () => api("/api/health/analysis"), ...poll(10000) });

export const useAlertHistory = () =>
  useQuery({
    queryKey: ["health", "history"],
    queryFn: () => api("/api/health/history?limit=50"),
    ...poll(30000),
  });
