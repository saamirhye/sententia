import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { CitationChips } from "@/components/citation-chips";
import { ReviewCard } from "@/components/review-card";
import type { Exchange } from "@/lib/types";

interface ExchangeItemProps {
  exchange: Exchange;
  onResolveReview: (exchangeId: string, approved: boolean) => void;
}

export function ExchangeItem({ exchange, onResolveReview }: ExchangeItemProps) {
  return (
    <div className="flex flex-col gap-2">
      <div className="max-w-[85%] self-end break-words rounded-lg bg-primary px-3 py-2 text-sm text-primary-foreground">
        {exchange.query}
      </div>

      {exchange.status === "awaiting_review" ? (
        <ReviewCard exchange={exchange} onResolve={onResolveReview} />
      ) : (
        <Card>
          <CardContent>
            <p className="whitespace-pre-wrap text-sm">
              {exchange.answer}
              {exchange.status === "streaming" && (
                <span className="ml-0.5 animate-pulse">...</span>
              )}
            </p>
            {exchange.status === "error" && (
              <Badge variant="destructive" className="mt-2">
                {exchange.errorMessage}
              </Badge>
            )}
            {(exchange.status === "done" || exchange.status === "declined") && (
              <CitationChips results={exchange.results} />
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
