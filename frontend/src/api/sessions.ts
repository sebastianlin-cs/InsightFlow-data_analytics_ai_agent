import { apiRequest } from "./client";
import type { AnalysisMessage, AnalysisSession } from "../types/session";

export function createAnalysisSession(datasetId: number, title?: string): Promise<AnalysisSession> {
  return apiRequest<AnalysisSession>("/api/analysis-sessions", {
    method: "POST",
    body: { dataset_id: datasetId, title },
  });
}

export function listAnalysisSessions(datasetId?: number): Promise<AnalysisSession[]> {
  const query = datasetId ? `?dataset_id=${datasetId}` : "";
  return apiRequest<AnalysisSession[]>(`/api/analysis-sessions${query}`);
}

export function getAnalysisSession(sessionId: number): Promise<AnalysisSession> {
  return apiRequest<AnalysisSession>(`/api/analysis-sessions/${sessionId}`);
}

export function listSessionMessages(sessionId: number): Promise<AnalysisMessage[]> {
  return apiRequest<AnalysisMessage[]>(`/api/analysis-sessions/${sessionId}/messages`);
}
