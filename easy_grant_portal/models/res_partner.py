# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ResPartner(models.Model):
    _inherit = "res.partner"

    portal_access = fields.Char(
        compute="_compute_portal_access",
        help="Indicates portal access status: 'active', 'revoked', or 'none'",
        string="Portal Access Status",
    )
    portal_revoke_note = fields.Text(
        string="Portal Access Revocation Reason",
        compute="_compute_portal_revoke_note",
        inverse="_inverse_portal_revoke_note",
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

    @api.depends('user_ids.portal_revoke_note')
    def _compute_portal_revoke_note(self):
        for partner in self:
            user = self.env['res.users'].search([('login', '=', partner.email),('active', 'in', [True, False])], limit=1)
            partner.portal_revoke_note = user.portal_revoke_note or False

    def _inverse_portal_revoke_note(self):
        for partner in self:
            if user := self.env['res.users'].search([('login', '=', partner.email),('active', 'in', [True, False])], limit=1):
                user.sudo().portal_revoke_note = partner.portal_revoke_note

    def toggle_portal_access(self):
        """
        Toggles portal access for the partner and ensures the toggle is successful.
        This method only allows toggling access to one partner at a time.

        :return: A dictionary with the result of the operation.
        """
        self.ensure_one()
        if not self.email:
            return {
                "type": "ir.actions.client",
                "tag": "refresh_portal_access_button",
                "target": "current",
                "params": [self._prepare_result(
                    success=False,
                    portal_access=self.portal_access,
                    res_id=self.id,
                    message=_("This partner does not have an email address."),
                )],
            }

        # Open Confirmation Modal
        if not self.env.context.get('confirmed'):
            return {
                'type': 'ir.actions.act_window',
                'name': _('Confirm Portal Access Change'),
                'res_model': 'res.partner',
                'res_id': self.id,
                'view_mode': 'form',
                'views': [(self.env.ref('easy_grant_portal.confirmation_modal').id, 'form')],
                'target': 'new',
                'context': {
                    'dialog_size': 'small',
                },
            }

        # Refresh the computed field to ensure accuracy
        self._compute_portal_access()
        current_access = self.portal_access == 'active'
        expected_access = not current_access

        # Perform the appropriate action
        if not current_access:
            result = self.env["res.users"].sudo().grant_portal_access(self.id)
        else:
            result = self.env["res.users"].sudo().revoke_portal_access(self.id)

        # Refresh the computed field to get the updated state
        self._compute_portal_access()

        # Ensure the state matches the expected result
        success = result.get("success") and (self.portal_access == 'active') == expected_access

        # Log to the chatter
        if success:
            if self.portal_access == 'active':
                message = _("Portal access has been granted by %s.") % self.env.user.name
            else:
                message = _("Portal access has been revoked by %s. Revocation reason: %s") % (self.env.user.name, self.portal_revoke_note)
            self.message_post(body=message)
            if self.parent_id:
                self.parent_id.message_post(body=_("For partner %s: %s") % (self.name, message))

        results = self._prepare_result(
            success=success,
            portal_access=self.portal_access,
            res_id=self.id,
            message=result.get("message"),
        )

        # Return the action for JS
        return {
            "type": "ir.actions.client",
            "tag": "refresh_portal_access_button",
            "target": "current",
            "params": results,
        }

    def _prepare_result(self, success, portal_access, res_id, message):
        """Helper method to structure the result data."""
        return {
            "success": success,
            "portal_access": portal_access,
            "message": message,
            "res_id": res_id,
        }
