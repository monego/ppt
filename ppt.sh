#!/bin/bash

# Variables
OWNER="$1"
REPO="$2"
API_URL="https://api.github.com/repos/$OWNER/$REPO/releases/latest"

# Make a GET request to the GitHub API to retrieve the latest release information
response=$(curl -s "$API_URL")

# Extract useful information using jq
latest_version=$(echo "$response" | jq -r '.tag_name')
release_date=$(echo "$response" | jq -r '.published_at')
formatted_date=$(date --date="$release_date" +"%Y-%m-%d")

read -p "The latest version is $latest_version and it was released on $formatted_date. Install? (y/n) " confirm

assets=($(echo "$response" | jq '.assets[].name'))

case "$confirm" in
  y|Y )
      PS3="Select a release: "
      select rel_choice in "${assets[@]}"; do
	  if [[ " ${assets[@]} " =~ " ${rel_choice} " ]]; then
    	      FNAME=${rel_choice:1:-1} # Workaround to remove strings from URL
	      # Download latest release
	      url="https://github.com/$OWNER/$REPO/releases/download/$latest_version/$FNAME"
	      wget "$url" -O "/tmp/$FNAME"
	      # Unpack executable to ~/.local/bin/
	      tar -zxf "/tmp/$FNAME" -C "$HOME/.local/bin/"
	      break
	  else
	      echo "Invalid selection. Exiting..."
	      exit 1
	  fi
      done
      ;;
  n|N )
      echo "Operation canceled. Exiting..."
      ;;
  * )
      echo "Invalid choice. Exiting..."
      ;;
esac
