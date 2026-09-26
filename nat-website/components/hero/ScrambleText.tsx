"use client";

import { useEffect, useRef, useState } from "react";

const GLYPHS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
const SETTLE_MS_PER_CHAR = 40;
const SETTLE_STAGGER_MS = 28;

/**
 * Per-character "decode" reveal: each character cycles random glyphs before settling into
 * the final text, left to right. Implemented with requestAnimationFrame per constitution
 * Principle III (no GSAP ScrambleTextPlugin — that's a paid Club GreenSock bonus plugin).
 */
export default function ScrambleText({ text, className = "" }: { text: string; className?: string }) {
  const [display, setDisplay] = useState(text);
  const rafRef = useRef(0);

  useEffect(() => {
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduceMotion) {
      setDisplay(text);
      return;
    }

    const chars = text.split("");
    const settleAt = chars.map((_, i) => i * SETTLE_STAGGER_MS + SETTLE_MS_PER_CHAR * 4);
    const totalDuration = Math.max(...settleAt) + 100;
    let start: number | null = null;

    function frame(timestamp: number) {
      if (start === null) start = timestamp;
      const elapsed = timestamp - start;

      const next = chars
        .map((char, i) => {
          if (char === " ") return " ";
          if (elapsed >= settleAt[i]) return char;
          return GLYPHS[Math.floor(Math.random() * GLYPHS.length)];
        })
        .join("");
      setDisplay(next);

      if (elapsed < totalDuration) {
        rafRef.current = requestAnimationFrame(frame);
      } else {
        setDisplay(text);
      }
    }

    rafRef.current = requestAnimationFrame(frame);
    return () => cancelAnimationFrame(rafRef.current);
  }, [text]);

  return (
    <span className={className}>
      <span aria-hidden="true" className="font-mono tabular-nums">
        {display}
      </span>
      <span className="sr-only">{text}</span>
    </span>
  );
}
