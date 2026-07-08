import { Badge } from "@/components/ui/badge";
import type { SearchResult } from "@/lib/types";

export function CitationChips({ results }: { results: SearchResult[] }) {
  if (results.length === 0) return null;
  return (
    <div className="mt-2 flex flex-wrap gap-1.5">
      {results.map((r, i) => (
        <Badge
          key={i}
          variant={r.kind === "case" ? "secondary" : "outline"}
          title={r.snippet}
          className="h-auto max-w-full whitespace-normal break-words text-left"
        >
          {r.source}
        </Badge>
      ))}
    </div>
  );
}
