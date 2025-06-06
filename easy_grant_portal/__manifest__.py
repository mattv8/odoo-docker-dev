# -*- coding: utf-8 -*-
{
    'name': "Easy Grant Portal",
    'summary': "Easily manage portal access for partners",
    'description': """
    This module provides an easy way to grant and revoke portal access for partners.
    Features include:
    - Grant/Revoke portal access buttons in partner views
    - Confirmation modal with revocation reason tracking
    - Portal access status indicators
    - Automatic email invitations when granting access
    """,
    'author': "Odoo Community",
    'website': "https://github.com/OCA/server-tools",
    'category': 'Extra Tools',
    'version': '17.0.1.0.0',
    'license': 'LGPL-3',
    'depends': ['base', 'portal', 'auth_signup'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'easy_grant_portal/static/src/js/res_partner.js',
        ],
    },
    'installable': True,
    'auto_install': False,
}
