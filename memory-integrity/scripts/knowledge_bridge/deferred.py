#!/usr/bin/env python3
"""Phase 5: deferral registry for optional deployments (CAP-01/02/17/18/19/
20/22 and heavyweight backends). Everything here is DEFERRED by default:
enable() without a written approval raises; with approval it returns
ACTIVATION_PENDING — never ACTIVE, which needs a qualified backend the
registry does not possess. Standard library only.
"""
CAPABILITIES = (
    ("global-graphrag", ("CAP-01",), ("measured win vs local traversal",)),
    ("drift-exploration", ("CAP-02",), ("bounded loop contract proven",)),
    ("distributed-store", ("CAP-17",), ("measured size/concurrency demand",)),
    ("external-vector-store", ("CAP-18",), ("reindex parity proven",)),
    ("mcp-api-facade", ("CAP-19",), ("auth model + actual user need",)),
    ("graph-explorer", ("CAP-20",), ("actual user need",)),
    ("cross-store-erasure", ("CAP-22",), ("multiple stores exist",)),
)


class DeferredError(ValueError):
    pass


def capabilities():
    return [{"id": ident, "status": "DEFERRED", "requirements": list(reqs),
             "unblock_when": list(unblock)}
            for ident, reqs, unblock in CAPABILITIES]


def enable(capability_id, approval=None):
    known = {ident for ident, _, _ in CAPABILITIES}
    if capability_id not in known:
        raise DeferredError("E_DEFERRED_UNKNOWN: %r" % (capability_id,))
    if not isinstance(approval, dict) or not approval.get("approver") \
            or not approval.get("scope"):
        raise DeferredError("E_DEFERRED_APPROVAL: enabling %r needs a written "
                            "approval with approver and scope" % (capability_id,))
    return {"id": capability_id, "status": "ACTIVATION_PENDING",
            "approval": {"approver": approval["approver"], "scope": approval["scope"],
                         "budget": approval.get("budget", "none")},
            "note": "pending backend qualification; not active"}
