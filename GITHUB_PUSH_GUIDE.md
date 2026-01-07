# How to Push to GitHub

## Step-by-Step Instructions

### Option 1: Using GitHub CLI (Recommended - Fastest)

```bash
# Install GitHub CLI if not already installed
# brew install gh  # on macOS

# Authenticate with GitHub
gh auth login

# Create a new repository and push
gh repo create iceberg-hands-on --public --source=. --remote=origin --push
```

### Option 2: Manual Setup (Traditional Method)

#### Step 1: Create a GitHub Repository

1. Go to https://github.com/new
2. Repository name: `iceberg-hands-on` (or your preferred name)
3. Description: "Apache Iceberg hands-on tutorial with Spark, MinIO, and Firebolt"
4. Choose Public or Private
5. **DO NOT** initialize with README, .gitignore, or license (we already have these)
6. Click "Create repository"

#### Step 2: Initialize Git and Push

```bash
# Navigate to your project directory
cd /Users/asimkumarrout/Documents/Firebolt/Python

# Initialize git repository
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: Apache Iceberg hands-on tutorial"

# Add remote repository (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/iceberg-hands-on.git

# Rename branch to main (if needed)
git branch -M main

# Push to GitHub
git push -u origin main
```

#### Step 3: If You Get Authentication Errors

If you see authentication errors, you have a few options:

**Option A: Use Personal Access Token**
1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token with `repo` permissions
3. Use token as password when prompted:
```bash
git push -u origin main
# Username: YOUR_USERNAME
# Password: YOUR_PERSONAL_ACCESS_TOKEN
```

**Option B: Use SSH (Recommended for frequent use)**
```bash
# Generate SSH key if you don't have one
ssh-keygen -t ed25519 -C "your_email@example.com"

# Add SSH key to ssh-agent
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# Copy public key
cat ~/.ssh/id_ed25519.pub
# Copy the output and add it to GitHub: Settings → SSH and GPG keys → New SSH key

# Change remote URL to SSH
git remote set-url origin git@github.com:YOUR_USERNAME/iceberg-hands-on.git

# Push again
git push -u origin main
```

### Option 3: Using the Automated Script

Run the provided script:
```bash
chmod +x push_to_github.sh
./push_to_github.sh
```

## What Gets Pushed

The following files will be pushed to GitHub:
- ✅ README.md (main GitHub page)
- ✅ ICEBERG_HANDSON_README.md (detailed tutorial)
- ✅ docker-compose.yml
- ✅ setup.sh
- ✅ requirements.txt
- ✅ .gitignore
- ✅ scripts/ (all Python scripts)
- ✅ notebooks/ (notebook templates)

The following will be excluded (via .gitignore):
- ❌ data/ (NYC Taxi data - too large)
- ❌ jars/ (downloaded JARs)
- ❌ __pycache__/
- ❌ .env files

## After Pushing

Once pushed, your repository will be available at:
`https://github.com/YOUR_USERNAME/iceberg-hands-on`

The README.md will automatically display as the main page!

## Updating the Repository Later

```bash
# Make your changes
git add .
git commit -m "Description of changes"
git push
```

## Troubleshooting

### Error: "remote origin already exists"
```bash
# Remove existing remote
git remote remove origin
# Add it again with correct URL
git remote add origin https://github.com/YOUR_USERNAME/iceberg-hands-on.git
```

### Error: "failed to push some refs"
```bash
# Pull first, then push
git pull origin main --allow-unrelated-histories
git push -u origin main
```

### Want to push only Iceberg tutorial files?
If you want to create a separate repository just for the Iceberg tutorial:

```bash
# Create a new directory
mkdir ../iceberg-hands-on
cd ../iceberg-hands-on

# Copy only tutorial files
cp ../Python/README.md .
cp ../Python/ICEBERG_HANDSON_README.md .
cp ../Python/docker-compose.yml .
cp ../Python/setup.sh .
cp ../Python/requirements.txt .
cp ../Python/.gitignore .
cp -r ../Python/scripts .
cp -r ../Python/notebooks .

# Then initialize git and push
git init
git add .
git commit -m "Initial commit: Apache Iceberg hands-on tutorial"
git remote add origin https://github.com/YOUR_USERNAME/iceberg-hands-on.git
git push -u origin main
```

