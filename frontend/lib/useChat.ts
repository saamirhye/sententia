"use client";

import { useCallback, useRef, useState } from "react";
import { streamChat } from "@/lib/streamChat";
import type { Exchange } from "@/lib/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

function newExchange(query: string): Exchange {
  return {
    id: crypto.randomUUID(),
    query,
    status: "streaming",
    answer: "",
    answerChunks: [],
    results: [],
    sufficient: null,
    attempts: null,
    reviewQuestion: null,
    threadId: null,
    errorMessage: null,
  };
}

/**
 * Drives the scrolling exchange history. Each call to sendQuery starts a
 * brand-new, independent backend run (POST /api/chat) -- there is no shared
 * conversation state with prior exchanges, by design (see Exchange's doc
 * comment in lib/types.ts). resolveReview continues the one exchange
 * currently paused at the human-review checkpoint via POST /api/chat/resume.
 */
export function useChat() {
  const [exchanges, setExchanges] = useState<Exchange[]>([]);
  const busyRef = useRef(false);
  const isBusy = exchanges.some((e) => e.status === "streaming" || e.status === "awaiting_review");

  const updateExchange = useCallback((id: string, patch: Partial<Exchange>) => {
    setExchanges((prev) => prev.map((e) => (e.id === id ? { ...e, ...patch } : e)));
  }, []);

  const sendQuery = useCallback(
    async (query: string) => {
      if (busyRef.current) return;
      busyRef.current = true;

      const exchange = newExchange(query);
      setExchanges((prev) => [...prev, exchange]);

      try {
        await streamChat(
          `${API_BASE_URL}/api/chat`,
          { query },
          {
            onAnswerDelta: (text) =>
              setExchanges((prev) =>
                prev.map((e) =>
                  e.id === exchange.id
                    ? { ...e, answer: e.answer + text, answerChunks: [...e.answerChunks, text] }
                    : e
                )
              ),
            onHumanReviewRequired: (payload) =>
              updateExchange(exchange.id, {
                status: "awaiting_review",
                reviewQuestion: payload.question,
                threadId: payload.thread_id,
                results: payload.results,
                attempts: payload.attempts,
              }),
            onDone: (payload) =>
              updateExchange(exchange.id, {
                status: "done",
                results: payload.results,
                sufficient: payload.sufficient,
                attempts: payload.attempts,
              }),
          }
        );
      } catch (err) {
        updateExchange(exchange.id, {
          status: "error",
          errorMessage: err instanceof Error ? err.message : "Request failed.",
        });
      } finally {
        setExchanges((prev) => {
          const current = prev.find((e) => e.id === exchange.id);
          if (current?.status !== "awaiting_review") busyRef.current = false;
          return prev;
        });
      }
    },
    [updateExchange]
  );

  const resolveReview = useCallback(
    async (exchangeId: string, approved: boolean) => {
      const exchange = exchanges.find((e) => e.id === exchangeId);
      if (!exchange || !exchange.threadId) return;

      updateExchange(exchangeId, { status: "streaming" });

      try {
        await streamChat(
          `${API_BASE_URL}/api/chat/resume`,
          { thread_id: exchange.threadId, approved },
          {
            onAnswerDelta: (text) =>
              setExchanges((prev) =>
                prev.map((e) =>
                  e.id === exchangeId
                    ? { ...e, answer: e.answer + text, answerChunks: [...e.answerChunks, text] }
                    : e
                )
              ),
            onHumanReviewRequired: () =>
              updateExchange(exchangeId, {
                status: "error",
                errorMessage: "Unexpected second review request.",
              }),
            onDone: (payload) =>
              updateExchange(exchangeId, {
                status: approved ? "done" : "declined",
                results: payload.results,
                sufficient: payload.sufficient,
                attempts: payload.attempts,
              }),
          }
        );
      } catch (err) {
        updateExchange(exchangeId, {
          status: "error",
          errorMessage: err instanceof Error ? err.message : "Request failed.",
        });
      } finally {
        busyRef.current = false;
      }
    },
    [exchanges, updateExchange]
  );

  return { exchanges, isBusy, sendQuery, resolveReview };
}
