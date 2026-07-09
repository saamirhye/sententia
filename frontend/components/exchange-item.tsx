import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Card, CardContent } from "@/components/ui/card";
import { CitationChips } from "@/components/citation-chips";
import { FollowUpChips } from "@/components/follow-up-chips";
import { ReviewCard } from "@/components/review-card";
import { ErrorPanel } from "@/components/error-panel";
import { ThinkingIndicator } from "@/components/thinking-indicator";
import type { Exchange } from "@/lib/types";

interface ExchangeItemProps {
  exchange: Exchange;
  onResolveReview: (exchangeId: string, approved: boolean) => void;
  onSelectFollowUp: (question: string) => void;
  isBusy: boolean;
}

export function ExchangeItem({ exchange, onResolveReview, onSelectFollowUp, isBusy }: ExchangeItemProps) {
  const isThinking = exchange.status === "streaming" && exchange.answerChunks.length === 0;
  const isTyping = exchange.status === "streaming" && exchange.answerChunks.length > 0;
  const isSettled = !isThinking && !isTyping;

  return (
    <div className="animate-rise-in flex flex-col gap-3">
      <div className="max-w-[85%] self-end break-words rounded-lg bg-primary px-3 py-2 text-sm text-primary-foreground shadow-sm">
        {exchange.query}
      </div>

      {exchange.status === "awaiting_review" ? (
        <ReviewCard exchange={exchange} onResolve={onResolveReview} />
      ) : (
        <Card className="border border-border shadow-sm ring-0">
          <CardContent>
            {isThinking && <ThinkingIndicator />}

            {isTyping && (
              <p className="whitespace-pre-wrap text-sm">
                {exchange.answerChunks.map((chunk, i) => (
                  <span key={i} className="animate-chunk-in">
                    {chunk}
                  </span>
                ))}
                <span
                  aria-hidden="true"
                  className="animate-caret-blink ml-0.5 inline-block h-4 w-[2px] translate-y-0.5 bg-foreground align-middle"
                />
              </p>
            )}

            {isSettled && (
              <div className="prose prose-sm dark:prose-invert animate-rise-in max-w-none [&>*:first-child]:mt-0 [&>*:last-child]:mb-0">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{exchange.answer}</ReactMarkdown>
              </div>
            )}

            {exchange.status === "error" && <ErrorPanel message={exchange.errorMessage} />}

            {(exchange.status === "done" || exchange.status === "declined") && (
              <CitationChips results={exchange.results} />
            )}
          </CardContent>
        </Card>
      )}

      {exchange.status === "done" && (
        <FollowUpChips
          questions={exchange.followUpQuestions}
          onSelect={onSelectFollowUp}
          disabled={isBusy}
        />
      )}
    </div>
  );
}
