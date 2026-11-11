/**
 * lib/fib/scorer.ts
 * Pure, side-effect-free FIB scoring engine.
 * All logic is synchronous — no blockchain calls here.
 */

import type {
  FibBlank,
  FibMetadata,
  BlankAttempt,
  LearnerSession,
  BlankStatus,
} from "@/types";

// ─── Scoring helpers ─────────────────────────────────────────────────────────

/**
 * Normalise a user answer for comparison:
 * - trim whitespace
 * - lowercase
 * - collapse internal whitespace
 */
function normalise(raw: string): string {
  return raw.trim().toLowerCase().replace(/\s+/g, " ");
}

/**
 * Evaluate a single blank attempt against its correct answers.
 * For "numeric" type, allows ±0.001 floating-point tolerance.
 */
export function evaluateBlank(blank: FibBlank, userAnswer: string): BlankStatus {
  const norm = normalise(userAnswer);
  if (!norm) return "unanswered";

  if (blank.type === "numeric") {
    const userNum = parseFloat(norm);
    if (isNaN(userNum)) return "incorrect";
    return blank.answers.some((a) => Math.abs(parseFloat(a) - userNum) <= 0.001)
      ? "correct"
      : "incorrect";
  }

  return blank.answers.some((a) => normalise(a) === norm) ? "correct" : "incorrect";
}

/**
 * Score a complete set of attempts against FIB metadata.
 * Returns a partial LearnerSession (without identity fields).
 */
export function scoreSession(
  metadata: FibMetadata,
  attempts: Map<string, string> // blankId → userAnswer
): Pick<LearnerSession, "attempts" | "earnedPoints" | "totalPoints"> {
  const blankMap = new Map<string, FibBlank>(metadata.blanks.map((b) => [b.id, b]));

  let earnedPoints = 0;
  let totalPoints = 0;

  const scoredAttempts: BlankAttempt[] = metadata.blanks.map((blank) => {
    totalPoints += blank.points;
    const userAnswer = attempts.get(blank.id) ?? "";
    const status = evaluateBlank(blank, userAnswer);
    if (status === "correct") earnedPoints += blank.points;

    return {
      blankId: blank.id,
      userAnswer,
      status,
      attemptedAt: new Date().toISOString(),
    };
  });

  // Handle attempts for blanks not in metadata (defensive)
  attempts.forEach((userAnswer, blankId) => {
    if (!blankMap.has(blankId)) return;
  });

  return { attempts: scoredAttempts, earnedPoints, totalPoints };
}

/**
 * Calculate score percentage (0–100), rounded to 1 decimal.
 */
export function scorePercent(earned: number, total: number): number {
  if (total === 0) return 0;
  return Math.round((earned / total) * 1000) / 10;
}

/**
 * Determine if a session qualifies for digital credential issuance.
 * Threshold: 70% by default (configurable).
 */
export function qualifiesForCredential(
  earned: number,
  total: number,
  thresholdPct = 70
): boolean {
  return scorePercent(earned, total) >= thresholdPct;
}
