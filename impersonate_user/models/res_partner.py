from odoo import models, fields, api, _
from odoo.http import request

class ResPartner(models.Model):
    _inherit = "res.partner"

    portal_access = fields.Char(
        compute="_compute_portal_access",
        help="Indicates portal access status: 'active', 'revoked', or 'none'",
        string="Portal Access Status",
    )

    @api.depends('user_ids', 'user_ids.groups_id')
    def _compute_portal_access(self):
        """Compute if the partner has portal access based on their user groups."""
        portal_group = self.env.ref('base.group_portal')
        for partner in self:
            if any(portal_group in user.groups_id for user in partner.user_ids):
                partner.portal_access = 'active'
            elif self.env['res.users'].search([('login', '=', partner.email), ('active', 'in', [False])], limit=1):
                partner.portal_access = 'revoked'
            else:
                partner.portal_access = 'none'

    def action_impersonate_portal_user(self):
        """
        Allow a user to directly impersonate portal users when viewing from Contacts module.
        Only works for users who have portal access enabled already.
        """
        self.ensure_one()

        # Find the portal user associated with this partner
        portal_user = self.env['res.users'].sudo().search([
            ('partner_id', '=', self.id),
            ('active', '=', True),
            ('groups_id', 'in', self.env.ref('base.group_portal').id)
        ], limit=1)

        if not portal_user:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': _('No active portal user found for this contact.'),
                    'type': 'warning',
                    'sticky': False,
                }
            }

        # Do the login
        request.session.authenticate_without_password(
            self.env.cr.dbname,
            portal_user.login,
            self.env
        )

        return {
            'type': 'ir.actions.act_url',
            'url': '/my',
            'target': 'self',
        }
