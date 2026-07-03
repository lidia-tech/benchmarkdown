# Mistral OCR Retry Hardening — Design Spec

Issue: [#16 — Harden Mistral OCR extractor against transient API failures](https://github.com/lidia-tech/benchmarkdown/issues/16)
Follows: #8 / PR #15 (Mistral OCR extractor)

## Problem

The extractor makes a single attempt at `upload → signed URL → ocr.process`.
Live testing exposed intermittent, server-side transient failures that are not
extraction bugs (a re-run succeeds) but surface as hard `ValueError`s:

- `Status 404 — "No file matches the given query"`: eventual-consistency race
  just after `files.upload` returns a file id.
- `RemoteProtocolError: Server disconnected without sending a response`: a
  transport-level hiccup during `ocr.process`.

The `mistralai` SDK's built-in retries don't cover a 404, so these slip through.

## Approach

Wrap the whole blocking `upload → signed URL → ocr → join` sequence in a bounded
retry loop. Re-running the *entire* sequence (not just one call) is deliberate:
a fresh `files.upload` yields a new file id, which is what clears the 404 race.

- **Attempts:** `1 + max_retries` (default `max_retries = 3` ⇒ up to 4 attempts).
- **Backoff:** exponential, `_RETRY_BACKOFF_BASE * 2**attempt` seconds
  (0.5, 1.0, 2.0 …), a module constant so it isn't a UI knob.
- Each attempt owns its `finally` cleanup (`files.delete`) so a retried attempt
  doesn't leak the previous upload.

### Error classification (`_is_transient`)

- **Retry:** `httpx.RequestError` subclasses (connection/protocol/timeout, incl.
  `RemoteProtocolError`); HTTP `408`, `409`, `425`, `429`, any `5xx`; and `404`
  (the post-upload race). Status code is read from the SDK error message, which
  always contains `Status <code>` (robust to the SDK's exact attribute names).
- **Fail fast (permanent):** `401`/`403` (auth), `400`/`422` (bad request), any
  other `4xx`, and any exception whose shape we can't classify — we do not retry
  blindly.

The existing friendly error mapping (auth / quota / generic) is applied to the
*final* exception after retries are exhausted or on a permanent error.

## Config change

`MistralOCRConfig` gains `max_retries: int = 3` (`ge=0`). Like `api_key`, it is
**excluded from `BASIC_FIELDS`/`ADVANCED_FIELDS`** — it's a robustness setting,
not a benchmark-quality parameter, so it stays out of the generated UI while
remaining settable programmatically and in saved profiles. `to_ocr_kwargs()` is
unchanged (retries are an extractor concern, not an API parameter).

## Testing

Offline unit tests with a mocked Mistral client (no network, no key):

- **Retry-then-succeed:** client raises a transient error (a fake `SDKError`
  with a 404 message, then a `RemoteProtocolError`) on early attempts, succeeds
  after; assert the final markdown and the attempt count. `time.sleep` is
  monkeypatched to a no-op so tests stay fast.
- **Fail-fast on auth:** a 401 `SDKError` is raised once; assert the extractor
  raises after a single attempt (no retries) with the auth-friendly message.
- **Exhaustion:** a transient error on every attempt; assert it raises after
  exactly `1 + max_retries` attempts.

The existing unit tests (config, `to_ocr_kwargs`, discovery) stay green; the
`integration`+`live` e2e test is unchanged.
