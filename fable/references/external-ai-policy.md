# External AI policy

Public web research is not an external-AI call. Sending project content to another AI/model/provider is.

Before each external AI call, disclose:

- provider/service;
- purpose of the call;
- exact categories of data to be sent;
- whether secrets, credentials, personal data, proprietary code, or other sensitive material are present;
- approximate payload size;
- expected output and how it will be verified.

Wait for explicit approval for that call. One approval covers one call unless the user explicitly authorizes a named batch/range. Minimize payload to the smallest material excerpt. Never send secrets or credentials. Treat external model output as advice, not evidence, until checked against primary sources, repository state, or direct verification.

If the provider or payload changes materially, request new approval.
