#!/usr/bin/env python3
"""
Odoo Shell Command Executor
This script executes Python commands in an Odoo shell environment.
"""

import sys
import subprocess
import argparse
import os
import re
import threading


def filter_odoo_output(output_lines, command_started_event):
    """
    Filter Odoo shell output to suppress initialization messages.
    Only show command results and errors.
    """
    filtered_lines = []
    command_started = False
    in_shell_banner = True

    # Patterns to identify Odoo initialization messages to suppress
    suppress_patterns = [
        r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} \d+ INFO',  # INFO log lines with timestamp
        r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} \d+ WARNING',  # WARNING log lines with timestamp
        r'^/.*\.py:\d+: UserWarning:',  # Python warnings
        r'^\s*import pkg_resources',  # Import warnings
        r'^\s*The pkg_resources package',  # Package deprecation warnings
        r'^profiling:/tmp/.*\.gcda:Cannot open',  # Profiling errors
        r'^profiling:.*Cannot open',  # General profiling errors
    ]

    # Patterns that indicate command execution area (keep these)
    command_area_patterns = [
        r'^In \[\d+\]:',  # IPython input prompt
        r'^>>>',  # Python prompt
        r'^env:',  # Environment variable display
        r'^odoo:',  # Odoo module display
        r'^openerp:',  # OpenERP alias display
        r'^self:',  # Self object display
    ]

    # Patterns that indicate shell is ready (end of initialization)
    shell_ready_patterns = [
        r'^Python \d+\.\d+\.\d+',  # Python version line
        r'^IPython.*--',  # IPython version line
        r'^Tip:',  # IPython tip
    ]

    # Patterns that indicate errors we should always show
    error_patterns = [
        r'^ERROR',
        r'^Traceback',
        r'^  File',
        r'^\w*Error:',
        r'^\w*Exception:',
    ]

    for line in output_lines:
        # Always show error messages
        if any(re.match(pattern, line) for pattern in error_patterns):
            filtered_lines.append(line)
            continue

        # Check if we've reached the shell ready area
        if in_shell_banner:
            if any(re.match(pattern, line) for pattern in shell_ready_patterns):
                # We're at the shell banner area, start showing output
                in_shell_banner = False
                filtered_lines.append(line)
                continue
            # Still in initialization, suppress logs but show warnings/errors
            if not any(re.match(pattern, line) for pattern in suppress_patterns):
                # If it's not a suppressed pattern, show it (could be important)
                if line.strip():  # Don't show empty lines during init
                    filtered_lines.append(line)
            continue

        # Check if command execution has started
        if not command_started:
            if any(re.match(pattern, line) for pattern in command_area_patterns):
                command_started = True
                command_started_event.set()
                filtered_lines.append(line)
                continue

        # After shell is ready, show everything except suppressed patterns
        if not any(re.match(pattern, line) for pattern in suppress_patterns):
            filtered_lines.append(line)

    return filtered_lines


def main():
    parser = argparse.ArgumentParser(description='Execute commands in Odoo shell')
    parser.add_argument('--python-bin', required=True, help='Path to Python binary')
    parser.add_argument('--odoo-bin', required=True, help='Path to Odoo binary')
    parser.add_argument('--db-user', required=True, help='Database user')
    parser.add_argument('--db-pass', required=True, help='Database password')
    parser.add_argument('--db-name', required=True, help='Database name')
    parser.add_argument('--log-level', required=True, help='Log level')
    parser.add_argument('--data-dir', required=True, help='Data directory')
    parser.add_argument('--addons-path', required=True, help='Addons path')
    parser.add_argument('--modules', default='', help='Modules to install')
    parser.add_argument('--command', required=True, help='Command to execute')
    parser.add_argument('--verbose', action='store_true', help='Show all output including initialization')

    args = parser.parse_args()

    # Get command from args, or fall back to environment variable
    command = args.command
    if command == "$ODOO_EXEC_COMMAND":
        command = os.environ.get('ODOO_EXEC_COMMAND', '')
        if not command:
            print("Error: No command provided via --command or ODOO_EXEC_COMMAND environment variable", file=sys.stderr)
            sys.exit(1)

    # Build the Odoo shell command with quieter log level for initialization
    log_level = 'error' if not args.verbose else args.log_level
    shell_cmd = [
        args.python_bin, args.odoo_bin, 'shell',
        '-r', args.db_user,
        '-w', args.db_pass,
        '--log-level=' + log_level,
        '--db_host=odoo-postgres',
        '--db_port=5432',
        '--data-dir=' + args.data_dir,
        '--addons-path=' + args.addons_path,
        '-d', args.db_name,
        '--shell-interface=ipython'
    ]

    # Add modules if specified
    if args.modules:
        shell_cmd.extend(args.modules.split())

    if args.verbose:
        print(f"Starting Odoo shell with command: {' '.join(shell_cmd)}")
        print(f"Executing command:\n{command}")
        print("-" * 50)

    try:
        # Prepare environment to disable profiling and coverage
        env = os.environ.copy()
        env['PYTHONDONTWRITEBYTECODE'] = '1'  # Disable .pyc files
        env.pop('COVERAGE_PROCESS_START', None)  # Disable coverage if enabled
        env.pop('GCOV_PREFIX', None)  # Disable gcov profiling
        env.pop('GCOV_PREFIX_STRIP', None)  # Disable gcov profiling

        # Start the Odoo shell process
        proc = subprocess.Popen(
            shell_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,  # Line buffered
            universal_newlines=True,
            env=env  # Use cleaned environment
        )

        # Send the command followed by exit
        full_cmd = command + '\nexit()\n'
        proc.stdin.write(full_cmd)
        proc.stdin.flush()
        proc.stdin.close()

        # Read output line by line
        output_lines = []
        for line in proc.stdout:
            output_lines.append(line.rstrip('\n'))

        # Wait for completion
        return_code = proc.wait()

        if args.verbose:
            # Show all output in verbose mode
            for line in output_lines:
                print(line)
        else:
            # Filter output to show only command results
            command_started_event = threading.Event()
            filtered_lines = filter_odoo_output(output_lines, command_started_event)

            # Print filtered output
            for line in filtered_lines:
                print(line)

        if return_code != 0:
            if not args.verbose:
                print(f"Process exited with code: {return_code}", file=sys.stderr)
            sys.exit(return_code)

    except (subprocess.SubprocessError, OSError, IOError) as e:
        print(f"Error executing command: {e}", file=sys.stderr)
        if 'proc' in locals():
            proc.terminate()
        sys.exit(1)


if __name__ == '__main__':
    main()
