# Language and Theme Editor Contract — MCW Launcher 1.0.1

This document defines the source files that a future MCW translation and theme editor may read and write.

## Language packs

Built-in language packs live in:

```text
lang/en-US.json
lang/vi-VN.json
```

Each pack has three top-level objects:

```json
{
  "meta": {
    "locale": "vi-VN",
    "name": "Tiếng Việt"
  },
  "translations": {
    "navigation.instances": "Instance",
    "navigation.launcher_settings": "Cài đặt launcher"
  },
  "aliases": {}
}
```

### Stable rules

1. Application code should store semantic keys such as `navigation.launcher_settings`, not rendered English text.
2. Every built-in locale must contain the same translation keys.
3. Placeholder names must match between locales.
4. Translation values must be non-empty strings.
5. `aliases` exist only for compatibility with older source strings. New UI code should not depend on aliases.
6. `Instance` is intentionally preserved as a product/domain term, but it still uses `navigation.instances`.
7. Language changes are persisted immediately and applied after restarting MCW Launcher.

The release preflight validates navigation keys, parity, placeholders, and required Vietnamese labels.

## Theme manifests

Theme manifests live under:

```text
themes/<theme-id>/theme.json
```

The frozen schema and generated runtime contract live under:

```text
docs/schema/theme.schema.v6.json
docs/schema/theme-asset-catalog.v1.json
docs/schema/theme-runtime-contract.v1.json
```

A theme editor should validate against the frozen schema, preserve unknown compatible fields, and never write paths outside the selected theme directory.

## Recommended editor workflow

1. Load the English pack as the canonical key catalog.
2. Compare all other locales against that catalog.
3. Show placeholder mismatches before saving.
4. Save language JSON as UTF-8.
5. Validate theme manifests against the exported schema.
6. Run `python -m tools.release_preflight` before publishing a pack or launcher release.
