# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sabeel B (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import odoo
from odoo import fields
from odoo.http import request, Session
from odoo.modules.registry import Registry
from datetime import timedelta


def authenticate_without_password(self, dbname, login, env):
    """Function for login without password"""
    if not hasattr(self, 'impersonation_origin_id'):
        self.impersonation_origin_id = None
        self.impersonation_active = False
        self.impersonation_start_time = None

    # Store current user before switching
    if env and env.user:
        self.impersonation_origin_id = env.user.id
        self.impersonation_active = True
        self.impersonation_start_time = fields.Datetime.now()

    # Mark session as modified
    self.modified = True

    registry = Registry(dbname)
    pre_uid = env['res.users'].search([("login", '=', login)]).id
    self.uid = None
    self.pre_login = login
    self.pre_uid = pre_uid

    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, pre_uid, {})
        # If 2FA is disabled we finalize immediately
        user = env['res.users'].browse(pre_uid)
        if not user._mfa_url():
            self.finalize(env)

    if request and request.session is self and request.db == dbname:
        request.env = odoo.api.Environment(request.env.cr, self.uid, self.context)
        request.update_context(**self.context)

    return pre_uid


def init(self, *args, **kwargs):
    """Initialize session with impersonation fields"""
    super(Session, self).init(*args, **kwargs)
    self.impersonation_origin_id = None
    self.impersonation_active = False
    self.impersonation_start_time = None


def switch_back_user(self):
    """Securely switch back to original user from impersonation"""
    if not self.impersonation_origin_id:
        return False

    original_uid = self.impersonation_origin_id

    # Clear impersonation state before switching
    self.impersonation_origin_id = None
    self.modified = True

    # Get original user's login
    with Registry(self.db).cursor() as cr:
        env = odoo.api.Environment(cr, original_uid, {})
        login = env['res.users'].browse(original_uid).login

        # Switch back using existing secure method
        return self.authenticate_without_password(self.db, login, env)


def check_impersonation_validity(self):
    """Check if the current impersonation session is valid"""
    if not self.impersonation_active or not self.impersonation_start_time:
        return False

    # Timeout check (defaults to 4 hours)
    max_age = timedelta(hours=4)
    now = fields.Datetime.now()
    impersonation_age = now - self.impersonation_start_time

    if impersonation_age > max_age:
        self.clear_impersonation()
        return False

    return True

def clear_impersonation(self):
    """Clear all impersonation-related session data"""
    self.impersonation_origin_id = None
    self.impersonation_active = False
    self.impersonation_start_time = None
    self.modified = True


Session.authenticate_without_password = authenticate_without_password
Session.init = init
Session.switch_back_user = switch_back_user
Session.check_impersonation_validity = check_impersonation_validity
Session.clear_impersonation = clear_impersonation
