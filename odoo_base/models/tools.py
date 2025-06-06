import logging
from odoo.tools.convert import xml_import
from odoo.addons.odoo_base.__constants__ import BLOCKED_VIEW_XML_IDS

_logger = logging.getLogger(__name__)


# Stash the original
_orig_tag_root = xml_import._tag_root

def _patched_tag_root(self, el):
    """
    Block from loading any <template> or <record> whose @id is in our skip list,
    (BLOCKED_VIEW_XML_IDS) then proceed with the normal tag dispatch.
    """
    # el is an lxml element whose children are <template> / <record> / etc.
    new_children = []
    for rec in el:
        rid = rec.get('id')
        if rid in BLOCKED_VIEW_XML_IDS:
            _logger.info("Skipping XML import of view %s", rid)
            # Do not include rec in new_children: it will never be loaded
            continue
        new_children.append(rec)
    # Replace the children of el with our filtered list
    el[:] = new_children

    # Now call the original on the filtered element
    return _orig_tag_root(self, el)

# Install the patch
xml_import._tag_root = _patched_tag_root
