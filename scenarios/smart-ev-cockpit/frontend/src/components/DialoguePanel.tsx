import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import type { FormEvent, KeyboardEvent } from "react";

import { APP_COPY, type DialogueLabels } from "../i18n";

export interface DialogueMessage {
  id: string;
  role: "user" | "assistant";
  text: string;
  meta?: string;
  traceId?: string | null;
}

interface DialoguePanelProps {
  utterance: string;
  messages: DialogueMessage[];
  anchorActorId?: string;
  labels?: DialogueLabels;
  onUtteranceChange: (text: string) => void;
  onSubmit: (text: string) => Promise<void>;
}

export function DialoguePanel({
  utterance,
  messages,
  anchorActorId,
  labels = APP_COPY.en.dialogue,
  onUtteranceChange,
  onSubmit,
}: DialoguePanelProps) {
  const [isSending, setIsSending] = useState(false);
  const [scrollbarMetrics, setScrollbarMetrics] = useState({
    hasOverflow: false,
    thumbHeight: 100,
    thumbTop: 0,
  });
  const messagesRef = useRef<HTMLDivElement>(null);
  const isSendingRef = useRef(false);
  const latestMessageId = messages.at(-1)?.id ?? "";

  const updateScrollbarMetrics = useCallback(() => {
    const node = messagesRef.current;
    if (!node) {
      return;
    }
    const maxScrollTop = Math.max(0, node.scrollHeight - node.clientHeight);
    const hasOverflow = maxScrollTop > 1;
    const thumbHeight = hasOverflow
      ? Math.max(18, Math.min(100, (node.clientHeight / node.scrollHeight) * 100))
      : 100;
    const maxThumbTop = Math.max(0, 100 - thumbHeight);
    const thumbTop = hasOverflow
      ? Math.min(maxThumbTop, (node.scrollTop / maxScrollTop) * maxThumbTop)
      : 0;
    setScrollbarMetrics({ hasOverflow, thumbHeight, thumbTop });
  }, []);

  const scrollMessagesFromPointer = useCallback((track: HTMLDivElement, clientY: number) => {
    const node = messagesRef.current;
    if (!node) {
      return;
    }
    const rect = track.getBoundingClientRect();
    const maxScrollTop = Math.max(0, node.scrollHeight - node.clientHeight);
    if (rect.height <= 0 || maxScrollTop <= 0) {
      return;
    }
    const pointerOffset = Math.min(Math.max(clientY - rect.top, 0), rect.height);
    node.scrollTop = (pointerOffset / rect.height) * maxScrollTop;
    updateScrollbarMetrics();
  }, [updateScrollbarMetrics]);

  const handleScrollbarPointerDown = useCallback(
    (event: React.PointerEvent<HTMLDivElement>) => {
      event.preventDefault();
      const track = event.currentTarget;
      scrollMessagesFromPointer(track, event.clientY);

      const handlePointerMove = (moveEvent: PointerEvent) => {
        scrollMessagesFromPointer(track, moveEvent.clientY);
      };
      const handlePointerUp = () => {
        document.removeEventListener("pointermove", handlePointerMove);
        document.removeEventListener("pointerup", handlePointerUp);
      };

      document.addEventListener("pointermove", handlePointerMove);
      document.addEventListener("pointerup", handlePointerUp);
    },
    [scrollMessagesFromPointer],
  );

  useEffect(() => {
    updateScrollbarMetrics();
    const node = messagesRef.current;
    if (!node || typeof ResizeObserver === "undefined") {
      return undefined;
    }
    const observer = new ResizeObserver(updateScrollbarMetrics);
    observer.observe(node);
    return () => observer.disconnect();
  }, [messages.length, updateScrollbarMetrics]);

  useLayoutEffect(() => {
    const node = messagesRef.current;
    if (!node) {
      return;
    }
    node.scrollTop = Math.max(0, node.scrollHeight - node.clientHeight);
    updateScrollbarMetrics();
  }, [anchorActorId, latestMessageId, messages.length, updateScrollbarMetrics]);

  async function submitUtterance() {
    if (isSendingRef.current) {
      return;
    }
    isSendingRef.current = true;
    setIsSending(true);
    try {
      await onSubmit(utterance);
    } finally {
      isSendingRef.current = false;
      setIsSending(false);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await submitUtterance();
  }

  function handleUtteranceKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (
      event.key !== "Enter" ||
      event.shiftKey ||
      event.altKey ||
      event.ctrlKey ||
      event.metaKey ||
      event.nativeEvent.isComposing
    ) {
      return;
    }
    event.preventDefault();
    void submitUtterance();
  }

  return (
    <section
      className="panel dialogue-panel"
      aria-label={labels.floatingLabel}
      data-layout="floating-chat"
      data-anchor-actor={anchorActorId}
    >
      <header className="dialogue-panel__header">
        <div>
          <span>{labels.assistantName}</span>
          <h2>{labels.title}</h2>
        </div>
      </header>
      <div className="dialogue-panel__history-shell" data-history-shell="scrollable">
        <div
          className="dialogue-panel__messages"
          role="log"
          aria-label={labels.recentLabel}
          aria-live="polite"
          data-scrollable="history"
          data-scrollbar="visible"
          data-custom-scrollbar="true"
          data-has-overflow={scrollbarMetrics.hasOverflow ? "true" : "false"}
          tabIndex={0}
          ref={messagesRef}
          onScroll={updateScrollbarMetrics}
        >
          {messages.length > 0 ? (
            messages.map((message) => (
              <article
                className={`dialogue-message dialogue-message--${message.role}`}
                key={message.id}
              >
                <span>{message.role === "user" ? labels.userName : labels.assistantName}</span>
                <p>{message.text}</p>
                {message.meta ? <small>{message.meta}</small> : null}
              </article>
            ))
          ) : (
            <p className="dialogue-panel__empty">{labels.empty}</p>
          )}
        </div>
        <div
          className="dialogue-panel__scrollbar"
          data-scrollbar-track="visible"
          aria-hidden="true"
          onPointerDown={handleScrollbarPointerDown}
        >
          <span
            className="dialogue-panel__scrollbar-thumb"
            style={{
              height: `${scrollbarMetrics.thumbHeight}%`,
              top: `${scrollbarMetrics.thumbTop}%`,
            }}
          />
        </div>
      </div>
      <form className="dialogue-form" onSubmit={handleSubmit}>
        <label htmlFor="utterance">{labels.utterance}</label>
        <textarea
          id="utterance"
          value={utterance}
          onChange={(event) => onUtteranceChange(event.target.value)}
          onKeyDown={handleUtteranceKeyDown}
          rows={4}
        />
        <button type="submit" disabled={isSending}>
          {isSending ? labels.sending : labels.send}
        </button>
      </form>
    </section>
  );
}
