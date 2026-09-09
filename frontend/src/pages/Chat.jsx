import { useEffect, useRef, useState } from "react";
import { askQuestion, getErrorMessage } from "../api";
import ModelBadge from "../components/ModelBadge";
import { useChat } from "../ChatContext";

export default function Chat() {
  const { messages, setMessages } = useChat();
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, sending]);

  async function handleSend(e) {
    e.preventDefault();
    const question = input.trim();
    if (!question || sending) return;

    setError("");
    setInput("");
    setMessages((prev) => [...prev, { role: "user", text: question }]);
    setSending(true);

    try {
      const { data } = await askQuestion(question);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: data.answer,
          tier: data.model_tier,
          cached: data.cached,
          cost: data.cost_usd,
          tokens: data.tokens_in + data.tokens_out,
          note: data.note,
        },
      ]);
    } catch (err) {
      setError(getErrorMessage(err));
      // Put the question back so it's not lost if the call failed.
      setInput(question);
      setMessages((prev) => prev.slice(0, -1));
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="chat-page">
      <div className="chat-window">
        {messages.length === 0 && (
          <div className="chat-empty">
            <p>Ask anything. Short, simple questions get routed to a lightweight model.</p>
            <p>Longer or "explain/compare/write"-style questions get the bigger model - unless today's budget is already spent.</p>
          </div>
        )}

        {messages.map((message, index) => (
          <div key={index} className={"bubble bubble--" + message.role}>
            <p className="bubble__text">{message.text}</p>
            {message.role === "assistant" && (
              <div className="bubble__meta">
                <ModelBadge tier={message.tier} cached={message.cached} />
                <span className="bubble__stat">{message.tokens} tokens</span>
                <span className="bubble__stat">${message.cost.toFixed(6)}</span>
              </div>
            )}
            {message.note && <p className="bubble__note">{message.note}</p>}
          </div>
        ))}

        {sending && (
          <div className="bubble bubble--assistant bubble--pending">
            <span className="typing-dot" />
            <span className="typing-dot" />
            <span className="typing-dot" />
          </div>
        )}

        <div ref={scrollRef} />
      </div>

      {error && <p className="form-error form-error--chat" role="alert">{error}</p>}

      <form className="chat-input" onSubmit={handleSend}>
        <textarea
          className="chat-input__field"
          placeholder="Ask something..."
          value={input}
          rows={1}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSend(e);
            }
          }}
        />
        <button className="button button--primary" type="submit" disabled={sending || !input.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}
