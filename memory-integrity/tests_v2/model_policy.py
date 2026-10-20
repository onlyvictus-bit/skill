"""Explicit legacy protocol-model scope; never imported by product code.

The active release does NOT permit native operations. These narrowly named
test classes retain historical state-machine/transport-double assertions by
mocking only the policy check. No production enable switch or native proof.
"""
from functools import wraps
from unittest.mock import patch


def legacy_model_policy(*targets):
    def decorate(cls):
        original = cls.setUp
        @wraps(original)
        def setup(case):
            for target in targets:
                policy = patch(target)
                policy.start()
                case.addCleanup(policy.stop)
            original(case)
        cls.setUp = setup
        return cls
    return decorate
