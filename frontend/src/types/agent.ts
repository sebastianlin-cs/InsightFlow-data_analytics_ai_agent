export interface AgentTrace {
  intent?: string;
  planner_source?: string;
  response_source?: string;
  selected_tool?: string;
  validated_columns?: string[];
  chart_url?: string | null;
  fallback_reason?: string | null;
  llm_enabled?: boolean;
  llm_provider?: string | null;
  steps?: string[];
}

export type AgentQueryResponse = {
  session_id: number;
  dataset_id: number;
  intent?: string;
  answer: string;
  analysis_plan?: string[];
  tool_used?: string | null;
  tool_result?: unknown;
  chart_url?: string | null;
  follow_up_questions?: string[];
  agent_trace?: AgentTrace;
  metadata?: Record<string, unknown>;
};
