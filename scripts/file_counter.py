import os
from pathlib import Path
from collections import defaultdict

DESCRIPTION = "Count files by extension in current directory"


def main():
    current_dir = Path.cwd()
    file_counts = defaultdict(int)
    total_files = 0
    
    print(f"Counting files in: {current_dir}")
    print("=" * 50)
    
    for item in current_dir.iterdir():
        if item.is_file():
            extension = item.suffix.lower() if item.suffix else "no extension"
            file_counts[extension] += 1
            total_files += 1
    
    if file_counts:
        print("File counts by extension:")
        for ext, count in sorted(file_counts.items()):
            print(f"  {ext}: {count} files")
        print("=" * 50)
        print(f"Total files: {total_files}")
    else:
        print("No files found in the current directory.")