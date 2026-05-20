import { FormEvent, useState } from "react";

type Props = {
  loading: boolean;
  onSubmit: (message: string) => Promise<void>;
};

export function ChatInput({ loading, onSubmit }: Props) {
  const [message, setMessage] = useState("");

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const trimmed = message.trim();
    if (!trimmed) return;
    await onSubmit(trimmed);
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
      <div className="mt-3 flex justify-end">
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
