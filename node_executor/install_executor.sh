#!/bin/bash

# Function to check if bun is installed
check_bun_installed() {
    if ! command -v bun &> /dev/null
    then
        echo "bun not found. Installing bun..."
        curl -fsSL https://bun.sh/install | bash
        source ~/.bashrc  # Reload bash profile
    fi
}

# Step 0: Check if bun is installed
check_bun_installed

# Step 1: Install bun dependencies
echo "Installing dependencies..."
bun install

# Step 2: Create the binary file  using bun
echo "Create an binary file"
bun build src/cli.ts --compile --outfile node_executor 

echo "Binary created successfully."

