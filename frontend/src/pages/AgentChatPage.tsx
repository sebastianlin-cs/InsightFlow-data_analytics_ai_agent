import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { queryAgent } from "../api/agent";
import { getAnalysisSession, listSessionMessages } from "../api/sessions";
import { BackButton } from "../components/BackButton";
import { ChatInput } from "../components/ChatInput";
import { MessageList } from "../components/MessageList";
import type { AnalysisMessage, AnalysisSession } from "../types/session";

export function AgentChatPage() {
  const { sessionId } = useParams();
  const numericSessionId = Number(sessionId);
  const [session, setSession] = useState<AnalysisSession | null>(null);
  const [messages, setMessages] = useState<AnalysisMessage[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);

  async function loadChat() {
    if (!numericSessionId) return;
    setLoading(true);
    setError(null);
    try {
      const [sessionData, messageData] = await Promise.all([
        getAnalysisSession(numericSessionId),
        listSessionMessages(numericSessionId),
      ]);
      setSession(sessionData);
      setMessages(messageData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load chat");
    } finally {
      setLoading(false);
    }
  }

  async function handleSend(message: string) {
    setSending(true);
    setError(null);
    try {
      const now = new Date().toISOString();
      const response = await queryAgent(numericSessionId, message);
      setMessages((current) => [
        ...current,
        {
          id: -Date.now(),
          session_id: numericSessionId,
          role: "user",
          content: message,
          structured_result_json: null,
          created_at: now,
        },
        {
          id: -Date.now() - 1,
          session_id: numericSessionId,
          role: "assistant",
          content: response.answer,
          structured_result_json: response.metadata ?? null,
          created_at: new Date().toISOString(),
          agent_trace: response.agent_trace,
          analysis_plan: response.analysis_plan,
          tool_used: response.tool_used,
          tool_result: response.tool_result,
          chart_url: response.chart_url,
          follow_up_questions: response.follow_up_questions,
        },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Agent query failed");
    } finally {
      setSending(false);
    }
  }

  useEffect(() => {
    loadChat();
  }, [numericSessionId]);

  if (loading) return <p className="text-sm text-slate-500">Loading session...</p>;
  if (error) return <p className="rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</p>;

  return (
    <div className="space-y-6">
      <div className="flex justify-start">
        <BackButton fallbackTo={session ? `/datasets/${session.dataset_id}` : "/workspace"} label="Back" />
      </div>

      <div>
        <h1 className="text-2xl font-semibold text-slate-950">{session?.title ?? "Analysis Session"}</h1>
      </div>
      <MessageList messages={messages} />
      <ChatInput loading={sending} onSubmit={handleSend} />
    </div>
  );
}
