"use client";

import { useEffect, useRef } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ExchangeItem } from "@/components/exchange-item";
import type { Exchange } from "@/lib/types";

interface ExchangeListProps {
  exchanges: Exchange[];
  onResolveReview: (exchangeId: string, approved: boolean) => void;
  onSelectFollowUp: (question: string) => void;
  isBusy: boolean;
}

export function ExchangeList({ exchanges, onResolveReview, onSelectFollowUp, isBusy }: ExchangeListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const lastAnswerLength = exchanges.at(-1)?.answer.length ?? 0;

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [exchanges.length, lastAnswerLength]);

  return (
    <ScrollArea className="min-h-0 flex-1">
      <div className="flex flex-col gap-4 py-2">
        {exchanges.map((exchange) => (
          <ExchangeItem
            key={exchange.id}
            exchange={exchange}
            onResolveReview={onResolveReview}
            onSelectFollowUp={onSelectFollowUp}
            isBusy={isBusy}
          />
        ))}
        <div ref={bottomRef} />
      </div>
    </ScrollArea>
  );
}
