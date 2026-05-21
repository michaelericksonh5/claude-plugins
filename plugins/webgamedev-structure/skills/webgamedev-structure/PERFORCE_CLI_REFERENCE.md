# Perforce CLI Reference

Helix Core is branded as P4 in current docs; the command-line tool remains `p4`.

## Setup, Login, and Workspace

Use read-only checks before planning any file work:

```text
p4 set
p4 info
p4 login -s
p4 client -o
p4 where //webgamedev/<gamefolder>/...
p4 have //webgamedev/<gamefolder>/...
```

Confirm `P4PORT`, `P4USER`, `P4CLIENT`, `P4CONFIG`, login status, and that the workspace view maps the needed `//webgamedev/...` paths.

## Sync and Update

Preview latest-file updates before applying them:

```text
p4 sync -n //webgamedev/<gamefolder>/...
p4 sync //webgamedev/<gamefolder>/...
```

## Edit and Checkout

Check binary ownership, then open existing files for edit:

```text
p4 opened -as //webgamedev/<gamefolder>/texture/portrait/symbols/hp1.webp
p4 edit //webgamedev/<gamefolder>/texture/portrait/symbols/hp1.webp
```

## Add New Files

Place new runtime assets in the approved GameForge destination, then add explicit targets:

```text
p4 add //webgamedev/<gamefolder>/texture/portrait/symbols/hp1.webp
```

## Reconcile Add/Edit Only

Never use default `p4 reconcile` automation for GameForge assets because default reconcile behavior can open deletes. Preview and apply add/edit detection only:

```text
p4 reconcile -n -a -e //webgamedev/<gamefolder>/...
p4 reconcile -a -e //webgamedev/<gamefolder>/...
```

## Status, Review, and History

Use these read-only commands to inspect pending work and depot history:

```text
p4 status //webgamedev/<gamefolder>/...
p4 opened
p4 opened -as //webgamedev/<gamefolder>/...
p4 diff -sa //webgamedev/<gamefolder>/...
p4 files //webgamedev/<gamefolder>/...
p4 changes -m 10 //webgamedev/<gamefolder>/...
p4 describe <change>
p4 filelog //webgamedev/<gamefolder>/texture/portrait/symbols/hp1.webp
p4 fstat //webgamedev/<gamefolder>/texture/portrait/symbols/hp1.webp
p4 print //webgamedev/<gamefolder>/texture/portrait/symbols/hp1.webp
```

## Submit and Check In

Perforce submits reviewed changelists; it does not use Git-style push. There is no general `p4 submit` dry run, so preflight with status/opened/diff/change review before submitting:

```text
p4 opened
p4 diff -sa
p4 changes -m 10 //webgamedev/<gamefolder>/...
p4 submit -c <change> -d "Description"
```

For `GLOBAL` / `_Common-New` changes, confirm cross-game ownership and QA expectations first.

## Revision History and Rollback

To inspect or recover old content without deleting history, read or sync an older revision:

```text
p4 filelog filePath
p4 print filePath#3
p4 sync filePath#3
p4 sync filePath#head
```

If an old revision should become the new current content, write it over the working file, open the file for edit, and submit a new revision. Keep history intact.

## Blocked and No-Delete Commands

H5G never-delete policy avoids deletion-style operations even when Perforce preserves history. `p4 delete` creates a delete revision but does not obliterate old file revisions; `p4 move` preserves integration history but leaves the predecessor deleted at head. The plugin still does not automate either operation.

Do not automate:

```text
p4 delete
p4 move
p4 obliterate
p4 reconcile -d
p4 reconcile -w
p4 clean
p4 revert
p4 revert -w
p4 resolve
typemap edits
binary conflict resolution
```

`p4 obliterate` permanently removes history and is never appropriate for this skill.

## Command Coverage

This skill knows the P4 CLI command families artists normally need: setup/login/workspace mapping, update/sync, checkout/edit, add, reconcile, status/opened, diff/review, changelist/submit, history, revision inspection, and blocked destructive/admin commands. For an unlisted P4 command, stop and check the current Perforce command reference before advising or scripting it.
