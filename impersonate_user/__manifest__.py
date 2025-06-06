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
{
    'name': 'Impersonate User',
    'version': '17.0.1.0.1',
    'category': 'Extra Tools',
    'summary': 'Admin can log in as any user',
    'description': 'The "Login As Any User" module allows administrators to '
                   'switch to any user account without the need for '
                   'passwords or other authentication.',
    'author': 'Cybrosys Techno Solution',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solution',
    'website': 'https://www.cybrosys.com',
    'depends': ['web', 'website', 'portal'],
    'data': [
        'security/ir.model.access.csv',
        'wizards/user_selection_views.xml',
        'views/portal_templates.xml',
        'views/res_partner.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'impersonate_user/static/src/js/systray_button.js',
            'impersonate_user/static/src/xml/systray_button_templates.xml',
            'impersonate_user/static/src/js/impersonate_user_button.js',
            'impersonate_user/static/src/xml/impersonate_user_button.xml',
        ],
        'web.qunit_suite_tests': [
            'impersonate_user/static/src/tests/mock_switch_user.js',
        ]},
    'license': 'LGPL-3',
    'installable': True,
    'auto-install': False,
    'application': False,
}
