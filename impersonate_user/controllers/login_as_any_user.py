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
from odoo import http
from odoo.http import request

import logging
_logger = logging.getLogger(__name__)


class UserSwitch(http.Controller):
    """This is a controller to switch user and switch back to admin
        user_switch:
            this function is to check weather the user is admin or not
        switch_admin:
            function to switch back to admin
    """

    @http.route('/switch/user', type='json', auth='public')
    def user_switch(self):
        """
            Summary:
                function to check weather the user is admin
            Return:
                weather the current user is admin or not
        """
        return request.env.user._is_admin()

    @http.route('/switch/back', type='http', auth='user', website=True)
    def switch_back(self):
        """Switch back to original user from portal impersonation"""
        session = request.session

        # Validate impersonation state exists
        if not session.get('impersonation_origin_id'):
            return request.redirect('/web', 303)

        try:
            # Check if impersonation session is still valid
            if not session.check_impersonation_validity():
                session.clear_impersonation()
                return request.redirect('/web', 303)

            if session.switch_back_user():
                request.env.user.context_get()
                return request.redirect('/web')
            else:
                session.clear_impersonation()
                return request.redirect('/web', 303)

        except Exception:
            # Only log the error internally; do not expose details to client
            _logger.exception("Error during user switch-back")
            session.clear_impersonation()
            return request.redirect('/web', 303)
