# Safety Rules

## Preview First

Always preview when P4 supports it:

```text
p4 sync -n
p4 reconcile -n -a -e
```

Bundled scripts default to previews for supported mutating operations and require `--apply` before running a real mutation.

## Mutating Commands

These require explicit approval and `--apply` in the wrapper:

```text
sync
edit
add
reconcile
submit
```

Submit also requires a changelist and description.

## Blocked Commands

Never automate:

```text
p4 clean
p4 delete
p4 move
p4 reconcile -d
p4 reconcile -w
p4 revert
p4 revert -w
p4 obliterate
typemap edits
binary conflict resolution
```

`p4 delete` does not obliterate history, but H5G never-delete policy still avoids delete-style operations. Write over/update to a new version instead of deleting or moving depot paths.

## Binary Art

Prefer typemap-managed exclusive locking (`+l`) for merge-impossible binary assets such as PSD, Spine binaries, videos, packed textures, audio masters, and project files. Typemap changes are admin-only and must not be scripted by this plugin.

Use `p4 opened -as` to see who has files open before editing binary art.

## GLOBAL Changes

Treat `ASSETS/GLOBAL` and `//webgamedev/assets/_Common-New/` as shared common assets. Review owners, affected games, QA needs, file size, and override behavior before submit.
