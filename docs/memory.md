# Memory

Memory starts as Redis Stream events written after chat or post drafting interactions. The consumer extracts candidate memories with rules suitable for local tests, filters sensitive data, hashes normalized key/value pairs, performs embedding deduplication, detects conflicts, and records `supersedes` when a newer memory conflicts with an older one.

Users can list and delete memories through the API. Sensitive identity numbers, phone numbers, emails, passwords, and card-like values are not stored.



At request time, active memories for the current user are ranked against the resolved query with embedding cosine similarity. Only Top-K relevant records are supplied to the Planner and grounded synthesizer. Memory may personalize routing or wording, but it is never added to the Evidence list and cannot justify an official campus fact.
