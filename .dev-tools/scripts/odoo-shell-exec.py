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

    # Build the Odoo shell command
    shell_cmd = [
        args.python_bin, args.odoo_bin, 'shell',
        '-r', args.db_user,
        '-w', args.db_pass,
        '--log-level=' + args.log_level,
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
            bufsize=0,  # Unbuffered for immediate output
            universal_newlines=True,
            env=env  # Use cleaned environment
        )
        # Send the command followed by exit
        full_cmd = command + '\nexit()\n'
        proc.stdin.write(full_cmd)
        proc.stdin.flush()
        proc.stdin.close()

        # Process output in real-time
        if args.verbose:
            # Show all output in verbose mode
            for line in proc.stdout:
                print(line.rstrip('\n'))
        else:
            # Filter output in real-time
            command_started = False
            in_shell_banner = True

            for line in proc.stdout:
                line = line.rstrip('\n')

                # Always show error messages immediately
                if any(re.match(pattern, line) for pattern in [
                    r'^ERROR', r'^Traceback', r'^  File', r'^\w*Error:', r'^\w*Exception:'
                ]):
                    print(line)
                    continue

                # Check if we've reached the shell ready area
                if in_shell_banner:
                    if any(re.match(pattern, line) for pattern in [
                        r'^Python \d+\.\d+\.\d+', r'^IPython.*--', r'^Tip:'
                    ]):
                        in_shell_banner = False
                        print(line)
                        continue
                    # Still in initialization, suppress logs but show important messages
                    if not any(re.match(pattern, line) for pattern in [
                        r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} \d+ INFO',
                        r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} \d+ WARNING',
                        r'^/.*\.py:\d+: UserWarning:',
                        r'^\s*import pkg_resources',
                        r'^\s*The pkg_resources package',
                        r'^profiling:/tmp/.*\.gcda:Cannot open',
                        r'^profiling:.*Cannot open',
                    ]):
                        if line.strip():  # Don't show empty lines during init
                            print(line)
                    continue

                # Check if command execution has started
                if not command_started:
                    if any(re.match(pattern, line) for pattern in [
                        r'^In \[\d+\]:', r'^>>>', r'^env:', r'^odoo:', r'^openerp:', r'^self:'
                    ]):
                        command_started = True
                        print(line)
                        continue

                # After command execution starts, show ALL output except profiling errors
                if command_started:
                    # Show everything (including INFO, WARNING, DEBUG, ERROR logs) except profiling errors
                    if not any(re.match(pattern, line) for pattern in [
                        r'^profiling:/tmp/.*\.gcda:Cannot open',
                        r'^profiling:.*Cannot open',
                    ]):
                        print(line, flush=True)
                else:
                    # Before command starts, suppress initialization logs (INFO/WARNING) but keep errors
                    if not any(re.match(pattern, line) for pattern in [
                        r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} \d+ INFO',
                        r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} \d+ WARNING',
                        r'^profiling:/tmp/.*\.gcda:Cannot open',
                        r'^profiling:.*Cannot open',
                    ]):
                        print(line)

        # Wait for completion
        return_code = proc.wait()

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
