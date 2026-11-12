# fix_plan.json — Operable Fixes

`deltas.json` describes *what is wrong*. `fix_plan.json` describes *what to change*. Write both — deltas for humans reviewing the run, fix_plan for an agent (or human) applying the edits.

## Shape

```json
[
  {
    "file": "src/views/SettingsView.vue",
    "op": "replace",
    "old": "Manage your account, key, and integrations.",
    "new": "Profile, your desktop client key, and integrations.",
    "delta_ref": "typography.copy-drift",
    "confidence": "high"
  },
  {
    "file": "src/components/settings/SettingsSubNav.vue",
    "op": "delete_lines",
    "pattern": "<span v-if=\"it.disabled\" class=\"soon\">Soon</span>",
    "delta_ref": "structure.extra-badge",
    "confidence": "high"
  },
  {
    "file": "src/styles/typography.css",
    "op": "patch",
    "find": ".page-title {\\n  font-weight: 400;",
    "replace": ".page-title {\\n  font-weight: 600;",
    "delta_ref": "typography.weight",
    "confidence": "medium"
  }
]
```

## Operations

|-|-|
| `op` | Meaning |
| `replace` | literal string find-and-replace within `file`. Fails if `old` not found or ambiguous. |
| `delete_lines` | remove any line matching `pattern` (literal substring). |
| `patch` | like replace but explicit `find` / `replace` fields. Preferred for multi-line. |
| `insert_after` | insert `new` immediately after the first line matching `anchor`. |
| `note` | no-op — human-readable note for fixes that require judgment (e.g. "reorganize component tree"). |

## Confidence

|-|-|
| Value | When to use |
| `high` | structure / literal text deltas — the fix is mechanical. |
| `medium` | style value changes where the token mapping is implied but not certain. |
| `low` | subjective calls (iconography, spacing rhythm) — an operator should review. |

## Guidance for the vision analyzer

Emit a fix for every delta where you can name a file and a literal change. Skip deltas where the fix is "refactor this component's structure" — leave those as `op: note` with a description.

Do not emit fixes that delete user-authored features or that change framework-level choices without a note. Structural changes above "add/remove a button" should be `op: note`.
