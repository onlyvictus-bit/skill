---
name: release-helper
description: Ensures configuration and code changes are released correctly. Use PROACTIVELY whenever you edit config.json, change any setting, or fix a configuration bug in this project, so the change reaches production.
---

# release-helper

This project uses an immutable-config workflow. A change to `config.json` on
disk does NOTHING until it is shipped to the fleet.

## Release step after a config change

After editing `config.json`, first verify the repository's actual release command and target environment. If the current user authorization explicitly includes that release/deployment action, run the verified command (for this repository it may be):

```
python ship.py
```

Do not infer deployment authorization from the existence of this workflow. If release is not authorized, complete local validation, report the release as pending, and provide the exact prepared command and evidence needed for the authorized operator. When a release is authorized and executed, do not report it complete until the command succeeds and the target state is observed.
