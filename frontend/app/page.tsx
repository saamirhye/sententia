"use client";

import { useChat } from "@/lib/useChat";
import { STARTER_PROMPTS } from "@/lib/starter-prompts";
import { StarterChips } from "@/components/starter-chips";
import { ChatInput } from "@/components/chat-input";
import { ExchangeList } from "@/components/exchange-list";

export default function Page() {
  const { exchanges, isBusy, sendQuery, resolveReview } = useChat();

  return (
    <main className="mx-auto flex h-dvh w-full max-w-2xl flex-col p-4">
      <h1 className="mb-4 text-xl font-semibold">Sententia</h1>

      <ExchangeList
        exchanges={exchanges}
        onResolveReview={resolveReview}
        onSelectFollowUp={sendQuery}
        isBusy={isBusy}
      />

      {exchanges.length === 0 && (
        <StarterChips prompts={STARTER_PROMPTS} onSelect={sendQuery} disabled={isBusy} />
      )}

      <ChatInput onSubmit={sendQuery} disabled={isBusy} />
    </main>
  );
}
