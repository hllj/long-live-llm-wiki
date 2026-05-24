---
branch_pattern: "NNN-slug"
commit_format: "conventional"
allowed_types:
  - feat
  - fix
  - chore
  - docs
  - refactor
special_rules:
  - doc_first_commit
  - no_force_push_master
  - coauthor_trailer_required
---

# Git Convention

## Branch naming

```
NNN-slug
```

- `NNN` — zero-padded spec number (e.g. `001`, `012`)
- `slug` — kebab-case feature name derived from the spec slug

Examples:
- `001-wiki-gap-research`
- `002-new-feature`

## Commit format

[Conventional Commits](https://www.conventionalcommits.org/) — `type(scope): description`

```
type(scope): short imperative description

Optional body.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```

**Allowed types:** `feat`, `fix`, `chore`, `docs`, `refactor`

## Special rules

1. **Doc-first commit** — the first commit on any feature branch must include the spec, plan, and/or tasks docs (not implementation files alone).
2. **No force-push to master** — `git push --force` to `master` is forbidden.
3. **Co-author trailer required** — every commit must include the `Co-Authored-By` trailer.
