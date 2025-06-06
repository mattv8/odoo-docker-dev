/** @odoo-module **/

import { registry } from "@web/core/registry";

/**
 * Mock for the /switch/user route used in tests
 * This mock simulates the behavior of the user_switch controller method
 * which checks if the current user is an admin.
 */
function mockSwitchUser(route, args) {
    // Mock response simulating admin user check
    // Return true to simulate admin user, false for non-admin
    return true;
}

/**
 * Mock for the /switch/back route used in tests
 * This mock simulates the behavior of switching back to the original user
 */
function mockSwitchBack(route, args) {
    // Mock response simulating successful switch back
    return { redirect: '/web' };
}

// Register the mocks in the mock_server registry
registry.category("mock_server").add("/switch/user", mockSwitchUser);
registry.category("mock_server").add("/switch/back", mockSwitchBack);
