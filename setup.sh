#!/bin/bash
# NeuralAudit Quick Start Script
# This script helps you get started with NeuralAudit in minutes

set -e

echo "============================================"
echo "🚀 NeuralAudit Quick Start Setup"
echo "============================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Check Python
echo -e "${BLUE}Step 1: Checking Python installation...${NC}"
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8+"
    exit 1
fi
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"
echo ""

# Step 2: Create virtual environment
echo -e "${BLUE}Step 2: Creating virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
fi
echo ""

# Step 3: Activate virtual environment
echo -e "${BLUE}Step 3: Activating virtual environment...${NC}"
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"
echo ""

# Step 4: Install dependencies
echo -e "${BLUE}Step 4: Installing dependencies...${NC}"
pip install --upgrade pip setuptools wheel > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Step 5: Setup configuration
echo -e "${BLUE}Step 5: Setting up configuration...${NC}"
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${GREEN}✓ Configuration file created (.env)${NC}"
    echo -e "${YELLOW}  Note: Review .env file for customization${NC}"
else
    echo -e "${GREEN}✓ Configuration file already exists${NC}"
fi
echo ""

# Step 6: Create necessary directories
echo -e "${BLUE}Step 6: Creating directories...${NC}"
mkdir -p logs models data screenshots results
echo -e "${GREEN}✓ Directories created${NC}"
echo ""

# Step 7: Verify installation
echo -e "${BLUE}Step 7: Verifying installation...${NC}"
python3 -c "
import config
import logger
import scraper
import preprocessing
import model
import auditor
import database
import pipeline
print('✓ All modules imported successfully')
" || {
    echo "❌ Module import failed. Please check installation."
    exit 1
}
echo -e "${GREEN}✓ Installation verified${NC}"
echo ""

# Step 8: Display quick usage
echo "============================================"
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo "============================================"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo ""
echo "1. Review configuration:"
echo "   nano .env"
echo ""
echo "2. Run tests (optional):"
echo "   python integration_tests.py"
echo ""
echo "3. Try examples:"
echo "   python examples.py"
echo ""
echo "4. Process a product:"
echo "   python main.py --product 'https://example.com/product'"
echo ""
echo "5. Start API server:"
echo "   python main.py --api"
echo "   Then visit: http://localhost:8000/docs"
echo ""
echo "6. Process batch from CSV:"
echo "   python main.py --csv products.csv"
echo ""
echo -e "${YELLOW}Documentation:${NC}"
echo "  - USAGE.md: User guide"
echo "  - IMPLEMENTATION.md: Detailed setup"
echo "  - README.md: Project overview"
echo ""
echo "============================================"
