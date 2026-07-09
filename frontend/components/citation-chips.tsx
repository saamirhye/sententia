import { Badge } from "@/components/ui/badge";
import type { SearchResult } from "@/lib/types";

const TOOLTIP_PREVIEW_LENGTH = 300;

function previewText(text: string): string {
  return text.length > TOOLTIP_PREVIEW_LENGTH
    ? text.slice(0, TOOLTIP_PREVIEW_LENGTH).trim() + "..."
    : text;
}

export function CitationChips({ results }: { results: SearchResult[] }) {
  if (results.length === 0) return null;
  return (
    <div className="mt-3 flex flex-wrap gap-1.5">
      {results.map((r, i) => (
        <Badge
          key={i}
          variant={r.kind === "case" ? "secondary" : "outline"}
          title={previewText(r.text)}
          className="h-auto max-w-full cursor-help whitespace-normal break-words border-border/80 text-left shadow-sm"
        >
          {r.source}
        </Badge>
      ))}
    </div>
  );
}
