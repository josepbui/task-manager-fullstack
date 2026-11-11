/**
 * types/index.ts
 * Central domain-model types for Thomathdison P2P Class platform.
 *
 * Naming convention (Tech-Invisible strategy):
 *   - wallet address  → "identityAccount"
 *   - NFT / token     → "digitalCredential"
 *   - smart contract  → "automatedGuarantee"
 *   - Arweave TX      → "storageReceipt"
 */

// ─── Lecture / Content Layer ────────────────────────────────────────────────

/** Static lecture asset stored on Arweave / IPFS */
export interface LectureAsset {
  /** Arweave transaction ID (storageReceipt) */
  storageReceiptId: string;
  /** Publicly accessible gateway URL */
  gatewayUrl: string;
  /** MIME type: "application/pdf" | "image/png" | "image/jpeg" */
  mimeType: "application/pdf" | "image/png" | "image/jpeg";
  /** Total page / slide count */
  totalPages: number;
  /** SHA-256 content hash for integrity verification */
  contentHash: string;
}

export interface Lecture {
  id: string;
  title: string;
  description: string;
  instructorAccount: string; // Tech-Invisible: wallet address
  asset: LectureAsset;
  /** ISO-8601 publish timestamp */
  publishedAt: string;
  /** Base L2 chain ID where automatedGuarantee is deployed */
  chainId: number;
  /** Address of the content-access automatedGuarantee */
  guaranteeAddress: string;
}

// ─── FIB (Fill-In-the-Blank) Layer ──────────────────────────────────────────

/**
 * Bounding box expressed as percentage of the containing page dimensions.
 * This keeps coordinates resolution-independent regardless of render size.
 */
export interface PercentageBoundingBox {
  /** Left edge as % of page width  (0–100) */
  xPct: number;
  /** Top edge as % of page height (0–100) */
  yPct: number;
  /** Width as % of page width     (0–100) */
  widthPct: number;
  /** Height as % of page height   (0–100) */
  heightPct: number;
}

export type FibType = "text" | "multiple_choice" | "numeric";

export interface FibBlank {
  id: string;
  /** 1-based page number this blank belongs to */
  pageNumber: number;
  /** Position on page in percentage coordinates */
  bbox: PercentageBoundingBox;
  type: FibType;
  /** Correct answer(s); for multiple_choice, first element is correct */
  answers: string[];
  /** Choices for multiple_choice type */
  options?: string[];
  /** Optional hint shown after wrong attempt */
  hint?: string;
  /** Score weight (default 1) */
  points: number;
}

export interface FibMetadata {
  lectureId: string;
  version: number;
  blanks: FibBlank[];
  /** Arweave TX ID where this metadata JSON is stored */
  storageReceiptId?: string;
}

// ─── Session / Progress Layer ────────────────────────────────────────────────

export type BlankStatus = "unanswered" | "correct" | "incorrect";

export interface BlankAttempt {
  blankId: string;
  userAnswer: string;
  status: BlankStatus;
  attemptedAt: string; // ISO-8601
}

export interface LearnerSession {
  sessionId: string;
  lectureId: string;
  /** Tech-Invisible: wallet address of the learner */
  learnerAccount: string;
  attempts: BlankAttempt[];
  /** Total points earned in this session */
  earnedPoints: number;
  /** Maximum possible points */
  totalPoints: number;
  startedAt: string;
  completedAt?: string;
}

// ─── Digital Credential (NFT) Layer ─────────────────────────────────────────

export interface DigitalCredential {
  /** ERC-721 token ID */
  tokenId: string;
  lectureId: string;
  /** Recipient's identity account */
  holderAccount: string;
  /** Percentage score that triggered issuance */
  scorePercent: number;
  /** Arweave TX storing the credential metadata */
  metadataStorageReceiptId: string;
  issuedAt: string;
  /** Base L2 transaction hash */
  chainTxHash: string;
}

// ─── Utility Types ───────────────────────────────────────────────────────────

export type Result<T, E = Error> =
  | { ok: true; value: T }
  | { ok: false; error: E };

export type AsyncResult<T, E = Error> = Promise<Result<T, E>>;
