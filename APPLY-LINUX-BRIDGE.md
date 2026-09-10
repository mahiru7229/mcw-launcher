# Apply MCW Update Bridge v1.2.0

Copy these files into the root of the `mcw-launcher` repository, preserving paths.

Then run:

```bash
git add .
git commit -m "fix(recovery): add Linux update bridge"
git push
```

Run the workflow:

`Actions -> Build MCW Update Bridge -> Run workflow`

Keep the target pinned to `v1.5.1-beta.3`.

Expected assets:

```text
MCW-Update-Bridge-v1.2.0-windows-x64.exe
MCW-Update-Bridge-v1.2.0-windows-x64.exe.sha256
MCW-Update-Bridge-v1.2.0-linux-x64
MCW-Update-Bridge-v1.2.0-linux-x64.sha256
```

Linux smoke test:

```bash
chmod +x MCW-Update-Bridge-v1.2.0-linux-x64
./MCW-Update-Bridge-v1.2.0-linux-x64 --cli --install-dir /path/to/MCW-Launcher
```
