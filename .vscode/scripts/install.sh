#!/bin/bash

# Color codes
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No color

docker_dir=".vscode/docker" # docker-compose.yml directory
env_dir="." # .env directory
export USER_ID=$(id -u)
export GROUP_ID=$(id -g)

echo -e "${Yellow}Current directory: $(pwd)${NC}"
echo -e "${Yellow}Using USER_ID=${USER_ID} and GROUP_ID=${GROUP_ID} for Docker containers.${NC}"

# Default behavior
BUILD=true

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-build)
            BUILD=false
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Check if .env file exists
check_dot_env() {
    if [ ! -f "${env_dir}/.env" ]; then
        cp "${docker_dir}/.env.example" "${env_dir}/.env"
        echo -e "${RED}A .env file has been created from $docker_dir/.env.example. Please edit it to configure your environment settings and run the build task again.${NC}"
        exit 1
    fi
}

# Load .env variables
load_env_variables() {
    if [ -f "${env_dir}/.env" ]; then
        # Read and process each line of the .env file
        while IFS= read -r line || [ -n "$line" ]; do
            # Trim leading and trailing whitespace
            line=$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

            # Skip comments and empty lines
            if [[ "$line" =~ ^#.*$ || -z "$line" ]]; then
                continue
            fi

            # Ensure the line is valid for export
            if [[ ! "$line" =~ ^[a-zA-Z_][a-zA-Z0-9_]*= ]]; then
                echo -e "${RED}Warning: Invalid line in .env file: $line${NC}"
                continue
            fi

            # Export the variable, allowing for quotes and string replacements
            eval "export $line"
        done < "$env_dir/.env"

    else
        echo -e "${RED}Error: .env file not found in $env_dir.${NC}"
        exit 1
    fi
}

# Check if Docker is installed
check_docker_installed() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Docker is not installed. Installing Docker...${NC}"
        # Add Docker's official GPG key:
        sudo apt-get update
        sudo apt-get install ca-certificates curl
        sudo install -m 0755 -d /etc/apt/keyrings
        sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
        sudo chmod a+r /etc/apt/keyrings/docker.asc

        # Add the repository to Apt sources:
        echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
        $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
        sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
        sudo apt-get update
        sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    fi
    echo -e "${BLUE}Docker Version: $(docker --version)${NC}"
}

# Check if Docker Compose v2 is installed
check_docker_compose_installed() {
    if ! sudo docker compose version &> /dev/null; then
        echo -e "${YELLOW}Docker Compose v2 is not installed. Installing Docker Compose v2...${NC}"
        DOCKER_CONFIG=${DOCKER_CONFIG:-$HOME/.docker}
        mkdir -p $DOCKER_CONFIG/cli-plugins
        curl -SL https://github.com/docker/compose/releases/download/v2.22.0/docker-compose-linux-x86_64 -o $DOCKER_CONFIG/cli-plugins/docker-compose
        chmod +x $DOCKER_CONFIG/cli-plugins/docker-compose
    fi
    echo -e "${BLUE}Docker Compose Version: $(sudo docker compose version | head -n 1)${NC}"
}

check_dot_env
load_env_variables
check_docker_installed
check_docker_compose_installed

if [ "$BUILD" = true ]; then
    echo -e "${BLUE}Building Docker containers...${NC}"
    sudo docker compose -f .vscode/docker/docker-compose.yml build
fi