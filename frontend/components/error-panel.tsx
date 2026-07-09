import { AlertTriangleIcon } from "lucide-react";

export function ErrorPanel({ message }: { message: string | null }) {
  return (
    <div
      role="alert"
      className="mt-3 flex items-start gap-2 rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive"
    >
      <AlertTriangleIcon className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
      <div>
        <p className="font-medium">Something went wrong</p>
        <p className="text-destructive/90">{message ?? "The request failed. Please try again."}</p>
      </div>
    </div>
  );
}
