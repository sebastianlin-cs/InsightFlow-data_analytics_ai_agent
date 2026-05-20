import type { AnalysisMessage } from "../types/session";

type Props = {
  messages: AnalysisMessage[];
};

export function MessageList({ messages }: Props) {
  if (messages.length === 0) {
    return <div className="rounded-lg border border-dashed border-slate-300 bg-white p-8 text-center text-slate-500">No messages yet.</div>;
  }

  return (
    <div className="space-y-3">
      {messages.map((message) => {
        const isUser = message.role === "user";
        return (
          <div key={message.id} className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-2xl rounded-lg px-4 py-3 ${isUser ? "bg-slate-900 text-white" : "border border-slate-200 bg-white text-slate-900"}`}>
              <div className="text-xs font-semibold uppercase tracking-wide opacity-70">{message.role}</div>
              <div className="mt-1 whitespace-pre-wrap text-sm">{message.content}</div>
              <div className="mt-2 text-xs opacity-60">{new Date(message.created_at).toLocaleString()}</div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
