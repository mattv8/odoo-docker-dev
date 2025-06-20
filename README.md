# Odoo Development Environment

This project includes a Docker-based development environment. All installation, build, and runtime tasks are handled through Docker and VSCode tasks.

---

## Table of Contents

- [Installation & Setup](#installation--setup)
- [VSCode Tasks](#vscode-tasks)
- [Accessing the Containers](#accessing-the-containers)
- [Entrypoint Script Usage](#entrypoint-script-usage)
    - [General Behavior](#general-behavior)
    - [Scaffolding New Modules](#scaffolding-new-modules)
    - [Upgrading or Installing Modules](#upgrading-or-installing-modules)
- [Debugging with debugpy](#debugging-with-debugpy)
- [PostgreSQL Setup & Maintenance](#postgresql-setup--maintenance)
- [Additional Notes](#additional-notes)
- [Troubleshooting](#troubleshooting)

---

## Installation & Setup

### Prerequisites
- **Visual Studio Code (VSCode)**: We recommend using VSCode as your Integrated Development Environment (IDE) due to its integrated task automation capabilities. [CODE.VISUALSTUDIO.COM](https://code.visualstudio.com/docs/editor/tasks)

- **Docker & Docker Compose**: Ensure Docker and Docker Compose are installed and running on your system.

- **Linux Environment**: This setup requires a Linux environment.
  - **Linux/macOS**: Use your native terminal
  - **Windows**: Install and configure WSL (Windows Subsystem for Linux) to run a Linux environment. For optimal performance, store your project files within the WSL filesystem. Detailed setup instructions are available in Microsoft's guide. [LEARN.MICROSOFT.COM](https://learn.microsoft.com/en-us/windows/wsl/setup/environment)

- **Extensions**: A list of recommended extensions is in `.vscode/extensions.json`.

### Installation

1. **Clone the Necessary Repositories** Choose a working directory (e.g., `~/Odoo`) and clone the following repositories. Adjust folder names as needed, but be sure to update the paths used in startup commands later:
    1. **Odoo 17.0 Community**
        ```bash
        git clone --branch 17.0 git@github.com:odoo/odoo.git odoo
        ```

    2. **Odoo-EE 17.0 (Enterprise, requires access permission)**
        ```bash
        git clone --branch 17.0 git@github.com:odoo/enterprise.git odoo-e
        ```

    3. **Custom Modules**
        ```bash
        git clone https://github.com/mattv8/odoo-docker-dev.git custom-modules
        ```

2. **Run the Install Script** The install script located at `.vscode/scripts/install.sh` sets up your environment, installs Docker, Docker Compose, and creates a `.env` file. **Run this script first**:

    ```bash
    cd <your_project_root>
    bash .vscode/scripts/install.sh
    ```

    This script will:

    - Configure your environment.
    - Ensure Docker and Docker Compose are installed.
    - Create the `.env` file (if not already present).

## VSCode Tasks

This repository includes a set of pre-configured VSCode tasks. These tasks allow you to:

- **Restart Odoo**: Press <kbd>Ctrl+Shift+B</kbd> (or <kbd>Cmd+Shift+B</kbd> on macOS) to start or restart the Odoo server.

- **Start the Docker Stack**: A task to start the Docker containers (including PostgreSQL and PGAdmin).
Use the Command Palette <kbd>Ctrl+Shift+P</kbd> (or <kbd>Cmd+Shift+P</kbd> on macOS) and select **Tasks: Run a Task** then choose **Start Docker Stack**.

- **Enter Odoo Shell**: A task that starts an Odoo shell within the Docker container with the appropriate environment configuration.

- **Run Odoo Tests**: A task to run **all** Odoo tests with the appropriate environment configuration.

- **Scaffold New Module**: A task to create a new Odoo module with the scaffold command. You'll be prompted to enter the module name.

---

### Accessing the Containers

Once your Docker stack is running, you can access the services using the following URLs:

- **Odoo**
Access your Odoo instance at: [http://localhost:8069](http://localhost:8069/)

- **PGAdmin**
Manage your PostgreSQL databases with PGAdmin at: [http://localhost:8080](http://localhost:8080/)

- **Mailpit**
View and debug outgoing emails via Mailpit at: [http://localhost:8081](http://localhost:8081/)

These ports are defined in your environment configuration (e.g., in your `.env` file) as:
- `ODOO_PORT=8069`

- `PGADMIN_PORT=8080`

- `MAILPIT_PORT=8081`

Make sure these ports are correctly mapped in your Docker Compose configuration so that they are accessible from your host machine.

## Entrypoint Script Usage
An `entrypoint.sh` (located at `.vscode/scripts/entrypoint.sh` which is copied to `/usr/local/bin/odoo` in the Docker image) dispatches commands based on the first argument passed when executing `odoo` in the container.

### General Behavior

- **Default Startup**:

    When no specific subcommand is given, Odoo starts with `debugpy` attached (listening on port 5678), allowing you to remotely attach a debugger.

- **Shell Mode**:

    Run `sudo docker exec -it odoo-server odoo shell` to start an interactive Odoo shell with the appropriate environment configuration.

    *Example:*

    ```bash
    sudo docker exec -it odoo-server odoo shell

    # Or run a long command:
    sudo docker exec -it odoo-server odoo shell --exec "
    env = self.env
    # Find a product tag from demo data
    tag = env['product.tag'].search([], limit=1)
    if tag:
        print('First product tag name:', repr(tag.name))
        print('Tag name type:', type(tag.name))
    else:
        print('No product tags found')
    "
    ```

- **Testing Mode**

    To run tests from the VS Code command palette: press <kbd>Ctrl + Shift + P</kbd> (or <kbd>Cmd + Shift + P</kbd> on macOS), choose **Tasks: Run a Task**, then select **Run All Odoo Tests**.

    Run your test suite in a fresh database with:
    ```bash
    sudo docker exec -it odoo-server odoo test
    ```
    This command will:
    1. Create a new temporary test database
    2. Install all modules
    3. Execute your tests
    4. Automatically drop the test database when complete

    *Example:*

    ```bash
    # Install and test every module, and run a specific UI test:
    sudo docker exec -it odoo-server odoo test --install-all --test-tags=:TestUi.test_example

    # Install and test only the 'custom_web' module, EXCLUDING a specific UI test:
    sudo docker exec -it odoo-server odoo test -i custom_web --test-tags=:-TestUi.test_example
    ```

    > *Notes:*
    > - Test exclusions (`--test-tags=:-...`) match Odoo.sh conventions.
    > - Each test run uses a new, randomly named database that is removed afterward.

### Scaffolding New Modules

You can quickly scaffold new Odoo modules using the built-in Odoo scaffold command. This creates a basic module structure with all necessary files in your modules directory.

*Examples:*

```bash
# Create a new module named 'my_custom_module' with the default template
sudo docker exec -it odoo-server odoo scaffold my_custom_module

# Create a module with the website template
sudo docker exec -it odoo-server odoo scaffold my_website_module --template=website

# Create a module with the theme template
sudo docker exec -it odoo-server odoo scaffold my_theme_module --template=theme
```

> *Notes:*
> - The scaffold command creates a complete module structure including `__manifest__.py`, `__init__.py`, models, views, and security files.
> - Available templates include: `default`, `website`, and `theme`.

### Upgrading or Installing Modules
You can CLI upgrade or install modules by passing either the `-u` (upgrade) or `-i` (install) flag as the first argument, followed by a comma-separated list of module names.

*Examples:*
- **Upgrade Modules**:

    ```bash
    sudo docker exec -it odoo-server odoo -u custom_sale,custom_crm

    #Or you can upgrade all at once with:
    sudo docker exec -it odoo-server odoo -u --all
    ```

- **Install Modules**:

    ```bash
    sudo docker exec -it odoo-server odoo -i new_module

    # Or you can install all at once with:
    sudo docker exec -it odoo-server odoo -i --all
    ```
> **Note:** The entrypoint script detects the flag (`-u` or `-i`) and constructs the command accordingly, bypassing the debugpy wrapper when upgrading or installing modules.

- **Using `.installed_modules` File**

    You can create a `.installed_modules` file in the root of your custom modules directory to specify which modules should be automatically installed when the container starts. Each module name should be on a new line.

    *Example .installed_modules file:*
    ```text
    custom_web
    custom_sale
    custom_crm
    # This is a comment
    custom_accounting
    ```

    The entrypoint script reads this file during container startup and automatically installs the listed modules. Comments (lines starting with #) and empty lines are ignored.

---

## Debugging with debugpy
To debug the Odoo server using VSCode's integrated Python debugger (`debugpy`), follow these steps:
1. **Ensure `debugpy` is Running**: The Odoo server should be started by default with `debugpy` enabled. This allows VSCode to attach to the running process for debugging.

2. **Start the Debugging Session**:
  - In VSCode, go to the Run and Debug view <kbd>Ctrl+Shift+D</kbd> (or <kbd>Cmd+Shift+D</kbd> on macOS).
  - Click the green play button or press <kbd>F5</kbd> to start debugging.

For more detailed information on Python debugging in VSCode, refer to the [official documentation](https://code.visualstudio.com/docs/python/debugging) .

## PostgreSQL Setup & Maintenance

- **Accessing pgAdmin**

    A pgAdmin container is included for easy GUI management. After you start your stack, point your browser at `http://localhost:${PGADMIN_PORT}` (default `PGADMIN_PORT` is `8080`).

    - **Login:**  use the credentials from your `.env` (`DB_PASS`).

- **Tuning the server**

    You can override any PostgreSQL setting by editing  the file `.vscode/docker/postgresql.conf`. Adjust your parameters (e.g. `max_connections`, `work_mem`, etc.) and then restart the `postgres` container with:
    ```bash
    sudo docker restart odoo-postgres
    ```

- **Dumping**

    To create a binary dump of your database from a local PostgreSQL server:
    ```bash
    # Replace 'your_database_name' with your actual database name
    pg_dump -Fc your_database_name > /tmp/your_database_$(date +%F).dump
    ```

    To create a dump from the Docker PostgreSQL container:
    ```bash
    # Dump directly to host filesystem
    sudo docker exec -e PGPASSWORD=${DB_PASS} odoo-postgres pg_dump -U ${DB_USER} -Fc your_database_name > /tmp/your_database_$(date +%F).dump

    # Or dump inside the container and copy to host
    sudo docker exec -e PGPASSWORD=${DB_PASS} odoo-postgres pg_dump -U ${DB_USER} -Fc your_database_name -f /tmp/backup.dump
    sudo docker cp odoo-postgres:/tmp/backup.dump /tmp/your_database_$(date +%F).dump
    ```

- **Restoring**

    To restore a database dump into your local PostgreSQL container:
    ```bash
    # Copy dump file to container (adjust source path as needed)
    sudo docker cp /path/to/backup.dump odoo-postgres:/tmp/

    # Create the database inside the container, if it doesn't already exist
    sudo docker exec odoo-postgres bash -c "createdb -U \"\$DB_USER\" \"\$DB_NAME\""

    # Restore the dump using credentials from the container's environment (this also cleans db if it exists already)
    sudo docker exec odoo-postgres bash -c "PGPASSWORD=\"\$DB_PASS\" pg_restore -c --if-exists -U \"\$DB_USER\" -d \"\$DB_NAME\" \"/tmp/backup.dump\""

    # ⚠️IMPORTANT⚠️: Be sure to neutralize the DB after restoring:
    sudo docker exec odoo-server odoo neutralize
    ```

    **For Windows users with WSL:**
    ```bash
    # Convert Windows path to WSL path and copy to container
    wslpath=$(wslpath "C:\Path\To\SQL.dump")
    sudo docker cp "$wslpath" odoo-postgres:/tmp/

    # Then restore the dump using credentials from the container's environment (this also cleans db if it exists already):
    sudo docker exec odoo-postgres bash -c "PGPASSWORD=\"\$DB_PASS\" pg_restore -c --if-exists -U \"\$DB_USER\" -d  \"\$DB_NAME\" \"/tmp/$(basename "$wslpath")\""

    # ⚠️IMPORTANT⚠️: Be sure to neutralize the DB after restoring:
    sudo docker exec odoo-server odoo neutralize
    ```

    To restore a dump for a staging environment using standard PostgreSQL commands:
    ```bash
    # Drop and recreate the database
    psql -d postgres -c 'DROP DATABASE IF EXISTS "your_staging_database";'
    psql -d postgres -c 'CREATE DATABASE "your_staging_database";'
    pg_restore --clean --no-owner --dbname="your_staging_database" /path/to/your_database.dump

    # ⚠️IMPORTANT⚠️: Be sure to neutralize the DB after restoring:
    # Adjust the path and configuration file as needed for your environment
    python3 /path/to/odoo-bin neutralize -c /path/to/odoo.conf -d your_staging_database --stop-after-init
    ```

- **Clearing the database volume**

    To completely wipe out your local Postgres data and start fresh, run:
    ```bash
    sudo docker compose down
    sudo docker volume rm "$(basename "$PWD")_postgres-data"
    ```

    Then bring the stack back up with `sudo docker compose up`.

## Additional Notes

- **Environment Variables**:
    In the entrypoint, some environment variables used by modules are set using `export` and are also accessible to Odoo using `os` for example:

    ```bash
    export SUPPRESS_FS_ERR=true
    ```

## Troubleshooting

- **Entrypoint Not Found / CRLF Issues**
    If you see the `odoo-server` container failing to start with errors like `exec /usr/local/bin/odoo: no such file or directory`, ensure that your entrypoint script uses UNIX line endings (LF). The Dockerfile uses `dos2unix` to convert CRLF to LF. Verify your source file encoding if issues persist.

- **Unable to Remote Connect to debugpy**
    If you can’t attach to the debugger, confirm that debugpy is listening on all interfaces. Also, ensure that the container port is correctly mapped in the Docker configuration.

    ```bash
    sudo docker exec -it odoo-server netstat -tuln | grep :5678
    ```
    You should see an entry similar to:

    ```nginx
    tcp   0   0 0.0.0.0:5678   0.0.0.0:*   LISTEN
    ```

- **Module Upgrade/Install Command Issues**
    When running module upgrades or installs (`-u` or `-i`), make sure you pass the flag as the first argument. The entrypoint script shifts this flag and constructs the command accordingly. Verify your module names are comma-separated.

- **Scaffold Command Issues**
    When using the scaffold command (`scaffold`), ensure the `/custom-odoo` directory is writable by the `odoo` user inside the container. All scaffolded modules are automatically created in this directory.

- **PostgreSQL Checkpoints / Timeouts**
    If you encounter frequent checkpoints or idle transaction timeouts during database restore, consider increasing `max_wal_size` in `.vscode/docker/postgresql.conf`.

    > *Note: Use caution when increasing `DB_TIMEOUT` in `.env` as that is set to match production and shouldn't need to be increased.*
