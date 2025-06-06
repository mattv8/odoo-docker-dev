from odoo import fields, models, api


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    def _notify_get_recipients(self, message, msg_vals, **kwargs):
        """Compute recipients to notify based on subtype and followers. This
        method returns data structured as expected for ``_notify_recipients``."""

        recipient_data = super()._notify_get_recipients(message, msg_vals, **kwargs)
        exclude_followers_ids = self.env.context.get('exclude_followers', [])
        if exclude_followers_ids:
            recipient_data = [d for d in recipient_data if d.get("id") not in exclude_followers_ids]
        return recipient_data
