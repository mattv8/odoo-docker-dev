---
applyTo: '**'
---
# Odoo AI Agent: Local Development Prompt Instructions

## Database Queries & Shell Commands

Use the Odoo shell to query the database and run Python commands:

```bash
# Interactive shell
sudo docker exec -it odoo-server odoo shell

# Execute long commands directly
sudo docker exec -it odoo-server odoo shell --exec "
env = self.env
orders = env['sale.order'].search([], limit=5)
for order in orders:
    print(f'Order: {order.name}, Customer: {order.partner_id.name}')
"
```

## Module Management

**IMPORTANT**: Do NOT manually upgrade modules using `-u` or `-i` flags.

Instead:
1. Add modules to `.installed_modules` file (one per line)
2. Use the "Restart Odoo Server" task which automatically upgrades modules listed in `.installed_modules`

## Searching Odoo Source Code

The Odoo source code is available within the container and can be searched:

```bash
# Search for patterns in Odoo core
sudo docker exec odoo-server bash -c "grep -r 'sale.order' /odoo"

# Search specific directories
sudo docker exec odoo-server bash -c "grep -r 'invoice' /odoo/addons/account"

# Search with context lines
sudo docker exec odoo-server bash -c "grep -r -A 3 -B 3 'def create' /odoo/addons/sale"
```

## Container Access

- Odoo server: `sudo docker exec -it odoo-server bash`
- Database queries: Use odoo shell (not direct psql)
- File system: Full access to `/odoo` (core) and custom modules directories

## Development Workflow

1. Make code changes in your local files
2. Add new modules to `.installed_modules` if needed
3. Use "Restart Odoo Server" task to apply changes
4. Query/debug using `odoo shell`
