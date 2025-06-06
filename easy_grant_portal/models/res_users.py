# -*- coding: utf-8 -*-
import logging
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import AccessDenied, UserError

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    portal_revoke_note = fields.Text(
        string="Portal Access Revocation Reason",
        help="Reason for revoking portal access.",
    )

    @api.model
    def grant_portal_access(self, partner_id):
        """
        Grants portal access to the given partner.

        Steps:
        1. Search for the partner by ID.
        2. Check if an associated user account exists already.
        3. Get or create the user account and assign them to the portal group.

        :param partner_id: the partner with an email address you're trying to grant portal access to
        :return: A dictionary with the result status and any messages.
        """
        try:
            partner = self.env['res.partner'].browse(partner_id)
            if not partner:
                raise UserError(_("No partner found with the id: %s.") % partner_id)

            if not partner.email:
                raise UserError(_("This partner does not have an email address."))

            # Check if a user exists by email. There should only ever be one on res_users
            user = self.search([('login', '=', partner.email), ('active', 'in', [True, False])], limit=1)

            # Prevent from overwriting existing internal users
            if user and not user.share:
                raise UserError(_("A user with the email of %s is an existing internal user") % user.login)

            # Fetch the portal group ID
            portal_group = self.env.ref('base.group_portal', raise_if_not_found=True)

            # If the user does not exist and needs to be created
            if not user:
                user = self.env['res.users'].create({
                    'partner_id': partner.id,
                    'login': partner.email,
                    # Remove other groups, add to Portal group
                    'groups_id': [(5, 0, 0), (4, portal_group.id)],
                })
                # Send invitation email
                user._action_reset_password()
                return {
                    'success': True,
                    'message': f"Portal access granted to email: {partner.email}. Password reset email sent.",
                }

            # The user exists already, but has been deactivated for some reason
            elif user and self._is_inactive_user(user):
                # Prevent accidentally changing the partner_id of the user's access without explicitly allowing from context
                if user.partner_id.id != partner.id and not self.env.context.get('allow_change_partner'):
                    raise UserError(_("This action will change the partner_id from %s (%s) to %s (%s).") %
                                    (user.partner_id.id, user.partner_id.name, partner.id, partner.name))

                user.write({
                    'active': True,
                    'partner_id': partner.id,
                    # Remove other groups, add to Portal group
                    'groups_id': [(5, 0, 0), (4, portal_group.id)],
                })
                user._action_reset_password()  # Sends password reset email
                return {
                    'success': True,
                    'message': f"Portal access reactivated for email: {partner.email}. Password reset email sent.",
                }

            else:
                raise UserError(_("An account with the email %s associated with the partner %s already has portal access.") %
                                (user.login, user.partner_id.name))

        except Exception as e:
            return {'success': False, 'message': str(e)}

    @api.model
    def revoke_portal_access(self, partner_id):
        """
        Revokes portal access for the given partner.

        Steps:
        1. Search for the partner by ID.
        2. Check if a user exists for the partner.
        3. Move the user to the 'Public' group and deactivate the user.

        :param partner_id: The partner ID to revoke access for.
        :return: A dictionary with the result status and message.
        """
        try:
            # Step 1: Search for the partner by ID
            partner = self.env['res.partner'].browse(partner_id)
            if not partner.email:
                raise UserError(_("No partner found with the id: %s.") % partner_id)

            user = self.env['res.users'].search([('login', '=', partner.email)], limit=1)
            if not user:
                raise UserError(_("No Portal user found with email: %s") % partner.email)

            # Step 2: Fetch the public group
            public_group = self.env.ref('base.group_public', raise_if_not_found=True)

            # Step 3: Update user groups and deactivate the user
            user.write({
                'active': False,
                # Remove all groups, add to Public
                'groups_id': [(5, 0, 0), (4, public_group.id)],
            })

            return {
                'success': True,
                'message': f"Portal access revoked for email: {partner.email}. User deactivated and moved to public group.",
            }
        except Exception as e:
            return {
                'success': False,
                'message': str(e),
            }

    def _is_inactive_user(self, user):
        """Return True if the user exists but is inactive and not in the portal group."""
        portal_group = self.env.ref('base.group_portal', raise_if_not_found=True)
        return user and not user.active and portal_group and (portal_group.id not in user.groups_id.ids)
