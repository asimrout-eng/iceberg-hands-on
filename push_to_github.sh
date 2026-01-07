#!/bin/bash

# Script to push Apache Iceberg Hands-On Tutorial to GitHub
# Usage: ./push_to_github.sh [repository-name] [github-username]

set -e

REPO_NAME=${1:-"iceberg-hands-on"}
GITHUB_USER=${2:-""}

echo "🚀 Pushing Apache Iceberg Hands-On Tutorial to GitHub"
echo "====================================================="

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Error: Git is not installed. Please install Git first."
    exit 1
fi

# Check if already a git repository
if [ -d ".git" ]; then
    echo "✅ Git repository already initialized"
    if [ -n "$(git remote -v)" ]; then
        echo "📡 Remote repository already configured:"
        git remote -v
        read -p "Do you want to push to existing remote? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git add .
            git commit -m "Update: Apache Iceberg hands-on tutorial" || echo "No changes to commit"
            git push
            echo "✅ Pushed to GitHub!"
            exit 0
        fi
    fi
else
    echo "📦 Initializing git repository..."
    git init
fi

# Get GitHub username if not provided
if [ -z "$GITHUB_USER" ]; then
    if command -v gh &> /dev/null; then
        GITHUB_USER=$(gh api user --jq .login 2>/dev/null || echo "")
    fi
    
    if [ -z "$GITHUB_USER" ]; then
        read -p "Enter your GitHub username: " GITHUB_USER
    fi
fi

echo "👤 GitHub username: $GITHUB_USER"
echo "📁 Repository name: $REPO_NAME"

# Check if GitHub CLI is available
if command -v gh &> /dev/null; then
    echo ""
    echo "🔍 GitHub CLI detected. Using it to create repository..."
    read -p "Create new repository '$REPO_NAME' on GitHub? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Check if authenticated
        if ! gh auth status &> /dev/null; then
            echo "🔐 Please authenticate with GitHub CLI:"
            gh auth login
        fi
        
        # Create repository
        echo "📦 Creating repository on GitHub..."
        gh repo create "$REPO_NAME" --public --source=. --remote=origin --description "Apache Iceberg hands-on tutorial with Spark, MinIO, and Firebolt" || {
            echo "⚠️  Repository might already exist. Continuing..."
        }
    fi
else
    echo ""
    echo "📝 Manual setup required:"
    echo "   1. Go to https://github.com/new"
    echo "   2. Create a repository named: $REPO_NAME"
    echo "   3. DO NOT initialize with README, .gitignore, or license"
    echo "   4. Press Enter when done..."
    read
    
    # Add remote
    echo "🔗 Adding remote repository..."
    git remote add origin "https://github.com/$GITHUB_USER/$REPO_NAME.git" || {
        echo "⚠️  Remote might already exist. Updating..."
        git remote set-url origin "https://github.com/$GITHUB_USER/$REPO_NAME.git"
    }
fi

# Stage all files
echo "📝 Staging files..."
git add .

# Check if there are changes to commit
if git diff --staged --quiet; then
    echo "ℹ️  No changes to commit"
else
    # Create initial commit
    echo "💾 Creating commit..."
    git commit -m "Initial commit: Apache Iceberg hands-on tutorial

- Complete setup with Docker, Spark, MinIO, and JupyterLab
- NYC Yellow Taxi dataset integration
- CRUD operations examples (INSERT, DELETE, SELECT, UPDATE)
- Firebolt.io integration guide
- Automated setup script
- Comprehensive documentation"
fi

# Set branch to main
git branch -M main 2>/dev/null || echo "Already on main branch"

# Push to GitHub
echo "🚀 Pushing to GitHub..."
if git push -u origin main 2>&1 | grep -q "Authentication failed\|fatal: Authentication failed"; then
    echo ""
    echo "❌ Authentication failed!"
    echo ""
    echo "Please set up authentication:"
    echo "   Option 1: Use Personal Access Token"
    echo "   - Go to: https://github.com/settings/tokens"
    echo "   - Generate new token (classic) with 'repo' permissions"
    echo "   - Use token as password when prompted"
    echo ""
    echo "   Option 2: Use SSH"
    echo "   - Run: ssh-keygen -t ed25519 -C 'your_email@example.com'"
    echo "   - Add key to GitHub: https://github.com/settings/keys"
    echo "   - Change remote: git remote set-url origin git@github.com:$GITHUB_USER/$REPO_NAME.git"
    echo ""
    exit 1
fi

echo ""
echo "✅ Successfully pushed to GitHub!"
echo ""
echo "🌐 Your repository is available at:"
echo "   https://github.com/$GITHUB_USER/$REPO_NAME"
echo ""
echo "📚 The README.md will automatically display as the main page!"

