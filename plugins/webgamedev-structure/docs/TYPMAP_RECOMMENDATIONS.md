# Typemap Recommendations

Typemap changes are admin-only. This plugin does not edit typemaps or run typemap commands.

For merge-impossible binary art, teams should prefer exclusive locking (`+l`) so only one user edits the file at a time. Candidate file families include:

- Photoshop and image source files: `.psd`, `.psb`, `.ai`.
- After Effects, Cinema 4D, Maya, and Unity project files.
- Spine binary/project files where text merge is not supported by the team workflow.
- Video masters and runtime video: `.mov`, `.mp4`, `.webm`, `.avi`.
- Audio masters and compressed runtime audio: `.wav`, `.m4a`, `.opus`.
- Packed texture pages and binary texture outputs.

Before editing binary art, run:

```powershell
p4 opened -as <file-or-folder>
```

If a needed binary type is not locked, raise it with the Perforce admin or pipeline owner rather than changing typemap locally.
