import { apiRequest } from "./client";
import type { AgentQueryResponse } from "../types/agent";

export function queryAgent(sessionId: number, query: string): Promise<AgentQueryResponse> {
  return apiRequest<AgentQueryResponse>("/api/agent/query", {
    method: "POST",
    body: { session_id: sessionId, query },
  });
}
