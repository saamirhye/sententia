export function ThinkingIndicator() {
  return (
    <div className="flex items-center gap-2 py-0.5 text-sm text-muted-foreground" role="status" aria-live="polite">
      <svg className="size-4 animate-spin text-muted-foreground" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
        <path className="opacity-90" fill="currentColor" d="M4 12a8 8 0 0 1 8-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
      <span>Thinking…</span>
    </div>
  );
}
