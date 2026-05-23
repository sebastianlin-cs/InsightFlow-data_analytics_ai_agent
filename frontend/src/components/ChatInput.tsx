import { FormEvent, useState } from "react";

type Props = {
  loading: boolean;
  onSubmit: (message: string, maxRetries: number) => Promise<void>;
};

export function ChatInput({ loading, onSubmit }: Props) {
  const [message, setMessage] = useState("");
  const [maxRetries, setMaxRetries] = useState(1);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const trimmed = message.trim();
    if (!trimmed) return;
    await onSubmit(trimmed, maxRetries);
    setMessage("");
  }

  return (
    <form onSubmit={handleSubmit} className="rounded-lg border border-slate-200 bg-white p-4">
      <textarea
        value={message}
        onChange={(event) => setMessage(event.target.value)}
        rows={3}
        placeholder="Ask about the dataset schema"
        className="w-full resize-none rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-900"
      />
      <div className="mt-3 flex items-center justify-between gap-3">
        <label className="flex items-center gap-2 text-xs font-medium text-slate-600">
          Debug retries
          <select
            value={maxRetries}
            onChange={(event) => setMaxRetries(Number(event.target.value))}
            className="rounded-md border border-slate-300 bg-white px-2 py-1 text-xs text-slate-900 outline-none focus:border-slate-900"
          >
            <option value={0}>0</option>
            <option value={1}>1</option>
            <option value={2}>2</option>
            <option value={3}>3</option>
          </select>
        </label>
        <button
          disabled={loading || !message.trim()}
          className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:bg-slate-400"
        >
          {loading ? "Sending..." : "Send"}
        </button>
      </div>
    </form>
  );
}
