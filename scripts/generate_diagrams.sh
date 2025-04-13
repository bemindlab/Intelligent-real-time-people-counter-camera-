#!/bin/bash
# Script to generate SVG diagrams from D2 files

# Check if d2 is installed
if ! command -v d2 &> /dev/null; then
    echo "Error: d2 is not installed."
    echo "Please install d2 first:"
    echo "  - macOS: brew install d2"
    echo "  - Linux: curl -fsSL https://d2lang.com/install.sh | sh -"
    echo "  - Windows (via Scoop): scoop install d2"
    exit 1
fi

D2_DIR="../docs/d2"
OUTPUT_DIR="../docs/d2"

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Navigate to the script directory
cd "$(dirname "$0")"

# Generate SVG files for all D2 files
echo "Generating SVG diagrams from D2 files..."
for d2_file in "$D2_DIR"/*.d2; do
    if [ -f "$d2_file" ]; then
        filename=$(basename "$d2_file")
        svg_filename="${filename%.d2}.svg"
        echo "Processing: $filename"
        d2 "$d2_file" "$OUTPUT_DIR/$svg_filename"
        echo "Created: $svg_filename"
    fi
done

echo "All diagrams generated successfully."
echo "SVG files are available in: $OUTPUT_DIR"