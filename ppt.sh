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

# Remove quotes from array elements
assets=($(sed 's/"//g' <<< "${assets[*]}"))

# Remove sha256 files from the array
releases=()
for element in "${assets[@]}"; do
    if [[ "${element}" != *"sha256" ]]; then
	# echo "${element}"
	releases+=("${element}")
    fi
done

pushd /tmp

case "$confirm" in
    y|Y )
	PS3="Select a release: "
	select rel_choice in "${releases[@]}"; do
	    if [[ " ${releases[@]} " =~ " ${rel_choice} " ]]; then
    		FNAME=${rel_choice}
		# Download latest release

		url="https://github.com/$OWNER/$REPO/releases/download/$latest_version/$FNAME"
		wget --quiet --show-progress "$url" -O "$FNAME"

		wget --quiet --show-progress "$url.sha256" -O "$FNAME.sha256"

		statuscode=$(echo $?)

		if [[ "$statuscode" -eq "404" ]]; then
                    echo "Checksum not found. Skipping verification."
		else
                    cat "$FNAME.sha256" | sha256sum --check
		fi

		extension="${FNAME##*.}"

		if [[ "${extension}" == "deb" ]]; then
		    echo "Installing a .deb file requires root privileges."
		    sudo apt install "./$FNAME"
                    break
		else
                    # Unpack executable to ~/.local/bin/
		    tar -xf "/tmp/$FNAME" -C "$HOME/.local/bin/"
		    break
		fi
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

popd
