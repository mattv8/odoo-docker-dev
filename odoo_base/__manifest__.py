# -*- coding: utf-8 -*-
{
    'name': "odoo_base",

    'summary': "Base implementation to centralize custom extensions"
               "of customizations to Odoo core or Enterprise",

    'description': """
    """,

    'author': "Custom Odoo Development",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail'],

    'assets': {
        'web.assets_backend': [
            'odoo_base/static/src/js/password_reveal_widget.js',
            'odoo_base/static/src/xml/password_reveal_widget.xml',
        ],
        'web.assets_frontend': [
        ],
    },

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
    ],
    'license': 'LGPL-3',
}
