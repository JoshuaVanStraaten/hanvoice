/** React Query hooks — the single place server state is fetched from. */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiGet, apiPatch, apiPost } from "../lib/api";
import { supabase } from "../lib/supabase";
import type {
  Plan,
  BlockCompleteResponse,
  LessonDetail,
  LessonSummary,
  Me,
  Progress,
  Profile,
  ScenarioSummary,
  UsageToday,
} from "../lib/types";

export function useMe() {
  return useQuery({ queryKey: ["me"], queryFn: () => apiGet<Me>("/me") });
}

/** Public pricing — anon RLS read; the landing page shows this pre-signup. */
export function usePlans() {
  return useQuery({
    queryKey: ["plans"],
    queryFn: async (): Promise<Plan[]> => {
      const { data, error } = await supabase
        .from("plans")
        .select("*")
        .order("price_usd_cents", { ascending: true });
      if (error) throw new Error(error.message);
      return (data ?? []) as Plan[];
    },
    staleTime: 60 * 60_000,
  });
}

export function useJoinWaitlist() {
  return useMutation({
    mutationFn: (email: string) =>
      apiPost<{ status: string }>("/waitlist", { email, source: "landing" }),
  });
}

export function useUsageToday() {
  return useQuery({
    queryKey: ["usage-today"],
    queryFn: () => apiGet<UsageToday>("/usage/today"),
    staleTime: 30_000,
  });
}

export function useLessons() {
  return useQuery({
    queryKey: ["lessons"],
    queryFn: () => apiGet<LessonSummary[]>("/lessons"),
    staleTime: 5 * 60_000,
  });
}

export function useLesson(slug: string) {
  return useQuery({
    queryKey: ["lesson", slug],
    queryFn: () => apiGet<LessonDetail>(`/lessons/${slug}`),
    staleTime: 5 * 60_000,
  });
}

export function useScenarios() {
  return useQuery({
    queryKey: ["scenarios"],
    queryFn: () => apiGet<ScenarioSummary[]>("/scenarios"),
    staleTime: 5 * 60_000,
  });
}

/** Marks a self-attested block (explain/quiz) as passed on the backend. */
export function useCompleteBlock(slug: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (blockId: number) =>
      apiPost<BlockCompleteResponse>(`/lessons/blocks/${blockId}/complete`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["lesson", slug] });
      void queryClient.invalidateQueries({ queryKey: ["progress"] });
    },
  });
}

export function useProgress() {
  return useQuery({
    queryKey: ["progress"],
    queryFn: () => apiGet<Progress>("/progress"),
  });
}

export function useUpdateProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (changes: Partial<Pick<Profile, "display_name" | "native_language">>) =>
      apiPatch<Profile>("/me", changes),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["me"] }),
  });
}

export function useCheckout() {
  return useMutation({
    mutationFn: (plan: "premium" | "founder") =>
      apiPost<{ checkout_url: string }>("/billing/checkout", { plan }),
    onSuccess: ({ checkout_url }) => {
      window.location.assign(checkout_url);
    },
  });
}

/** Invalidate everything usage/progress-related after a scored activity. */
export function useActivityInvalidation() {
  const queryClient = useQueryClient();
  return () => {
    void queryClient.invalidateQueries({ queryKey: ["usage-today"] });
    void queryClient.invalidateQueries({ queryKey: ["progress"] });
  };
}
