"use client";

import { useEffect, useState } from "react";

const THINKING_STAGES = [
  "Searching your workspace\u2026",
  "Checking relevant sources\u2026",
  "Preparing grounded answer\u2026",
];

const STAGE_DURATION_MS = 900;
const MIN_DISPLAY_MS = 400;

type ChatThinkingStateProps = {
  isThinking: boolean;
};

/**
 * Animated thinking state for the Chat page.
 * Cycles through thinking stage messages with a minimum display duration
 * so the UI never flickers.
 */
export function ChatThinkingState({ isThinking }: ChatThinkingStateProps) {
  const [stageIndex, setStageIndex] = useState(0);
  const [visible, setVisible] = useState(false);
  const [startedAt, setStartedAt] = useState<number | null>(null);

  useEffect(() => {
    if (isThinking) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setStageIndex(0);
      setVisible(true);
      setStartedAt(Date.now());
    } else {
      // Respect minimum display duration
      const elapsed = startedAt ? Date.now() - startedAt : 0;
      const remaining = Math.max(0, MIN_DISPLAY_MS - elapsed);
      const timer = setTimeout(() => setVisible(false), remaining);
      return () => clearTimeout(timer);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isThinking]);

  useEffect(() => {
    if (!visible) return;

    const interval = setInterval(() => {
      setStageIndex((current) =>
        current < THINKING_STAGES.length - 1 ? current + 1 : current,
      );
    }, STAGE_DURATION_MS);

    return () => clearInterval(interval);
  }, [visible]);

  if (!visible) return null;

  return (
    <article className="mr-auto max-w-3xl rounded-3xl bg-card p-5 shadow-sm ring-1 ring-border">
      <div className="flex items-center gap-3">
        {/* Pulsing dots */}
        <div className="flex gap-1" aria-hidden="true">
          {[0, 1, 2].map((i) => (
            <span
              key={i}
              className="h-2 w-2 rounded-full bg-muted-foreground/50"
              style={{
                animation: `pulse 1.2s ease-in-out ${i * 0.2}s infinite`,
              }}
            />
          ))}
        </div>
        <p className="text-sm font-medium text-muted-foreground transition-all duration-300">
          {THINKING_STAGES[stageIndex]}
        </p>
      </div>

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 0.35; transform: scale(0.85); }
          50% { opacity: 1; transform: scale(1); }
        }
      `}</style>
    </article>
  );
}
