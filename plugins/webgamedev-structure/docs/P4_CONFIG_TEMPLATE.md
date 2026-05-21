# P4 Config Template

Create a `.p4config` or project-specific config file in the workspace root if your team uses `P4CONFIG`.

```text
P4PORT=perforce.example.com:1666
P4USER=your.username
P4CLIENT=your_workspace_name
```

Then set the config filename once:

```powershell
p4 set P4CONFIG=.p4config
```

Verify:

```powershell
p4 set
p4 info
p4 login -s
p4 client -o
```

Do not commit personal credentials or tickets. `p4 login` stores authentication through P4's normal ticket mechanism.
