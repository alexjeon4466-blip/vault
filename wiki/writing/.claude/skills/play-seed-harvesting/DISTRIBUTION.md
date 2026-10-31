# Distribution notes

Base skill version: **1.8.0**. Portable packaging revision: **1.8.0-portable.1**.

This is a separate distribution copy, not a synchronized replacement for an installed skill. No source profile, source Vault, authentication, Git commit or push is changed by packaging. Version suffix identifies portability edits, not newly implemented collection capabilities.

## Included adaptations

- Replace the sender's absolute Vault path and private doctrine filenames with recipient-owned contracts and optional writing context.
- Make named companion skills optional, and document Markdown-only use.
- Retain the verified-access-baseline behavior, source boundaries, Korean pool version, A0/A1 semantics, full-view/all-states user-ledger rule and explicit approval gates.
- Explain that historical policy IDs and approvals do not constitute recipient consent or current access evidence.
- Remove selected session/source-story anecdotes; retain reusable methodological rules and public attribution.
- Make the spider test's artifact root temporary and portable; preserve an explicit environment override. Replace source-shaped fixture stories and selected numeric post IDs with synthetic test values, not source aliases.
- Keep production parser and validator code unchanged. Clearly label the incomplete spider and the unimplemented parts of its design reference; correct the reference's obsolete four-profile list to match the shipped code.
- Add installation/use instructions, dependency declaration, templates, rights notices, verification receipt and file hashes.

## Exclusions

Only the source skill's Markdown references and Python scripts are exported. Bytecode/cache directories are excluded. No harvest database, raw HTML, source-body archive, real batch JSON, personal creative work, review record, session log, cookie, credential, browser binary/profile, virtual environment or unrelated skill is copied. The templates are empty operating forms, not fabricated execution data.

## Known limitations

- Scrapy spider `start()` schedules no requests. Parsers and tests are not a complete network collector.
- Japanese operating references are included; Japanese run-specific collectors and approved sampling contracts are not.
- The generic structure checker receives only a CLI smoke check here; see the separate tests for card/A1 validators.
- The tests do not establish live site access, semantic judgment quality, source rights, full-original rendering, historical novelty or cross-platform runtime compatibility.
- Historical references may have narrower examples; the current SKILL.md contract and recipient's explicit instructions take priority. Do not reuse historical quotas, source substitutions, preselection forms or extra-conservative rules by accident.
- No automatic update channel or public repository is configured.

`MANIFEST.json` covers every payload file except itself. The delivered ZIP has a separate SHA-256 sidecar. Hashes detect accidental changes; they are not a cryptographic author signature.
