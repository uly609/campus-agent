# Memory

Memory starts as Redis Stream events written after chat or post drafting interactions. The consumer extracts candidate memories with rules suitable for local tests, filters sensitive data, hashes normalized key/value pairs, performs embedding deduplication, detects conflicts, and records `supersedes` when a newer memory conflicts with an older one.

Users can list and delete memories through the API. Sensitive identity numbers, phone numbers, emails, passwords, and card-like values are not stored.

