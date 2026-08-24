# Nautilus Version Policy

```yaml
version: "1.231.0"
channel: released
NO_FLOATING_VERSION: true
NO_NIGHTLY_IN_PRODUCTION: true
NO_AUTO_MAJOR_UPGRADE: true
```

Source of truth: `config/nautilus-version.yaml`

Upgrade only via `NAUTILUS_UPGRADE_GATE` after full test pyramid PASS.
