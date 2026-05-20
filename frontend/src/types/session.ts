export type AnalysisSession = {
  id: number;
  user_id: number;
  dataset_id: number;
  title: string;
  current_topic: string | null;
  current_intent: string | null;
  current_filters_json: Record<string, unknown> | null;
  last_result_summary_json: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
};

export type AnalysisMessage = {
  id: number;
  session_id: number;
  role: string;
  content: string;
  structured_result_json: Record<string, unknown> | unknown[] | null;
  created_at: string;
};
