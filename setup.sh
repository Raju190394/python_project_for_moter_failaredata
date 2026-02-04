#!/bin/bash

echo "======================================================"
echo "   Industrial Reliability Dashboard - Auto Setup"
echo "======================================================"
echo ""

# 1. Check for Python
if ! command -v python3 &> /dev/null
then
    echo "[ERROR] Python3 could not be found. Please install it."
    exit
fi

echo "[1/3] Python detected."

# 2. Install dependencies
echo "[2/3] Installing dependencies..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

# 3. Run the application
echo "[3/3] Launching Dashboard..."
python3 -m streamlit run app.py
