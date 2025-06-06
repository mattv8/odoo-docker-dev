# Easy Grant Portal

A simple Odoo module for managing portal access for partners.

## Features

- **Grant Portal Access**: Easily grant portal access to partners with email addresses
- **Revoke Portal Access**: Revoke portal access with mandatory reason tracking
- **Confirmation Modal**: Shows confirmation dialog before granting/revoking access
- **Status Indicators**: Visual buttons showing current portal access status
- **Automatic Emails**: Sends password reset/invitation emails when granting access
- **Revocation History**: Tracks and displays previous revocation reasons

## Installation

1. Copy the module to your Odoo addons directory
2. Update your app list in Odoo
3. Install the "Easy Grant Portal" module

## Usage

### Granting Portal Access

1. Navigate to a partner record that has an email address
2. In the kanban view or form view, you'll see a "Grant Portal Access" button
3. Click the button to open the confirmation modal
4. Click "Grant" to confirm - this will:
   - Create a portal user account (if needed)
   - Assign the portal group to the user
   - Send an invitation/password reset email

### Revoking Portal Access

1. For partners with active portal access, the button will show "Revoke Portal Access"
2. Click the button to open the confirmation modal
3. Enter a reason for revocation (mandatory)
4. Click "Revoke" to confirm - this will:
   - Deactivate the user account
   - Remove portal group access
   - Log a message in the partner's chatter

## Technical Details

### Dependencies

- `base`: Core Odoo functionality
- `portal`: Portal functionality
- `auth_signup`: User invitation and signup functionality

### Models Extended

- `res.partner`: Adds portal access status and revocation note fields
- `res.users`: Adds grant/revoke portal access methods and revocation note field

### Security

- Portal access buttons are only visible to users with `base.group_user` permissions
- All portal access operations are logged in the partner's chatter

## License

LGPL-3
