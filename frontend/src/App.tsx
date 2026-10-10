import { FormEvent, useEffect, useRef, useState } from "react";

import { askQuestion, fetchVehicles, sendFeedback } from "./api";
import type { Answer, Citation, FeedbackValue, VehicleOption } from "./types";

const suggestions = [
  "如何打开充电口？",
  "哨兵模式怎么使用？",
  "不同配置有什么差异？",
];

type SpeechState = "idle" | "speaking" | "paused";

function App() {
  const [vehicles, setVehicles] = useState<VehicleOption[]>([]);
  const [selectedTrim, setSelectedTrim] = useState("");
  const [vehicleError, setVehicleError] = useState("");
  const [question, setQuestion] = useState("");
  const [submittedQuestion, setSubmittedQuestion] = useState("");
  const [answer, setAnswer] = useState<Answer | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [source, setSource] = useState<Citation | null>(null);
  const [feedback, setFeedback] = useState<FeedbackValue | null>(null);
  const [feedbackError, setFeedbackError] = useState("");
  const [micNotice, setMicNotice] = useState(false);
  const [speechState, setSpeechState] = useState<SpeechState>("idle");
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

  const loadVehicles = async () => {
    setVehicleError("");
    try {
      const options = await fetchVehicles();
      setVehicles(options);
      setSelectedTrim((current) => current || options[0]?.trimId || "");
    } catch (loadError) {
      setVehicleError(loadError instanceof Error ? loadError.message : "车型加载失败。请重试。");
    }
  };

  useEffect(() => {
    void loadVehicles();
    return () => window.speechSynthesis?.cancel();
  }, []);

  const speak = (text: string) => {
    if (!("speechSynthesis" in window) || !("SpeechSynthesisUtterance" in window)) {
      setSpeechState("idle");
      return;
    }
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "zh-CN";
    utterance.rate = 1;
    utterance.onend = () => setSpeechState("idle");
    utterance.onerror = () => setSpeechState("idle");
    utteranceRef.current = utterance;
    window.speechSynthesis.speak(utterance);
    setSpeechState("speaking");
  };

  const toggleSpeech = () => {
    if (!answer) return;
    if (speechState === "speaking") {
      window.speechSynthesis.pause();
      setSpeechState("paused");
      return;
    }
    if (speechState === "paused") {
      window.speechSynthesis.resume();
      setSpeechState("speaking");
      return;
    }
    speak(answer.speechText);
  };

  const submitQuestion = async (event?: FormEvent) => {
    event?.preventDefault();
    const cleaned = question.trim();
    if (!cleaned || !selectedTrim || loading) return;

    window.speechSynthesis?.cancel();
    setSpeechState("idle");
    setSubmittedQuestion(cleaned);
    setLoading(true);
    setAnswer(null);
    setError("");
    setSource(null);
    setFeedback(null);
    setFeedbackError("");
    try {
      const response = await askQuestion(cleaned, selectedTrim);
      setAnswer(response);
      speak(response.speechText);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "服务暂时不可用，请重试。");
    } finally {
      setLoading(false);
    }
  };

  const chooseSuggestion = (suggestion: string) => {
    setQuestion(suggestion);
  };

  const recordFeedback = async (value: FeedbackValue) => {
    if (!answer) return;
    const previous = feedback;
    setFeedback(value);
    setFeedbackError("");
    try {
      setFeedback(await sendFeedback(answer.answerId, value));
    } catch (requestError) {
      setFeedback(previous);
      setFeedbackError(
        requestError instanceof Error ? requestError.message : "反馈未保存，请重试。",
      );
    }
  };

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">车书 AI</div>
        <span className="unofficial-badge">非官方产品</span>
      </header>

      <div className={`workspace ${source ? "source-visible" : ""}`}>
        <aside className="vehicle-panel" aria-label="车型配置">
          <div className="vehicle-panel-content">
            <label className="eyebrow" htmlFor="trim-select">
              当前车型
            </label>
            <strong className="model-name">Tesla Model 3</strong>
            {vehicleError ? (
              <div className="inline-error">
                <span>{vehicleError}</span>
                <button type="button" onClick={() => void loadVehicles()}>
                  重试
                </button>
              </div>
            ) : (
              <select
                id="trim-select"
                value={selectedTrim}
                onChange={(event) => setSelectedTrim(event.target.value)}
                disabled={!vehicles.length}
              >
                {!vehicles.length && <option>正在加载配置…</option>}
                {vehicles.map((vehicle) => (
                  <option key={vehicle.trimId} value={vehicle.trimId}>
                    {vehicle.displayName.replace("Model 3 ", "")}
                  </option>
                ))}
              </select>
            )}

            <section className="suggestion-section" aria-labelledby="suggestion-title">
              <h2 id="suggestion-title" className="eyebrow">
                建议问题
              </h2>
              <div className="suggestions">
                {suggestions.map((suggestion) => (
                  <button
                    type="button"
                    className="suggestion-chip"
                    key={suggestion}
                    onClick={() => chooseSuggestion(suggestion)}
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </section>
          </div>

        </aside>

        <main className="conversation">
          <div className="conversation-scroll" aria-live="polite">
            {!submittedQuestion && !loading && (
              <section className="welcome-card">
                <span className="welcome-icon" aria-hidden="true">
                  ✦
                </span>
                <h1>从官方资料中找到清楚答案</h1>
                <p>选择配置，或直接询问车辆功能、手册操作和配置差异。</p>
              </section>
            )}

            {submittedQuestion && (
              <div className="user-row">
                <div className="user-message">{submittedQuestion}</div>
              </div>
            )}

            {loading && (
              <div className="assistant-block loading-card" role="status">
                <span className="spinner" aria-hidden="true" />
                正在查找官方资料…
              </div>
            )}

            {error && (
              <div className="assistant-block status-card status-error">
                <div>
                  <strong>暂时无法连接问答服务</strong>
                  <p>{error} 你的问题仍保留在输入框中。</p>
                </div>
                <button type="button" className="secondary-button" onClick={() => void submitQuestion()}>
                  重试
                </button>
              </div>
            )}

            {answer && (
              <article className={`assistant-block answer-card ${answer.fallbackReason ? "fallback" : ""}`}>
                <div className="assistant-label">
                  <span aria-hidden="true">✦</span>
                  车书 AI
                </div>
                {answer.fallbackReason && <span className="result-label">资料不足 / 无法确认</span>}
                <div className="answer-text">{answer.answer}</div>
                <footer className="answer-actions">
                  <div className="citation-actions">
                    {answer.citations.map((citation) => (
                      <button
                        type="button"
                        className="text-button"
                        key={citation.id}
                        onClick={() => setSource(citation)}
                      >
                        <span aria-hidden="true">▧</span>
                        {citation.section}（Model 3 手册）
                      </button>
                    ))}
                  </div>
                  <div className="utility-actions">
                    <button type="button" className="icon-button" onClick={toggleSpeech}>
                      <span aria-hidden="true">{speechState === "speaking" ? "Ⅱ" : "▶"}</span>
                      <span className="sr-only">
                        {speechState === "speaking" ? "暂停播报" : "播放回答"}
                      </span>
                    </button>
                    <span className="action-divider" />
                    <button
                      type="button"
                      className={`icon-button feedback-up ${feedback === "up" ? "selected" : ""}`}
                      aria-pressed={feedback === "up"}
                      onClick={() => void recordFeedback("up")}
                    >
                      <span aria-hidden="true">👍</span>
                      <span className="sr-only">点赞</span>
                    </button>
                    <button
                      type="button"
                      className={`icon-button feedback-down ${feedback === "down" ? "selected" : ""}`}
                      aria-pressed={feedback === "down"}
                      onClick={() => void recordFeedback("down")}
                    >
                      <span aria-hidden="true">👎</span>
                      <span className="sr-only">点踩</span>
                    </button>
                  </div>
                </footer>
                {feedback && !feedbackError && (
                  <p className="feedback-note">感谢反馈，已记录本次选择。</p>
                )}
                {feedbackError && <p className="feedback-note error-text">{feedbackError}</p>}
              </article>
            )}
          </div>

          <form className="composer-wrap" onSubmit={(event) => void submitQuestion(event)}>
            {micNotice && (
              <div className="mic-notice" role="status">
                语音识别将在后续版本接入，你仍可使用文字提问。
                <button type="button" onClick={() => setMicNotice(false)} aria-label="关闭提示">
                  ×
                </button>
              </div>
            )}
            <div className="composer">
              <textarea
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                placeholder="询问 Model 3 的功能或操作…"
                rows={1}
                onKeyDown={(event) => {
                  if (event.key === "Enter" && !event.shiftKey) {
                    event.preventDefault();
                    void submitQuestion();
                  }
                }}
              />
              <button
                type="button"
                className="composer-button mic-button"
                onClick={() => setMicNotice(true)}
                aria-label="麦克风提问"
              >
                🎙
              </button>
              <button
                type="submit"
                className="composer-button send-button"
                disabled={!question.trim() || !selectedTrim || loading}
                aria-label="发送问题"
              >
                ↑
              </button>
            </div>
            <p className="safety-copy">请优先在车辆静止且确保安全时操作；驾驶中请勿使用该功能。</p>
          </form>
        </main>

        {source && (
          <aside className="source-panel" aria-label="官方资料来源">
            <header className="source-header">
              <strong>官方资料来源</strong>
              <button type="button" className="close-button" onClick={() => setSource(null)} aria-label="关闭来源详情">
                ×
              </button>
            </header>
            <div className="source-content">
              <h2>{source.section}</h2>
              <p className="source-meta">tesla.cn/ownersmanual · 核验于 {source.retrievedAt}</p>
              <div className="source-excerpt">
                <p>本回答依据 Tesla 中国 Model 3 车主手册中的“{source.section}”章节。</p>
                <p>打开原文可查看完整操作方法、注意事项和适用说明。</p>
              </div>
            </div>
            <a className="source-link" href={source.url} target="_blank" rel="noreferrer">
              打开完整官方手册 <span aria-hidden="true">↗</span>
            </a>
          </aside>
        )}
      </div>
    </div>
  );
}

export default App;
