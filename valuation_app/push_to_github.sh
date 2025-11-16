#!/bin/bash
# Script to push Business Valuation App to GitHub

echo "🚀 GitHub Push Helper Script"
echo "=============================="
echo ""

# Check if git is initialized
if [ ! -d .git ]; then
    echo "❌ Error: Not a git repository. Run 'git init' first."
    exit 1
fi

# Get GitHub username
echo "Enter your GitHub username:"
read -r github_username

if [ -z "$github_username" ]; then
    echo "❌ Error: Username cannot be empty"
    exit 1
fi

# Get repository name
echo ""
echo "Enter repository name (default: business-valuation-app):"
read -r repo_name

if [ -z "$repo_name" ]; then
    repo_name="business-valuation-app"
fi

# Ask for visibility
echo ""
echo "Repository visibility:"
echo "  1) Private (recommended)"
echo "  2) Public"
read -r visibility_choice

if [ "$visibility_choice" = "2" ]; then
    visibility="--public"
else
    visibility="--private"
fi

echo ""
echo "📋 Summary:"
echo "  GitHub User: $github_username"
echo "  Repository: $repo_name"
echo "  Visibility: ${visibility/--/}"
echo ""

# Check if GitHub CLI is installed
if command -v gh &> /dev/null; then
    echo "✅ GitHub CLI detected"
    echo ""
    echo "Do you want to use GitHub CLI to create and push? (y/n)"
    read -r use_gh_cli
    
    if [ "$use_gh_cli" = "y" ]; then
        echo ""
        echo "Creating repository and pushing with GitHub CLI..."
        gh repo create "$repo_name" $visibility --source=. --push
        
        if [ $? -eq 0 ]; then
            echo ""
            echo "✅ Success! Your repository is now on GitHub:"
            echo "   https://github.com/$github_username/$repo_name"
        else
            echo ""
            echo "❌ Failed to create repository. You may need to:"
            echo "   1. Login: gh auth login"
            echo "   2. Check if repository already exists"
        fi
        exit 0
    fi
fi

# Manual push instructions
echo ""
echo "📝 Manual Push Instructions:"
echo "=============================="
echo ""
echo "1️⃣  Create a new repository on GitHub:"
echo "   → Go to: https://github.com/new"
echo "   → Repository name: $repo_name"
echo "   → Visibility: ${visibility/--/}"
echo "   → DO NOT initialize with README, .gitignore, or license"
echo ""
echo "2️⃣  Then run these commands:"
echo ""
echo "   cd /workspace/valuation_app"
echo "   git remote add origin https://github.com/$github_username/$repo_name.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "3️⃣  If you prefer SSH:"
echo ""
echo "   git remote add origin git@github.com:$github_username/$repo_name.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "=============================="
echo ""
echo "💡 Tips:"
echo "   - Use a Personal Access Token if prompted for password"
echo "   - Generate token at: https://github.com/settings/tokens"
echo "   - Select 'repo' scope when creating token"
echo ""
echo "📚 For more details, see GITHUB_UPLOAD_GUIDE.md"
echo ""

# Ask if user wants to try pushing now
echo "Do you want to try pushing now? (y/n)"
read -r push_now

if [ "$push_now" = "y" ]; then
    echo ""
    echo "Adding remote..."
    git remote add origin "https://github.com/$github_username/$repo_name.git" 2>/dev/null
    
    if [ $? -ne 0 ]; then
        echo "⚠️  Remote 'origin' already exists. Updating..."
        git remote set-url origin "https://github.com/$github_username/$repo_name.git"
    fi
    
    echo "Setting branch to main..."
    git branch -M main
    
    echo ""
    echo "Pushing to GitHub..."
    echo "⚠️  You may be prompted for credentials."
    echo ""
    
    git push -u origin main
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Success! Your repository is now on GitHub:"
        echo "   https://github.com/$github_username/$repo_name"
    else
        echo ""
        echo "❌ Push failed. Common issues:"
        echo "   1. Repository doesn't exist on GitHub yet"
        echo "   2. Authentication failed (use Personal Access Token)"
        echo "   3. No write access to repository"
        echo ""
        echo "Create the repository on GitHub first, then try again."
    fi
else
    echo ""
    echo "✅ Setup complete! You can push manually when ready."
fi

echo ""
echo "🎉 Done!"
