#!/bin/bash

# Exit on error
set -e

# Build content
uv run scripts/build_content.py

# Build
mise x hugo -- hugo

# Add nofollow to comment links
uv run scripts/postprocess_comments_nofollow.py

# Normalize feed URLs
uv run scripts/postprocess_feed_paths.py public/blog

# Copy special pages
cp public/blog/s-anand/index.html public/
cp -R public/blog/calvin/ public/
cp -R p/ public/

# Ideas for other pages:
#   /p/ is a Medium/WordPress convention
#   /i/ for images, assets
#   /s/ for static / special pages
#   app, pub, doc, try, use, set, hub, lab, box, kit, ...
#   go, at for links
