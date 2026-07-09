import { Badge } from "@/components/ui/badge";
import type { SearchResult } from "@/lib/types";

export function CitationChips({ results }: { results: SearchResult[] }) {
  if (results.length === 0) return null;
  return (
    <div className="mt-3 flex flex-wrap gap-1.5">
      {results.map((r, i) => (
        <Badge
          key={i}
          variant={r.kind === "case" ? "secondary" : "outline"}
          title={r.snippet}
          className="h-auto max-w-full cursor-help whitespace-normal break-words border-border/80 text-left shadow-sm"
        >
          {r.source}
        </Badge>
      ))}
    </div>
  );
}
