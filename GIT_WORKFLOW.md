# Git Workflow - How to Push Files

## Standard Git Workflow

### Step 1: Check Status
See what files have changed:
```bash
git status
```

### Step 2: Add Files
Add files you want to commit:

```bash
# Add specific file
git add filename.py

# Add all files in current directory
git add .

# Add all files matching a pattern
git add *.py

# Add a directory
git add scripts/
```

### Step 3: Commit Changes
Create a commit with a descriptive message:
```bash
git commit -m "Description of what you changed"
```

Good commit messages:
- `git commit -m "Add Firebolt connection script"`
- `git commit -m "Update README with setup instructions"`
- `git commit -m "Fix docker-compose configuration"`

### Step 4: Push to GitHub
Push your commits to GitHub:
```bash
git push
```

If it's the first push for a branch:
```bash
git push -u origin main
```

## Complete Example

```bash
# 1. Check what changed
git status

# 2. Add files
git add .

# 3. Commit
git commit -m "Add new feature: Iceberg time travel queries"

# 4. Push
git push
```

## Quick Commands Reference

```bash
# See what changed
git status

# See detailed changes
git diff

# Add all changes
git add .

# Commit with message
git commit -m "Your message here"

# Push to GitHub
git push

# Pull latest changes from GitHub
git pull

# See commit history
git log --oneline

# See what branch you're on
git branch
```

## Common Scenarios

### Scenario 1: You modified existing files
```bash
git add .
git commit -m "Update documentation"
git push
```

### Scenario 2: You created new files
```bash
git add new_file.py
git commit -m "Add new script for data processing"
git push
```

### Scenario 3: You want to see changes before committing
```bash
# See what changed
git diff

# See what's staged
git diff --staged

# Then commit
git commit -m "Your message"
git push
```

### Scenario 4: You made a mistake in last commit message
```bash
git commit --amend -m "Corrected message"
git push --force-with-lease
```

### Scenario 5: You want to undo changes to a file
```bash
# Undo changes to a file (before committing)
git checkout -- filename.py

# Or restore (newer Git versions)
git restore filename.py
```

## Best Practices

1. **Commit often** - Small, frequent commits are better than large ones
2. **Write clear messages** - Describe what and why, not how
3. **Check status first** - Always run `git status` before committing
4. **Pull before push** - If working with others: `git pull` then `git push`
5. **Don't commit sensitive data** - Check `.gitignore` is working

## Troubleshooting

### Error: "Your branch is ahead of origin/main"
```bash
# Just push it
git push
```

### Error: "Updates were rejected"
```bash
# Pull latest changes first
git pull

# Resolve any conflicts, then
git push
```

### Error: "Nothing to commit"
- No changes detected
- Check `git status` to see if files are already committed
- Make sure you've saved your file changes

### Want to see what will be pushed?
```bash
git log origin/main..HEAD
```

