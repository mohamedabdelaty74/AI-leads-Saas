#!/bin/bash

# Elite Creatif Frontend - Quick Installation Script
# Run this script to set up your frontend in one command

echo "🚀 Elite Creatif Frontend Setup"
echo "================================"
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    echo "   Visit: https://nodejs.org"
    exit 1
fi

# Check Node version
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "❌ Node.js version 18+ required. Current version: $(node -v)"
    echo "   Please upgrade Node.js"
    exit 1
fi

echo "✅ Node.js $(node -v) detected"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
npm install

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✅ Dependencies installed"
echo ""

# Create .env.local if it doesn't exist
if [ ! -f .env.local ]; then
    echo "📝 Creating .env.local file..."
    cp .env.local.example .env.local
    echo "✅ .env.local created"
else
    echo "ℹ️  .env.local already exists"
fi

echo ""
echo "✨ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Ensure your backend is running on http://localhost:8000"
echo "2. Run 'npm run dev' to start the development server"
echo "3. Open http://localhost:3000 in your browser"
echo ""
echo "📚 Documentation:"
echo "- README.md - Complete documentation"
echo "- SETUP.md - Quick start guide"
echo "- COMPONENTS.md - Component reference"
echo "- COMPLETE-GUIDE.md - Full implementation guide"
echo "- FEATURES-SHOWCASE.md - Visual feature guide"
echo ""
echo "🎉 Happy coding!"
