export type SearchResultKind = "legislation" | "case";

export interface SearchResult {
  source: string;
  text: string;
  kind: SearchResultKind;
}

export interface HumanReviewPayload {
  thread_id: string;
  question: string;
  query: string;
  attempts: number;
  results: SearchResult[];
}

export interface DonePayload {
  results: SearchResult[];
  sufficient: boolean;
  attempts: number;
  follow_up_questions: string[];
}

export type ExchangeStatus = "streaming" | "awaiting_review" | "done" | "declined" | "error";

/**
 * One row in the scrolling history. This is cosmetic UI continuity only --
 * each exchange is an independent backend call with its own server-generated
 * thread_id (relevant only if human_review_required fires). The backend has
 * no cross-request memory; nothing here is ever sent back as "prior context."
 */
export interface Exchange {
  id: string;
  query: string;
  status: ExchangeStatus;
  answer: string;
  answerChunks: string[]; // raw chunks in arrival order -- used only while actively streaming
  results: SearchResult[];
  sufficient: boolean | null;
  attempts: number | null;
  reviewQuestion: string | null;
  threadId: string | null;
  errorMessage: string | null;
  followUpQuestions: string[];
}
