import type { DonePayload, HumanReviewPayload } from "@/lib/types";

interface StreamChatHandlers {
  onAnswerDelta: (text: string) => void;
  onHumanReviewRequired: (payload: HumanReviewPayload) => void;
  onDone: (payload: DonePayload) => void;
}

/**
 * Hand-rolled SSE consumer for this project's own wire format
 * (backend/src/sententia/api/routes.py's _sse(): "event: <name>\ndata: <json>\n\n").
 * Not EventSource (GET-only, our endpoints are POST) and not a third-party
 * SSE library -- the format is simple and fully ours.
 */
export async function streamChat(
  url: string,
  body: object,
  handlers: StreamChatHandlers,
  signal?: AbortSignal
): Promise<void> {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });
  if (!response.ok || !response.body) {
    throw new Error(`Request failed: ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const blocks = buffer.split("\n\n");
    buffer = blocks.pop() ?? ""; // last, possibly incomplete, block stays buffered

    for (const block of blocks) {
      if (!block.trim()) continue;
      const lines = block.split("\n");
      const eventLine = lines.find((l) => l.startsWith("event: "));
      const dataLine = lines.find((l) => l.startsWith("data: "));
      if (!eventLine || !dataLine) continue;

      const eventName = eventLine.slice("event: ".length).trim();
      const data = JSON.parse(dataLine.slice("data: ".length));

      if (eventName === "answer_delta") handlers.onAnswerDelta(data.text);
      else if (eventName === "human_review_required") handlers.onHumanReviewRequired(data);
      else if (eventName === "done") handlers.onDone(data);
    }
  }
}
