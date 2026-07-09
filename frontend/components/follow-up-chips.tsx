import { Button } from "@/components/ui/button";

interface FollowUpChipsProps {
  questions: string[];
  onSelect: (question: string) => void;
  disabled: boolean;
}

export function FollowUpChips({ questions, onSelect, disabled }: FollowUpChipsProps) {
  if (questions.length === 0) return null;
  return (
    <div className="flex flex-col gap-1.5">
      <span className="text-xs font-medium text-muted-foreground">Continue exploring</span>
      <div className="flex flex-wrap gap-2">
        {questions.map((question) => (
          <Button
            key={question}
            variant="secondary"
            size="sm"
            disabled={disabled}
            onClick={() => onSelect(question)}
            className="h-auto max-w-full whitespace-normal break-words text-left"
          >
            {question}
          </Button>
        ))}
      </div>
    </div>
  );
}
