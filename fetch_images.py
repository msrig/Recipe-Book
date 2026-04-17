#!/usr/bin/env python3
"""Fetch recipe images from Unsplash API and save locally."""

import urllib.request
import urllib.error
import os
from pathlib import Path

# Recipe search queries mapped to file names
RECIPES = {
    "recipe1.jpg": "Russian fermented vegetables salad",
    "recipe2.jpg": "Russian green sorrel soup",
    "recipe3.jpg": "Caesar salad with chicken",
    "recipe4.jpg": "Russian thin pancakes",
    "recipe5.jpg": "Chicken noodle soup",
    "recipe6.jpg": "Chocolate layer cake"
}

def download_image(url: str, filename: str, images_dir: str = "images") -> bool:
    """Download image from URL and save to local file."""
    try:
        filepath = os.path.join(images_dir, filename)
        # Add user agent to avoid being blocked
        request = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            with open(filepath, 'wb') as f:
                f.write(response.read())

        file_size = os.path.getsize(filepath) / 1024
        print(f"✓ Downloaded: {filename} ({file_size:.1f} KB)")
        return True
    except Exception as e:
        print(f"✗ Failed to download {filename}: {e}")
        return False

def main():
    """Main function to fetch all recipe images."""
    images_dir = "images"
    Path(images_dir).mkdir(exist_ok=True)

    print("Fetching recipe images from Unsplash...\n")

    for filename, query in RECIPES.items():
        print(f"Fetching: {query}")
        # Use Unsplash's free image service
        keywords = query.replace(" ", ",")
        url = f"https://source.unsplash.com/600x400/?{keywords}"
        download_image(url, filename, images_dir)
        print()

    print("Done! Images saved to 'images/' directory")

if __name__ == "__main__":
    main()
