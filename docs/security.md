# Security

CampusFlow applies three prompt-injection layers:

- Input layer detects direct attempts to ignore instructions or reveal system content.
- Retrieval layer marks suspicious evidence as untrusted data.
- Generation layer synthesizes only from evidence and refuses unsupported factual answers.

Additional controls include PII redaction, tool allowlisting, bounded replans, bounded draft edits, synthetic-only student-card OCR, and privacy-filtered logs.

Runtime provider keys are Fernet-encrypted before persistence and excluded from every response schema. Redis fixed-window limits protect API and chat routes with structured `RATE_LIMITED` responses. Session history stores metadata only; full message bodies are not persisted in session records.
