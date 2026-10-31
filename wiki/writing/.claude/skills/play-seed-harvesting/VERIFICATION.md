# Verification receipt

Package: **1.8.0-portable.1**

Verified at: 2026-10-31T12:08:12.235833+09:00

The payload was ZIP-encoded, extracted into a separate directory, and exercised there. This is a local Windows verification, not a cross-platform certification.

| Check | Observed result |
|---|---|
| A1 validator regression | 11 tests passed |
| Community note regression | 5 tests passed |
| Scrapy parser regression | 22 tests passed |
| Generic structure CLI smoke | exit 0 |
| A1 validator CLI smoke | exit 0 |
| Community note CLI smoke | exit 0 |

Total regression tests passed: **38**.

Additional checks:

- Python 3.11.15; optional parser runtime Scrapy 2.17.0 (asserted by its test).
- 7 Python files parsed with AST; SKILL frontmatter name, description, body and version validated.
- 23 unique root-relative backtick reference/script/template links resolved.
- Source/access/ethics and Korean standing-contract sections preserved; production parser and validator text unchanged.
- Source skill's complete file SHA-256 snapshot unchanged after packaging/testing.
- No sender absolute paths, private-note dependencies, credential-pattern matches or embedded email matches in the text payload. This allowlisted review and pattern scan is not a mathematical proof of all possible sensitive information.
- Bytecode, raw source archives, session logs, browser state and credentials are outside the allowlisted payload.
- Extracted test payload equals staged payload; final ZIP CRC, exact file set, manifest hashes, safe paths and final extraction equality checked by the packaging verifier.

Not tested or claimed: live community requests/access, actual seed yield, semantic A0/A1 correctness, full-original reproduction rights, automated scheduling/resume, Japanese network collectors, recipient installation, macOS/Linux execution. The spider start routine remains incomplete; this is explicitly documented rather than patched into a new collector.
