import { useCallback, useState } from "react";

export const HeadlessChat = () => {
  const [messages, setMessages] = useState<Array<{ id: string; text: string }>>([
    { id: "welcome", text: "Ask for quake trends, Snowflake-backed summaries, or a refresh." },
  ]);
  const [message, setMessage] = useState("");

  const sendMessage = useCallback(
    (message: string) => {
      if (!message.trim()) {
        return;
      }

      setMessages((current) => [...current, { id: crypto.randomUUID(), text: message.trim() }]);
      setMessage("");
    },
    [],
  );

  return (
    <div className="rounded-3xl border border-white/10 bg-white/5 p-4 text-sm text-slate-200 shadow-2xl shadow-slate-950/30 backdrop-blur-xl">
      <h2 className="mb-3 text-base font-semibold text-white">Headless Chat</h2>
      <div className="space-y-2">
        {messages.map((entry) => (
          <div key={entry.id} className="rounded-2xl bg-white/5 px-3 py-2">
            {entry.text}
          </div>
        ))}
      </div>
      <div className="mt-3 flex gap-2">
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          className="min-w-0 flex-1 rounded-2xl border border-white/10 bg-slate-950/70 px-3 py-2 text-white outline-none transition placeholder:text-slate-500 focus:border-cyan-400/70"
          placeholder="Ask something..."
        />
        <button
          onClick={() => sendMessage(message)}
          className="rounded-2xl bg-cyan-400 px-4 py-2 font-medium text-slate-950 transition hover:bg-cyan-300"
        >
          Send
        </button>
      </div>
    </div>
  );
};
