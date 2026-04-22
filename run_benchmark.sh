#!/bin/bash

# Sentinel Inference System - Benchmark Execution Script
# This script runs the benchmark suite and optionally converts the report to Word format

set -e

BASE_DIR="/home/i_deed/Desktop/sentinel-files/ultralytics_v1"
cd "$BASE_DIR"

echo "=========================================="
echo "Sentinel Inference System - Benchmark Suite"
echo "=========================================="
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Check if psutil is installed
if ! python3 -c "import psutil" 2>/dev/null; then
    echo "Installing required dependencies..."
    pip3 install psutil
fi

# Run the benchmark suite
echo "Running benchmark suite..."
echo ""
python3 benchmark_suite.py

echo ""
echo "=========================================="
echo "Benchmark execution completed!"
echo "=========================================="
echo ""

# Check if pandoc is available for Word conversion
if command -v pandoc &> /dev/null; then
    echo "Pandoc found - Converting latest report to Word format..."
    
    # Find the latest markdown report
    LATEST_MD=$(ls -t benchmark_results/benchmark_report_*.md 2>/dev/null | head -1)
    
    if [ -n "$LATEST_MD" ]; then
        OUTPUT_DOCX="${LATEST_MD%.md}.docx"
        pandoc "$LATEST_MD" -o "$OUTPUT_DOCX"
        echo "Word document created: $OUTPUT_DOCX"
    else
        echo "No markdown report found to convert"
    fi
else
    echo "Pandoc not found - Skipping Word conversion"
    echo "To install pandoc: sudo apt-get install pandoc"
    echo "Or manually copy the markdown content to Word"
fi

echo ""
echo "Results available in: benchmark_results/"
echo "Research report: benchmark_research_report.md"
echo ""
