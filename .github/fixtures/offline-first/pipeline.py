from rules import fresh


def process(sample, now):
    """Refuse revoked or stale input before returning its Unicode payload."""
    if sample['revoked']:
        raise ValueError('ACCESS_REVOKED')
    if not fresh(sample['captured_at'], now):
        raise ValueError('STALE_INPUT')
    return sample['text']
