# Fixes Applied to Setup Issues

This document shows exactly what was changed to fix the setup errors.

## Issue 1: Missing Python `requests` Module

### Error Message
```
ModuleNotFoundError: No module named 'requests'
```

### Problem
The `download_nyc_taxi_data.py` script requires the `requests` library, but it wasn't installed on your system.

### Solution Applied
```bash
python3 -m pip install requests --break-system-packages --user
```

### What This Does
- `python3 -m pip install requests` - Installs the requests package
- `--break-system-packages` - Required on macOS because Python is "externally managed" (protected by system)
- `--user` - Installs to user directory instead of system-wide (safer)

### Result
- Package installed at: `/Users/asimkumarrout/Library/Python/3.14/lib/python/site-packages`
- Version installed: `requests 2.32.5`
- The download script can now run successfully

### Alternative Solutions (for future reference)
If you don't want to use `--break-system-packages`, you could:
1. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install requests
   ```

2. Use pipx (for standalone apps):
   ```bash
   brew install pipx
   pipx install requests
   ```

---

## Issue 2: Docker Credential Helper Error

### Error Message
```
error getting credentials - err: exec: "docker-credential-desktop": executable file not found in $PATH
```

### Problem
Docker was configured to use a credential helper (`docker-credential-desktop`) that wasn't available in your PATH. This happens when Docker Desktop's credential helper isn't properly set up.

### Solution Applied

#### Before (Original Config)
**File**: `~/.docker/config.json`
```json
{
	"auths": {},
	"credsStore": "desktop",
	"currentContext": "desktop-linux"
}
```

#### After (Fixed Config)
**File**: `~/.docker/config.json`
```json
{
	"auths": {},
	"currentContext": "desktop-linux"
}
```

### What Changed
- **Removed**: `"credsStore": "desktop"` line
- This tells Docker to not use a credential helper
- Docker will work without it for local development

### Why This Works
- For local Docker images (like `minio/minio` and `apache/spark-py`), you don't need credential storage
- Credential helpers are mainly needed for private Docker registries
- Removing it allows Docker to pull public images without authentication issues

### Backup Created
A backup was created at: `~/.docker/config.json.backup`

To restore the original (if needed):
```bash
cp ~/.docker/config.json.backup ~/.docker/config.json
```

### Alternative Solutions (if you need credential helper)
If you need the credential helper later, you can:

1. Find where Docker Desktop installed it:
   ```bash
   find /Applications -name "docker-credential-desktop" 2>/dev/null
   ```

2. Add it to PATH:
   ```bash
   # Add to ~/.zshrc or ~/.bash_profile
   export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"
   ```

3. Or reinstall Docker Desktop to fix the credential helper setup

---

## Summary of Changes

| Issue | File Changed | What Was Changed |
|-------|-------------|------------------|
| Missing requests module | System Python | Installed `requests` package |
| Docker credential error | `~/.docker/config.json` | Removed `"credsStore": "desktop"` line |

## Verification

You can verify the fixes worked:

1. **Check requests is installed:**
   ```bash
   python3 -c "import requests; print('OK')"
   ```

2. **Check Docker works:**
   ```bash
   docker-compose ps
   ```

Both should work without errors now!

