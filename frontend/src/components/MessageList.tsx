import { apiAssetUrl } from "../api/client";
import type { AgentTrace } from "../types/agent";
import type { AnalysisMessage } from "../types/session";

type Props = {
  messages: AnalysisMessage[];
};

export function MessageList({ messages }: Props) {
  if (messages.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-slate-300 bg-white p-8 text-center text-slate-500">
        No messages yet.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {messages.map((message) => {
        const isUser = message.role === "user";
        const rich = getRichAgentData(message);
        return (
          <div key={message.id} className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-3xl rounded-lg px-4 py-3 ${
                isUser ? "bg-slate-900 text-white" : "border border-slate-200 bg-white text-slate-900"
              }`}
            >
              <div className="text-xs font-semibold uppercase tracking-wide opacity-70">{message.role}</div>
              <div className="mt-1 whitespace-pre-wrap text-sm leading-6">{message.content}</div>
              {!isUser && <AssistantResult data={rich} />}
              <div className="mt-2 text-xs opacity-60">{new Date(message.created_at).toLocaleString()}</div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function AssistantResult({ data }: { data: RichAgentData }) {
  const chartSrc = apiAssetUrl(data.chart_url ?? data.agent_trace?.chart_url);
  const hasPlan = data.analysis_plan.length > 0;
  const hasTrace = Boolean(data.agent_trace);
  const hasFollowUps = data.follow_up_questions.length > 0;
  const hasToolResult = data.tool_result !== undefined && data.tool_result !== null;

  if (!hasPlan && !hasTrace && !chartSrc && !hasToolResult && !hasFollowUps) return null;

  return (
    <div className="mt-4 space-y-3 border-t border-slate-100 pt-3">
      {hasPlan && (
        <section>
          <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Analysis Plan</div>
          <ol className="mt-2 list-decimal space-y-1 pl-5 text-sm text-slate-700">
            {data.analysis_plan.map((step, index) => (
              <li key={`${step}-${index}`}>{step}</li>
            ))}
          </ol>
        </section>
      )}

      {hasTrace && data.agent_trace && (
        <section>
          <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Agent Trace</div>
          <div className="mt-2 grid gap-2 text-xs text-slate-700 sm:grid-cols-2">
            <TraceItem label="Intent" value={data.agent_trace.intent} />
            <TraceItem label="Planner" value={data.agent_trace.planner_source} />
            <TraceItem label="Response" value={data.agent_trace.response_source} />
            <TraceItem label="Tool" value={data.agent_trace.selected_tool ?? data.tool_used} />
            <TraceItem label="Fallback" value={data.agent_trace.fallback_reason ?? "none"} />
            <TraceItem label="LLM" value={data.agent_trace.llm_enabled === undefined ? undefined : String(data.agent_trace.llm_enabled)} />
          </div>
          {data.agent_trace.steps && data.agent_trace.steps.length > 0 && (
            <ul className="mt-2 list-disc space-y-1 pl-5 text-xs text-slate-500">
              {data.agent_trace.steps.map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ul>
          )}
        </section>
      )}

      {chartSrc && (
        <section>
          <img
            src={chartSrc}
            alt="Generated chart"
            className="max-h-96 w-full rounded-md border border-slate-200 object-contain"
          />
        </section>
      )}

      {hasToolResult && (
        <details className="rounded-md border border-slate-200 bg-slate-50">
          <summary className="cursor-pointer px-3 py-2 text-xs font-semibold uppercase tracking-wide text-slate-600">
            Tool Result
          </summary>
          <pre className="max-h-80 overflow-auto border-t border-slate-200 p-3 text-xs text-slate-700">
            {JSON.stringify(data.tool_result, null, 2)}
          </pre>
        </details>
      )}

      {hasFollowUps && (
        <section>
          <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Follow-up Questions</div>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-700">
            {data.follow_up_questions.map((question) => (
              <li key={question}>{question}</li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}

function TraceItem({ label, value }: { label: string; value: string | null | undefined }) {
  if (!value) return null;
  return (
    <div className="rounded-md bg-slate-50 px-2 py-1">
      <span className="font-semibold text-slate-500">{label}: </span>
      <span>{value}</span>
    </div>
  );
}

type RichAgentData = {
  agent_trace?: AgentTrace;
  analysis_plan: string[];
  tool_used?: string | null;
  tool_result?: unknown;
  chart_url?: string | null;
  follow_up_questions: string[];
};

function getRichAgentData(message: AnalysisMessage): RichAgentData {
  const structured = isRecord(message.structured_result_json) ? message.structured_result_json : {};
  const agentTrace = message.agent_trace ?? getAgentTrace(structured);
  return {
    agent_trace: agentTrace,
    analysis_plan: message.analysis_plan ?? getStringArray(structured.analysis_plan),
    tool_used: message.tool_used ?? getStringValue(structured.selected_tool),
    tool_result: message.tool_result,
    chart_url: message.chart_url ?? getStringValue(structured.chart_url),
    follow_up_questions: message.follow_up_questions ?? getStringArray(structured.follow_up_questions),
  };
}

function getAgentTrace(value: Record<string, unknown>): AgentTrace | undefined {
  return isRecord(value.agent_trace) ? (value.agent_trace as AgentTrace) : undefined;
}

function getStringArray(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];
}

function getStringValue(value: unknown): string | null {
  return typeof value === "string" ? value : null;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
