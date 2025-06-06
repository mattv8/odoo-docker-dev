/** @odoo-module **/
import { registry } from "@web/core/registry";
import { FormRenderer } from "@web/views/form/form_renderer";
import { patch } from "@web/core/utils/patch";
import { onMounted } from "@odoo/owl";

registry.category("actions").add("refresh_portal_access_button", async function (env, { params }) {
    const { success, portal_access, message, res_id } = params;
    const notification = env.services.notification;
    const dialog = env.services.dialog;

    if (!success) {
        notification.add(`Error: ${message}`, { type: "danger" });
        return;
    }

    const button = document.getElementById(`portal_access_button_${res_id}`);
    if (!button) {
        console.warn(`Button with ID portal_access_button_${res_id} not found.`);
        return;
    }

    // Update button class and text based on the new access state
    button.classList.remove("btn-primary", "btn-danger");
    if (portal_access === 'active') {
        button.classList.add("btn-danger");
        button.textContent = "Revoke Portal Access";
    } else if (['none','revoked'].includes(portal_access)) {
        button.classList.add("btn-primary");
        button.textContent = "Grant Portal Access" + ((portal_access === 'revoked') ? " Again" : "");
    } else {
        button.classList.add("btn-warning");
        button.textContent = "Unknown Portal Access Status";
    }

    dialog.closeAll(); // This only fires on success, by design
});

/**
 * Patch FormRenderer to add portal revoke note validation
 */
patch(FormRenderer.prototype, {
    setup() {
        super.setup();
        this.config = this.env?.model?.root?.model?.config;
        this.data = this.env?.model?.root?.data;
        onMounted(this.validateRevokePortalNote);
    },

    /**
     * Validates the Portal Revoke Note when revoking portal access
     * @returns void
     */
    validateRevokePortalNote() {
        if ('portal_revoke_note' in this.config?.activeFields &&
            'portal_access' in this.config?.activeFields) {

            const previousNote = this.data.portal_revoke_note ?? '';

            if (this.data.portal_access === 'active') {
                // Get the textarea inside the portal_revoke_note field container.
                const revokeField = document.querySelector('[name="portal_revoke_note"] textarea');
                if (!revokeField) return;

                // Get the Revoke button with the confirmed context.
                const revokeButton = document.querySelector('button[name="toggle_portal_access"][data-role="confirm-portal-revoke-button"]');
                if (!revokeButton) return;

                const validate = () => {
                    const currentNote = revokeField.value.trim();
                    const disable = !currentNote || (previousNote && currentNote === previousNote);
                    revokeButton.disabled = disable;

                    let helpTextEl = revokeField.parentElement.querySelector('.o_field_helptext');
                    if (disable && currentNote) {
                        if (!helpTextEl) {
                            helpTextEl = document.createElement('span');
                            helpTextEl.className = 'o_field_helptext text-danger';
                            helpTextEl.style.backgroundColor = 'yellow';
                            helpTextEl.textContent = "Please update the Reason for Revocation.";
                            revokeField.parentElement.appendChild(helpTextEl);
                        }
                    } else {
                        if (helpTextEl) {
                            helpTextEl.remove();
                        }
                    }
                };

                // Listen for input and blur events.
                revokeField.addEventListener("input", validate);

                validate(); // Run validation onMounted
            }
        }
    }
});
