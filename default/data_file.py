import os
import uuid
import json
import logging
from datetime import date
from zipfile import ZipFile, ZIP_DEFLATED
from django.conf import settings
from ocdskit.util import json_dumps, json_loads, is_release_package, is_record_package
from django.utils.translation import gettext as _

logger = logging.getLogger(__name__)


class DataFile:
    """
    A data file on the server, that was either uploaded by a user or generated in response to a request.
    """

    """
    The separator between the prefix and ID of the file.
    """
    sep = '-'

    def __init__(self, prefix, ext, id=None, folder=None, original_name=None, data=None, valid=True,
                 invalid_reason=None):
        if len(prefix) > 20:
            prefix = prefix[:20 + 1]

        self.prefix = prefix
        self.ext = ext
        self.id = id or str(uuid.uuid4())
        self.original_name = original_name
        self.valid = valid
        self.invalid_reason = invalid_reason

        if folder is not None:
            self.folder = folder
        else:
            self.folder = '{:%Y-%m-%d}'.format(date.today())

    def as_dict(self):
        return self.__dict__

    def name_with_suffix(self, suffix):
        """
        Returns the file's name, with a suffix before its extension.

        :param str suffix: a suffix to the file's name
        """
        return self.prefix + self.sep + self.id + self.sep + suffix + self.ext

    @property
    def path(self):
        """
        Returns the full path to the file.
        """
        return os.path.join(self._directory, self._name)

    @property
    def url(self):
        """
        Returns the URL path to the file.
        """
        return '/result/{}/{}/'.format(self.folder, self.id)

    @property
    def size(self):
        """
        Returns the size of the file.
        """
        return os.path.getsize(self.path)

    def json(self):
        """
        Returns the file's parsed JSON contents.
        """
        with open(self.path, encoding='utf-8') as f:
            return json_loads(f.read())

    def write(self, file):
        """
        Write another file's contents to this file.

        :param file: a ``django.core.files.File`` object
        """
        self._makedirs()
        with open(self.path, 'wb') as f:
            for chunk in file.chunks():
                f.write(chunk)

    def write_json_to_zip(self, files):
        """
        Writes JSON data to a ZIP file.

        :param files: a dict in which keys are file names and values are file contents, or a generator that yields
                      tuples of file names and file contents.
        """
        self._makedirs()
        if isinstance(files, dict):
            files = files.items()
        for name, content in files:
            with ZipFile(self.path, 'a', compression=ZIP_DEFLATED) as zipfile:
                zipfile.writestr(name, json_dumps(content) + '\n')

    def is_valid(self, file, ocds_type=None):
        try:
            data = json_loads(file.read())
            if ocds_type == 'release-package':
                if not is_release_package(data):
                    self.valid = False
                    self.invalid_reason = _('Not a release package')
                    return False
            elif ocds_type == 'record-package':
                if not is_record_package(data):
                    self.valid = False
                    self.invalid_reason = _('Not a record package')
                    return False
            self.valid = True
            return True
        except json.JSONDecodeError:
            self.valid = False
            self.invalid_reason = _('Error decoding json')
            logger.debug('Error decoding file {}'.format(file.name))
        return False

    @property
    def _name(self):
        """
        Returns the file's name.
        """
        return self.prefix + self.sep + self.id + self.ext

    @property
    def _directory(self):
        """
        Returns the directory containing the file.
        """
        return os.path.join(settings.MEDIA_ROOT, self.folder)

    def _makedirs(self):
        """
        Creates the directory to contain the file.
        """
        os.makedirs(self._directory, exist_ok=True)
