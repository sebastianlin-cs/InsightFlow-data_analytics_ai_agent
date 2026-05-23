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
  const hasCodePreview = Boolean(data.generated_code_preview ?? data.agent_trace?.generated_code_preview);
  const hasCodeResult = data.code_execution_result !== undefined && data.code_execution_result !== null;

  if (!hasPlan && !hasTrace && !chartSrc && !hasToolResult && !hasFollowUps && !hasCodePreview && !hasCodeResult) return null;

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
            <TraceItem label="Execution" value={data.agent_trace.execution_mode ?? data.execution_mode} />
            <TraceItem label="Safety" value={data.agent_trace.safety_check} />
            <TraceItem label="Runner" value={data.agent_trace.runner} />
            <TraceItem label="Status" value={data.agent_trace.execution_status} />
            <TraceItem label="Time" value={formatExecutionTime(data.agent_trace.execution_time_ms)} />
            <TraceItem label="Reentry" value={data.agent_trace.reentry_used === undefined ? undefined : String(data.agent_trace.reentry_used)} />
            <TraceItem label="Retry" value={data.agent_trace.retry_count === undefined ? undefined : String(data.agent_trace.retry_count)} />
            <TraceItem label="Max Retry" value={data.agent_trace.max_retries === undefined ? undefined : String(data.agent_trace.max_retries)} />
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

      {hasCodePreview && (
        <details className="rounded-md border border-slate-200 bg-slate-50">
          <summary className="cursor-pointer px-3 py-2 text-xs font-semibold uppercase tracking-wide text-slate-600">
            Generated Code Preview
          </summary>
          <pre className="max-h-80 overflow-auto border-t border-slate-200 p-3 text-xs text-slate-700">
            {data.generated_code_preview ?? data.agent_trace?.generated_code_preview}
          </pre>
        </details>
      )}

      {hasCodeResult && (
        <details className="rounded-md border border-slate-200 bg-slate-50">
          <summary className="cursor-pointer px-3 py-2 text-xs font-semibold uppercase tracking-wide text-slate-600">
            Code Execution Result
          </summary>
          <pre className="max-h-80 overflow-auto border-t border-slate-200 p-3 text-xs text-slate-700">
            {JSON.stringify(data.code_execution_result, null, 2)}
          </pre>
        </details>
      )}

      {(data.agent_trace?.first_attempt || data.agent_trace?.repair_attempt) && (
        <details className="rounded-md border border-slate-200 bg-slate-50">
          <summary className="cursor-pointer px-3 py-2 text-xs font-semibold uppercase tracking-wide text-slate-600">
            First / Repair Attempt
          </summary>
          <pre className="max-h-80 overflow-auto border-t border-slate-200 p-3 text-xs text-slate-700">
            {JSON.stringify(
              {
                first_attempt: data.agent_trace.first_attempt,
                repair_attempt: data.agent_trace.repair_attempt,
              },
              null,
              2,
            )}
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
  execution_mode?: string | null;
  code_execution_result?: unknown;
  generated_code_preview?: string | null;
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
    execution_mode: message.execution_mode ?? getStringValue(structured.execution_mode),
    code_execution_result: message.code_execution_result ?? structured.code_execution_result,
    generated_code_preview:
      message.generated_code_preview ?? getStringValue(structured.generated_code_preview),
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

function formatExecutionTime(value: number | null | undefined): string | undefined {
  return typeof value === "number" ? `${value} ms` : undefined;
}
