/** @odoo-module **/
import { CharField } from "@web/views/fields/char/char_field";
import { registry } from "@web/core/registry";
import { useState, useRef } from "@odoo/owl";

// 1) Extend CharField for password‑reveal
export class PasswordRevealField extends CharField {
    setup() {
        super.setup();
        this.state = useState({ reveal: false });
        this.inputRef = useRef("input");  // matches <input t-ref="input">
    }
    toggleReveal() {
        this.state.reveal = !this.state.reveal;
        this.inputRef.el.type = this.state.reveal ? "text" : "password";
    }
    get iconClass() {
        return this.state.reveal ? "fa fa-eye-slash" : "fa fa-eye";
    }
}
PasswordRevealField.template = "odoo_base.PasswordRevealField";

// 2) Register widget
registry.category("fields").add("password_reveal", {
    component: PasswordRevealField,
    displayName: "Password Reveal",
    supportedTypes: ["char"],
    extractProps: ({ attrs }) => ({ placeholder: attrs.placeholder }),
});
