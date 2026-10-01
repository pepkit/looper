# pydantic-settings CLI Migration Guide

This document describes CLI incompatibilities discovered when migrating looper from `pydantic-argparse` to `pydantic-settings`, along with decisions for each.

## Background

looper previously used `pydantic-argparse` which only supports pydantic v1 (via `pydantic.v1` shim). This shim breaks on Python 3.14+, and the library is unmaintained. We migrated to `pydantic-settings` which is maintained by the pydantic team and has native CLI support.

---

## 1. Multi-value list arguments require commas

### Issue
With argparse/pydantic-argparse, list arguments supported space-separated values:
```bash
looper run --exc-flag completed running --dry-run
```

pydantic-settings does NOT support this syntax. It treats `running` as an unrecognized positional argument.

### Supported formats in pydantic-settings
```bash
# Comma-separated (recommended)
looper run --exc-flag completed,running --dry-run

# Repeated flags
looper run --exc-flag completed --exc-flag running --dry-run

# JSON
looper run --exc-flag '["completed","running"]' --dry-run
```

### Decision
**Breaking change accepted.** Use comma-separated syntax for multi-value arguments. This is cleaner and more explicit.

### Affected arguments
- `--exc-flag`
- `--sel-flag`
- `--sel-incl`
- `--amend`
- `--compute`
- `--sample-pipeline-interfaces`
- `--project-pipeline-interfaces`

---

## 2. Short flags are case-insensitive

### Issue
argparse treats `-p` and `-P` as distinct options. pydantic-settings treats them as the same (case-insensitive), causing conflicts.

Current conflicting aliases:
- `-p` → `--package`
- `-P` → `--project-pipeline-interfaces`

### Error
```
argparse.ArgumentError: argument -p/--project-pipeline-interfaces: conflicting option string: -p
```

### Options
1. Remove `-P` alias from `--project-pipeline-interfaces`
2. Change `-P` to a different letter (e.g., `-I` for Interfaces)
3. Use multi-character aliases (`--spi`, `--ppi`) instead of single letters

### Decision
**Changed to `--spi` and `--ppi`.** These multi-character aliases are more descriptive and avoid case-sensitivity issues. No single-letter aliases for these arguments.

---

## 3. Short flags require AliasChoices

### Issue
pydantic-settings doesn't automatically create short aliases from field definitions. The `cli_shortcuts` config option exists but conflicts with `cli_implicit_flags`.

### Solution
Use `pydantic.AliasChoices` in Field definitions:
```python
from pydantic import AliasChoices, Field

dry_run: bool = Field(
    default=False,
    validation_alias=AliasChoices('d', 'dry-run'),
    description="Don't actually submit jobs"
)
```

Single-character aliases automatically become short flags (`-d`), multi-character become long flags (`--dry-run`).

### Implementation
Updated `Command.create_model()` in `commands.py` to wire aliases into `AliasChoices` when creating dynamic models.

---

## 4. Boolean flags require cli_implicit_flags

### Issue
By default, pydantic-settings requires explicit values for boolean arguments:
```bash
# Required by default
looper run --dry-run true

# What users expect
looper run --dry-run
```

### Solution
Enable `cli_implicit_flags=True` in `SettingsConfigDict`:
```python
model_config = SettingsConfigDict(
    cli_parse_args=True,
    cli_implicit_flags=True,  # --dry-run works without value
)
```

This creates `--flag` / `--no-flag` pairs for boolean fields.

### Decision
**Enabled.** Preserves expected CLI behavior.

---

## 5. Help text customization

### Issue
pydantic-settings CLI help output exposes implementation details:
- Class docstrings appear as program description
- Type hints show `{bool,null}` for optional fields
- Subcommands have no descriptions by default

### Solution
Configure `SettingsConfigDict` and add Field descriptions:
```python
model_config = SettingsConfigDict(
    cli_parse_args=True,
    cli_hide_none_type=True,  # Hide {bool,null} type hints
)

# Add descriptions for subcommands
run: CliSubCommand[RunModel] = Field(description="Run or submit jobs.")
```

Change class docstring from implementation notes to user-facing description.

### Decision
**Configured.** Clean help output matching argparse style.

---

## Summary of Breaking Changes

| Change | Old Syntax | New Syntax |
|--------|-----------|------------|
| Multi-value lists | `--flag a b c` | `--flag a,b,c` |
| Case-sensitive short flags | `-p` and `-P` distinct | Case-insensitive (conflict) |

## Summary of Preserved Behavior

| Feature | Status |
|---------|--------|
| Long flags (`--dry-run`) | ✓ Works |
| Short flags (`-d`) | ✓ Works (via AliasChoices) |
| Boolean flags without value | ✓ Works (via cli_implicit_flags) |
| Kebab-case (`--dry-run` not `--dry_run`) | ✓ Works (via cli_kebab_case) |
