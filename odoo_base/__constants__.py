import os
import logging
from odoo.tools import config
from odoo.addons.odoo_base.__functions__ import str_to_bool

_logger = logging.getLogger('odoo')

"""
A boolean flag indicating whether the system is running in test mode.
This is determined based on the Odoo configuration settings.

Example:
    Check if the system is in test mode:
        from odoo.addons.odoo_base.__constants__ import IN_TEST_MODE
        if IN_TEST_MODE:
            # Perform test-specific logic
"""
IN_TEST_MODE = bool(config['test_enable'] or config['test_file'] or str_to_bool(os.getenv('IN_TEST_MODE', 'false')))
_logger.debug(f"[odoo_base] IN_TEST_MODE is {IN_TEST_MODE}")


"""
The ID of the tag used to identify 'MFG Sales Reps' on res_partner.
Can be queried like:
    SELECT id, name->>'en_US' as tag_name
    FROM res_partner_category
    WHERE name->>'en_US' = 'Mfg Sales Rep';

Example to check if the current user is a 'MFG Sales Rep':
        from odoo.addons.odoo_base.__constants__ import MFG_REP_CATEGORY_ID
        mfg_rep = MFG_REP_CATEGORY_ID in partner.category_id.ids
"""
MFG_REP_CATEGORY_ID =  8


"""
A set of view XML IDs that should be excluded from XML import.

Explanation(s):
    - sale_order_portal_content_inherit_website_sale: Because custom_web overwrites Odoo's
    /my/orders view, we need to skip this one because it depends on xpaths which are no
    longer present.
"""
BLOCKED_VIEW_XML_IDS = { 'sale_order_portal_content_inherit_website_sale' }
