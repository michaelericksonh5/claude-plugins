# Perforce Artist Workflows

Helix Core is currently branded as P4 in product docs; the command remains `p4`.

## Setup Checks

Confirm the environment before changing files:

```text
p4 set
p4 info
p4 login -s
p4 client -o
```

Expected setup includes `P4PORT`, `P4USER`, `P4CLIENT`, `P4CONFIG`, a valid `p4 login`, and a workspace view that maps the needed `//webgamedev/...` paths.

## Read-Only Diagnostics

These commands are safe diagnostics:

```text
p4 info
p4 set
p4 login -s
p4 client -o
p4 opened
p4 opened -as
p4 status
p4 reconcile -n -a -e
p4 sync -n
p4 diff -sa
p4 where
p4 have
p4 files
p4 changes
p4 describe
p4 filelog
p4 fstat
p4 print
```

Use `p4 opened -as` before editing binary art to see who else has files open.

## Sync

Use this when the user says update, sync, syncing, synching, or get latest.

Preview first:

```text
p4 sync -n //webgamedev/<gamefolder>/...
```

Apply only after review:

```text
p4 sync //webgamedev/<gamefolder>/...
```

## Edit Existing Files

Check locks/opened files first for binary assets:

```text
p4 opened -as //webgamedev/<gamefolder>/texture/portrait/symbols/hp1.webp
p4 edit //webgamedev/<gamefolder>/texture/portrait/symbols/hp1.webp
```

## Add New Files

Place files in the correct GameForge path, then add:

```text
p4 add //webgamedev/<gamefolder>/texture/portrait/symbols/hp1.webp
```

## Reconcile Local Changes

Preview first:

```text
p4 reconcile -n -a -e //webgamedev/<gamefolder>/...
```

Apply only after checking the preview:

```text
p4 reconcile -a -e //webgamedev/<gamefolder>/...
```

Never automate default `p4 reconcile`, `p4 reconcile -d`, or `p4 reconcile -w`; they can open delete behavior.

## Never-Delete Policy

Write over/update to a new version when content changes. Do not automate deletion-style operations:

```text
p4 delete
p4 move
p4 revert
```

`p4 delete` creates a delete revision but does not obliterate older revisions. H5G policy still avoids delete-style operations so teams can go backward with nothing lost. Never automate `p4 revert -w`; reverting discards pending local work.

## Submit

Use this when the user says check in, checking in, submit, push updates, or pushing updates. Perforce submits changelists; it does not use Git-style push.

Before submitting:

```text
p4 opened
p4 diff -sa
p4 changes -m 10 //webgamedev/<gamefolder>/...
```

Submit with a changelist and clear description:

```text
p4 submit -c <change> -d "Description"
```

For `GLOBAL` / `_Common-New` changes, confirm cross-game impact, ownership, and QA expectations before submit.

## History and Review

Use these to answer what changed and why:

```text
p4 filelog filePath
p4 changes filePath
p4 fstat filePath
p4 diff -sa filePath
```

Resolve conflicts deliberately. Do not automate binary conflict resolution.
