"use client";
import { useState, useCallback } from "react";
import type { QuestionnaireState, ResearchExperienceCreate, PaperCreate, CompetitionCreate, InternshipCreate } from "@/lib/types";
import {
  createStudentProfile, addResearchExperience, addPaper,
  addCompetition, addInternship, setPreferences, generateRecommendations,
} from "@/lib/api";
import toast from "react-hot-toast";

const TOTAL_STEPS = 7;

export function useQuestionnaire() {
  const [state, setState] = useState<QuestionnaireState>({
    step: 1,
    research_experiences: [],
    papers: [],
    competitions: [],
    internships: [],
  });
  const [loading, setLoading] = useState(false);

  const goNext = useCallback(() => {
    setState((s) => ({ ...s, step: Math.min(s.step + 1, TOTAL_STEPS) }));
  }, []);

  const goPrev = useCallback(() => {
    setState((s) => ({ ...s, step: Math.max(s.step - 1, 1) }));
  }, []);

  // Step 1: Create profile
  const submitBasicProfile = useCallback(async (data: QuestionnaireState["profile"]) => {
    if (!data) return;
    setLoading(true);
    try {
      const profile = await createStudentProfile(data);
      setState((s) => ({ ...s, profile: data, session_id: profile.session_id }));
      goNext();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "保存失败，请重试");
    } finally {
      setLoading(false);
    }
  }, [goNext]);

  // Step 2: Research experiences
  const submitResearch = useCallback(async (experiences: ResearchExperienceCreate[]) => {
    if (!state.session_id) return;
    setLoading(true);
    try {
      for (const exp of experiences) {
        await addResearchExperience(state.session_id, exp);
      }
      setState((s) => ({ ...s, research_experiences: experiences }));
      goNext();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "保存科研经历失败");
    } finally {
      setLoading(false);
    }
  }, [state.session_id, goNext]);

  // Step 3: Papers
  const submitPapers = useCallback(async (papers: PaperCreate[]) => {
    if (!state.session_id) return;
    setLoading(true);
    try {
      for (const paper of papers) {
        await addPaper(state.session_id, paper);
      }
      setState((s) => ({ ...s, papers }));
      goNext();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "保存论文失败");
    } finally {
      setLoading(false);
    }
  }, [state.session_id, goNext]);

  // Step 4: Competitions
  const submitCompetitions = useCallback(async (competitions: CompetitionCreate[]) => {
    if (!state.session_id) return;
    setLoading(true);
    try {
      for (const comp of competitions) {
        await addCompetition(state.session_id, comp);
      }
      setState((s) => ({ ...s, competitions }));
      goNext();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "保存竞赛失败");
    } finally {
      setLoading(false);
    }
  }, [state.session_id, goNext]);

  // Step 5: Internships
  const submitInternships = useCallback(async (internships: InternshipCreate[]) => {
    if (!state.session_id) return;
    setLoading(true);
    try {
      for (const intern of internships) {
        await addInternship(state.session_id, intern);
      }
      setState((s) => ({ ...s, internships }));
      goNext();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "保存实习失败");
    } finally {
      setLoading(false);
    }
  }, [state.session_id, goNext]);

  // Step 6: Preferences
  const submitPreferences = useCallback(async (preferences: QuestionnaireState["preferences"]) => {
    if (!state.session_id || !preferences) return;
    setLoading(true);
    try {
      await setPreferences(state.session_id, preferences);
      setState((s) => ({ ...s, preferences }));
      goNext();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "保存偏好失败");
    } finally {
      setLoading(false);
    }
  }, [state.session_id, goNext]);

  // Step 7: Generate recommendations and redirect
  const submitAndGenerate = useCallback(async (): Promise<string | null> => {
    if (!state.session_id) return null;
    setLoading(true);
    try {
      await generateRecommendations(state.session_id);
      return state.session_id;
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "推荐生成失败");
      return null;
    } finally {
      setLoading(false);
    }
  }, [state.session_id]);

  return {
    state,
    loading,
    totalSteps: TOTAL_STEPS,
    goNext,
    goPrev,
    submitBasicProfile,
    submitResearch,
    submitPapers,
    submitCompetitions,
    submitInternships,
    submitPreferences,
    submitAndGenerate,
  };
}
