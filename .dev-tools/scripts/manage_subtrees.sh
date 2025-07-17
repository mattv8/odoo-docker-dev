#!/bin/bash

# Git Subtree Management Script
# This script helps manage multiple Git subtrees for custom Odoo modules

set -e

SUBTREES_CONFIG=".subtrees"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

# Function to check if .subtrees file exists
check_config() {
    if [[ ! -f "$PROJECT_ROOT/$SUBTREES_CONFIG" ]]; then
        print_warning "No $SUBTREES_CONFIG file found. Creating example file..."
        cat > "$PROJECT_ROOT/$SUBTREES_CONFIG" << EOF
# Git Subtrees Configuration
# Format: module_name|repository_url|branch
# Example:
# my_custom_module|https://github.com/yourusername/my_custom_module.git|main
# another_module|https://github.com/yourusername/another_module.git|develop
EOF
        print_status "Created $SUBTREES_CONFIG file. Please add your subtree configurations."
        exit 0
    fi
}

# Function to read subtrees from config file
read_subtrees() {
    local subtrees=()
    while IFS='|' read -r module_name repo_url branch; do
        # Skip empty lines and comments
        if [[ -n "$module_name" && "$module_name" != \#* ]]; then
            subtrees+=("$module_name|$repo_url|$branch")
        fi
    done < "$PROJECT_ROOT/$SUBTREES_CONFIG"
    echo "${subtrees[@]}"
}

# Function to add a new subtree
add_subtree() {
    local module_name="$1"
    local repo_url="$2"
    local branch="${3:-main}"

    if [[ -z "$module_name" || -z "$repo_url" ]]; then
        print_error "Usage: $0 add <module_name> <repository_url> [branch]"
        exit 1
    fi

    print_header "Adding Subtree: $module_name"

    # Check if directory already exists
    if [[ -d "$PROJECT_ROOT/$module_name" ]]; then
        print_warning "Directory $module_name already exists. Skipping..."
        return 0
    fi

    # Add the subtree
    cd "$PROJECT_ROOT"
    if git subtree add --prefix="$module_name" "$repo_url" "$branch" --squash; then
        print_status "Successfully added subtree: $module_name"

        # Add to config file if not already there
        if ! grep -q "^$module_name|" "$SUBTREES_CONFIG" 2>/dev/null; then
            echo "$module_name|$repo_url|$branch" >> "$SUBTREES_CONFIG"
            print_status "Added $module_name to $SUBTREES_CONFIG"
        fi
    else
        print_error "Failed to add subtree: $module_name"
        return 1
    fi
}

# Function to pull updates from all subtrees
pull_subtrees() {
    local subtrees=($(read_subtrees))

    if [[ ${#subtrees[@]} -eq 0 ]]; then
        print_warning "No subtrees configured. Please add subtrees to $SUBTREES_CONFIG"
        return 0
    fi

    print_header "Pulling Updates from All Subtrees"

    cd "$PROJECT_ROOT"
    for subtree in "${subtrees[@]}"; do
        IFS='|' read -r module_name repo_url branch <<< "$subtree"

        if [[ -d "$module_name" ]]; then
            print_status "Pulling updates for: $module_name"
            if git subtree pull --prefix="$module_name" "$repo_url" "$branch" --squash; then
                print_status "Successfully updated: $module_name"
            else
                print_error "Failed to update: $module_name"
            fi
        else
            print_warning "Directory $module_name not found. Run 'add' command first."
        fi
    done
}

# Function to push changes to all subtrees
push_subtrees() {
    local subtrees=($(read_subtrees))

    if [[ ${#subtrees[@]} -eq 0 ]]; then
        print_warning "No subtrees configured. Please add subtrees to $SUBTREES_CONFIG"
        return 0
    fi

    print_header "Pushing Changes to All Subtrees"

    cd "$PROJECT_ROOT"
    for subtree in "${subtrees[@]}"; do
        IFS='|' read -r module_name repo_url branch <<< "$subtree"

        if [[ -d "$module_name" ]]; then
            # Check if there are changes in the subtree directory
            if git diff --quiet HEAD -- "$module_name/"; then
                print_status "No changes in $module_name, skipping..."
                continue
            fi

            print_status "Pushing changes for: $module_name"
            if git subtree push --prefix="$module_name" "$repo_url" "$branch"; then
                print_status "Successfully pushed: $module_name"
            else
                print_error "Failed to push: $module_name"
            fi
        else
            print_warning "Directory $module_name not found. Run 'add' command first."
        fi
    done
}

# Function to list all configured subtrees
list_subtrees() {
    check_config
    local subtrees=($(read_subtrees))

    if [[ ${#subtrees[@]} -eq 0 ]]; then
        print_warning "No subtrees configured."
        return 0
    fi

    print_header "Configured Subtrees"

    for subtree in "${subtrees[@]}"; do
        IFS='|' read -r module_name repo_url branch <<< "$subtree"
        echo -e "${BLUE}Module:${NC} $module_name"
        echo -e "${BLUE}Repository:${NC} $repo_url"
        echo -e "${BLUE}Branch:${NC} $branch"
        echo -e "${BLUE}Status:${NC} $([ -d "$PROJECT_ROOT/$module_name" ] && echo "Present" || echo "Not found")"
        echo ""
    done
}

# Function to show help
show_help() {
    cat << EOF
Git Subtree Management Script

Usage: $0 [command] [options]

Commands:
    add <module_name> <repo_url> [branch]  Add a new subtree
    pull                                   Pull updates from all subtrees
    push                                   Push changes to all subtrees
    list                                   List all configured subtrees
    help                                   Show this help message

Examples:
    $0 add my_module https://github.com/user/my_module.git main
    $0 pull
    $0 push
    $0 list

Configuration:
    Subtrees are configured in the .subtrees file in the project root.
    Format: module_name|repository_url|branch

EOF
}

# Main script logic
main() {
    cd "$PROJECT_ROOT"

    case "${1:-help}" in
        "add")
            add_subtree "$2" "$3" "$4"
            ;;
        "pull")
            check_config
            pull_subtrees
            ;;
        "push")
            check_config
            push_subtrees
            ;;
        "list")
            list_subtrees
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            print_error "Unknown command: ${1:-help}"
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
