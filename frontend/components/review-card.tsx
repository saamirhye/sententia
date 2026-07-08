import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CitationChips } from "@/components/citation-chips";
import type { Exchange } from "@/lib/types";

interface ReviewCardProps {
  exchange: Exchange;
  onResolve: (exchangeId: string, approved: boolean) => void;
}

export function ReviewCard({ exchange, onResolve }: ReviewCardProps) {
  return (
    <Card className="border-amber-400">
      <CardHeader>
        <CardTitle className="text-sm">Human review needed</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm">{exchange.reviewQuestion}</p>
        <p className="mt-1 text-xs text-muted-foreground">
          Reached after {exchange.attempts} search attempt(s).
        </p>
        <CitationChips results={exchange.results} />
        <div className="mt-3 flex gap-2">
          <Button size="sm" onClick={() => onResolve(exchange.id, true)}>
            Approve
          </Button>
          <Button size="sm" variant="outline" onClick={() => onResolve(exchange.id, false)}>
            Decline
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
