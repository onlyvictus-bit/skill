"""The current policy, not the legacy distractor."""
FRESHNESS_SECONDS = 300


def fresh(captured_at, now):
    return 0 <= now - captured_at <= FRESHNESS_SECONDS
