export type AgentQueryResponse = {
  session_id: number;
  dataset_id: number;
  answer: string;
  metadata: Record<string, unknown>;
};
