import { Button } from "@/components/ui/button";

interface StarterChipsProps {
  prompts: string[];
  onSelect: (prompt: string) => void;
  disabled: boolean;
}

export function StarterChips({ prompts, onSelect, disabled }: StarterChipsProps) {
  return (
    <div className="mb-4 flex flex-wrap gap-2">
      {prompts.map((prompt) => (
        <Button
          key={prompt}
          variant="outline"
          size="sm"
          disabled={disabled}
          onClick={() => onSelect(prompt)}
          className="h-auto max-w-full whitespace-normal break-words text-left"
        >
          {prompt}
        </Button>
      ))}
    </div>
  );
}
