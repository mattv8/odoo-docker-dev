from odoo import models, api

from odoo.addons.odoo_base import __functions__ as fn

class OdooBaseAbstracts(models.AbstractModel):
    """
    This model is designed to be inherited by other models and is particularly useful
    for exposing methods that can be called directly from XML templates, such as for
    encryption or decryption operations within the Odoo framework.
    """
    _name = 'odoo_base.abstracts'
    _description = 'Odoo Base Abstract Models'

    @api.model
    def fernet_encrypt(self, plaintext):
        """Encrypt a string using Fernet encryption with the database secret."""
        secret = fn._get_database_secret(self.env)
        return fn.fernet_encrypt(secret, plaintext)
