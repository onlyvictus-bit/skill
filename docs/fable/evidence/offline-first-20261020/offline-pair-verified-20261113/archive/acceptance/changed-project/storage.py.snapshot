import hashlib


def source_digest(text):
    """Hash exact UTF-8 bytes, including தமிழ் text and newlines."""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def reopen(checkpoint, current_text):
    if checkpoint['source_digest'] != source_digest(current_text):
        raise ValueError('CHECKPOINT_SOURCE_CHANGED')
    return checkpoint['completed']
