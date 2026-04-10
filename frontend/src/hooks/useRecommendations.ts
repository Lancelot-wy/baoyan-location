"use client";
import { useState, useCallback } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface ProgressEvent {
  step: string;
  message: string;
  progress: number;
  school?: string;
  department?: string;
  tier?: string;
  session_id?: string;
  total_results?: number;
}

export function useRecommendationStream() {
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState("准备中...");
  const [currentSchool, setCurrentSchool] = useState<string | null>(null);
  const [currentTier, setCurrentTier] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);
  const [analyzedSchools, setAnalyzedSchools] = useState<{school: string; dept: string; tier: string}[]>([]);

  const generate = useCallback(async (sessionId: string): Promise<string | null> => {
    setIsGenerating(true);
    setProgress(0);
    setMessage("连接服务器...");
    setError(null);
    setDone(false);
    setAnalyzedSchools([]);

    return new Promise((resolve) => {
      fetch(`${API}/api/v1/recommendations/generate-stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId }),
      }).then(async (response) => {
        if (!response.ok || !response.body) {
          setError("服务器连接失败");
          setIsGenerating(false);
          resolve(null);
          return;
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done: readerDone, value } = await reader.read();
          if (readerDone) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            try {
              const event: ProgressEvent = JSON.parse(line.slice(6));
              setProgress(event.progress || 0);
              setMessage(event.message || "");

              if (event.school) {
                setCurrentSchool(event.school);
                setCurrentTier(event.tier || null);
              }
              if (event.step === "analyzing" && event.school && event.department) {
                setAnalyzedSchools((prev) => [...prev, {
                  school: event.school!, dept: event.department!, tier: event.tier || ""
                }]);
              }

              if (event.step === "done") {
                setDone(true);
                setIsGenerating(false);
                resolve(sessionId);
                return;
              }
              if (event.step === "error") {
                setError(event.message);
                setIsGenerating(false);
                resolve(null);
                return;
              }
            } catch { /* skip malformed */ }
          }
        }

        // Stream ended without done event
        if (!done) {
          setIsGenerating(false);
          resolve(sessionId); // Try to show results anyway
        }
      }).catch((err) => {
        setError(`网络错误：${err.message}`);
        setIsGenerating(false);
        resolve(null);
      });
    });
  }, [done]);

  return {
    generate,
    progress,
    message,
    currentSchool,
    currentTier,
    isGenerating,
    error,
    done,
    analyzedSchools,
  };
}
