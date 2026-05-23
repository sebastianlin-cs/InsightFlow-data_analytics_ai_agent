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
  execution_mode?: string | null;
  code_generation_source?: string | null;
  safety_check?: string | null;
  runner?: string | null;
  timeout_seconds?: number | null;
  execution_status?: string | null;
  execution_time_ms?: number | null;
  reentry_used?: boolean | null;
  retry_count?: number | null;
  max_retries?: number | null;
  first_attempt?: Record<string, unknown> | null;
  repair_attempt?: Record<string, unknown> | null;
  generated_code_preview?: string | null;
  error?: string | null;
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
  execution_mode?: string | null;
  code_execution_result?: Record<string, unknown> | null;
  generated_code_preview?: string | null;
  metadata?: Record<string, unknown>;
};
