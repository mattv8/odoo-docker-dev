# Impersonate User

An Odoo module that allows administrators to securely impersonate other users without requiring their passwords. This is particularly useful for troubleshooting user-specific issues, testing permissions, and providing support.

## Features

- **Admin User Switching**: Administrators can switch to any user account in the system
- **Portal User Impersonation**: Direct impersonation of portal users from partner records
- **Secure Session Management**: Safe switching with automatic session validation and timeouts
- **Easy Switch Back**: Quick return to original admin account
- **Visual Indicators**: Systray button shows current impersonation status
- **Time-based Security**: Automatic session expiry after 4 hours for security

## Installation

1. Copy the module to your Odoo addons directory
2. Update your app list in Odoo
3. Install the "Impersonate User" module

## Usage

### Method 1: Systray User Switcher (Backend)

1. **Access the Switcher**: Look for the user switch icon in the systray (top right corner)
2. **Switch to Another User**:
   - Click the systray button
   - Select a user from the dropdown wizard
   - View their groups and permissions
   - Click "Switch" to impersonate them
3. **Switch Back**: Click the same systray button to return to your original admin account

### Method 2: Direct Portal User Impersonation

1. **From Partner Records**: Navigate to Contacts → select a partner with portal access
2. **Impersonate Button**: Click the "Impersonate User" button (visible in kanban and form views)
3. **Automatic Login**: You'll be automatically logged in as that portal user and redirected to `/my`
4. **Switch Back**: Use `/switch/back` URL or the systray button to return to admin

## Security Features

### Session Management
- **Secure Authentication**: Uses Odoo's built-in authentication without exposing passwords
- **Session Timeout**: Impersonation automatically expires after 4 hours
- **Session Validation**: Continuous validation of impersonation state
- **Safe Fallback**: Automatic cleanup and redirect on session errors

### Access Control
- **Admin Only**: Only users with admin privileges can initiate impersonation
- **Group Restrictions**: Respects existing user group permissions
- **Audit Trail**: All impersonation activities are logged for security

### Portal User Safety
- **Active Users Only**: Can only impersonate active portal users
- **Email Validation**: Requires valid email addresses for portal users
- **Group Verification**: Ensures users have proper portal group membership

## Technical Details

### Dependencies
- `web`: Core web interface functionality
- `website`: Website and portal functionality
- `portal`: Portal user management

### Models Extended
- `res.partner`: Adds portal access status and impersonation methods
- `res.users`: Enhanced with user switching capabilities
- `user.selection`: Wizard for selecting users to impersonate

### Session Extensions
- `authenticate_without_password()`: Secure passwordless authentication
- `switch_back_user()`: Safe return to original user
- `check_impersonation_validity()`: Session validation
- `clear_impersonation()`: Session cleanup

### Controllers
- `/switch/user`: Check admin status and initiate switching
- `/switch/back`: Return to original admin user

## UI Components

### Systray Widget
- Shows user switch status
- Provides quick access to user selection
- Visual indication when impersonating

### Partner Views
- Impersonate buttons in kanban and form views
- Only visible for contacts with portal access
- Restricted to sales team members

### User Selection Wizard
- Dropdown list of available users
- Display of user groups and permissions
- Confirmation before switching

## Security Considerations

⚠️ **Important Security Notes**:

1. **Admin Privileges Required**: Only administrators should have access to this module
2. **Audit Logging**: Consider enabling access logs for compliance
3. **Session Timeout**: 4-hour automatic timeout prevents abandoned sessions
4. **Data Access**: Impersonated users have full access to their data - use responsibly
5. **Testing Environment**: Ideal for development/testing; use caution in production

## Troubleshooting

### Common Issues

**Systray Button Not Visible**
- Ensure you have admin privileges
- Check that the module is properly installed
- Verify you're not already impersonating a user

**Portal Impersonation Fails**
- Verify the partner has an active email address
- Ensure the user has portal group membership
- Check that the user account is active

**Session Timeout Issues**
- Impersonation automatically expires after 4 hours
- Refresh the page to return to admin account
- Re-initiate impersonation if needed

### Error Handling
The module includes comprehensive error handling:
- Graceful fallback on session errors
- Automatic cleanup of invalid sessions
- Safe redirects when impersonation fails

## Development & Testing

### Test Mode Support
- QUnit test compatibility
- Conditional visibility in test environments
- Mock user switching for automated tests

### Logging
- Internal error logging for debugging
- No sensitive information exposed to users
- Exception handling for security

## License

LGPL-3 - GNU Lesser General Public License v3

## Credits

- **Author**: Cybrosys Techno Solutions
- **Maintainer**: Sabeel B (odoo@cybrosys.com)
- **Website**: https://www.cybrosys.com

## Version

17.0.1.0.1 - Compatible with Odoo 17.0
