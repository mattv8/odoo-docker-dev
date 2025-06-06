import logging
import os
import io
from odoo.addons.odoo_base.__functions__ import str_to_bool
from odoo import models, tools, http

_logger = logging.getLogger(__name__)

try:
    SUPPRESS_FS_ERR = bool(str_to_bool(os.getenv('SUPPRESS_FS_ERR', 'false')))
except ValueError:
    SUPPRESS_FS_ERR = False

try:
    SHOW_FULLPATH = bool(str_to_bool(os.getenv('SHOW_FULLPATH', 'false')))
except ValueError:
    SHOW_FULLPATH = False

MAX_PATH_LENGTH = 50

# Save the original method for later use
_original_from_attachment = http.Stream.from_attachment


class EmptyStream(io.BytesIO):
    """ Mimics Odoo's http.Stream but returns an empty response when a file is missing. """

    def __init__(self, path=""):
        super().__init__(b"")                       # Empty content
        self.path = path
        self.type = "path"                          # Mimic the expected type
        self.size = 0                               # Indicate an empty file
        self.mimetype = "application/octet-stream"  # Generic binary MIME type


@classmethod
def safe_from_attachment(cls, record):
    """ Wraps Odoo's from_attachment to suppress errors when files are missing. """
    try:
        return _original_from_attachment(record)
    except FileNotFoundError:
        if SUPPRESS_FS_ERR:
            data_dir = tools.config['data_dir']
            relative_path = os.path.relpath(
                record.store_fname, data_dir) if data_dir else record.store_fname
            display_path = relative_path if SHOW_FULLPATH else (
                relative_path[:MAX_PATH_LENGTH] + '...' if len(relative_path) > MAX_PATH_LENGTH else relative_path)

            _logger.info(
                "File not found: %s (SUPPRESS_FS_ERR=%s)",
                display_path,
                SUPPRESS_FS_ERR,
            )

            return EmptyStream(path=relative_path)
        raise


# Patch the method
http.Stream.from_attachment = safe_from_attachment


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    def _file_read(self, fname):
        """
        Overrides _file_read() to suppress FileNotFoundError when SUPPRESS_FS_ERR is set.
        """
        full_path = self._full_path(fname)

        # Get the relative path
        data_dir = tools.config['data_dir']
        relative_path = os.path.relpath(
            full_path, data_dir) if data_dir else full_path
        display_path = relative_path if SHOW_FULLPATH else (
            relative_path[:MAX_PATH_LENGTH] + '...' if len(relative_path) > MAX_PATH_LENGTH else relative_path)

        if SUPPRESS_FS_ERR:
            try:
                with open(full_path, 'rb') as f:
                    return f.read()
            except FileNotFoundError:
                _logger.info(
                    "File not found: %s (SUPPRESS_FS_ERR=%s)",
                    display_path,
                    SUPPRESS_FS_ERR,
                )
                return b""  # Return empty content
            except (IOError, OSError):
                _logger.info(
                    "_file_read encountered an issue reading %s. Returning empty content.",
                    relative_path,
                    exc_info=True
                )
                return b""
        else:
            return super(IrAttachment, self)._file_read(fname)
