/** @odoo-module **/
import { registry } from "@web/core/registry";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";
import { useService } from "@web/core/utils/hooks";
import { Component, useState } from "@odoo/owl";


class ImpersonateUserButton extends Component {
    static template = "impersonate_user.impersonate_user_button";

    /**
     * @type {Object} props
     * @extends {standardWidgetProps}
     */
    static props = { ...standardWidgetProps };

    setup() {
        super.setup();
        this.action = useService("action");
        this.orm = useService("orm");
        this.state = useState({
            isHovered: false,
        });
    }

    onMouseEnter() {
        this.state.isHovered = true;
    }

    onMouseLeave() {
        this.state.isHovered = false;
    }

    async onClick(ev) {
        ev.preventDefault();
        ev.stopPropagation();

        // Call the backend method to impersonate the user
        const action = await this.orm.call(
            "res.partner",
            "action_impersonate_portal_user",
            [this.props.record.data.id],
            {
                context: this.env.context,
            }
        );

        return this.action.doAction(action);
    }
}

export const ImpersonateUserButtonComponent = {
    component: ImpersonateUserButton,
}

// Register the component
registry.category("view_widgets").add("impersonate_user_button", ImpersonateUserButtonComponent);
