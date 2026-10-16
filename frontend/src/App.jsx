
import { useState } from "react";
import "./index.css";

const API_URL = "http://127.0.0.1:8000";

export default function App() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  async function askQuestion(event) {
    event.preventDefault();

    const text = question.trim();
    if (!text || loading) return;

    setMessages((old) => [...old, { role: "user", text }]);
    setQuestion("");
    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: text }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "The request failed.");
      }

      setMessages((old) => [
        ...old,
        {
          role: "assistant",
          text: data.answer,
          sources: data.sources || [],
        },
      ]);
    } catch (error) {
      setMessages((old) => [
        ...old,
        {
          role: "assistant",
          text: `Could not reach the chatbot: ${error.message}`,
          sources: [],
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page">
      <header className="header">
        <div className="logo">C</div>
        <div>
          <h1>College Assistant</h1>
          <p>Ask questions about your college</p>
        </div>
      </header>

      <section className="chat">
        {messages.length === 0 && (
          <div className="welcome">
            <h2>How can I help you?</h2>
            <p>
              Ask about academics, admissions, facilities,
              examination notices, and college services.
            </p>
            <p className="note">
              Answers will be based on verified college sources.
            </p>
          </div>
        )}

        {messages.map((message, index) => (
          <article className={`message ${message.role}`} key={index}>
            <strong>
              {message.role === "user" ? "You" : "College Assistant"}
            </strong>
            <p>{message.text}</p>

            {message.sources?.length > 0 && (
              <div className="sources">
                <strong>Sources</strong>
                {message.sources.map((source, i) => (
                  <a
                    key={`${source.url}-${i}`}
                    href={source.url}
                    target="_blank"
                    rel="noreferrer"
                  >
                    {source.title}
                    {source.page ? ` — page ${source.page}` : ""}
                  </a>
                ))}
              </div>
            )}
          </article>
        ))}

        {loading && (
          <p className="loading">Searching college information...</p>
        )}
      </section>

      <form className="composer" onSubmit={askQuestion}>
        <input
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Ask a college-related question..."
          maxLength={1000}
          aria-label="Your question"
        />
        <button disabled={loading || !question.trim()}>
          {loading ? "Wait..." : "Ask"}
        </button>
      </form>

      <footer>
        Verify important deadlines and policies with official college offices.
      </footer>
    </main>
  );
}
