# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo - Sentry connector
#    Copyright (C) 2014 Mohammed Barsi.
#    Copyright (C) 2016 Miku Laitinen (avoin.systems).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import traceback
import logging
import sys
import odoo.service.wsgi_server
import odoo.addons.web.controllers.main
import odoo.addons.report.controllers.main
import odoo.http
import odoo.tools.config as config
import odoo.osv.osv
import odoo.exceptions
from odoo.http import request
from raven import Client
from raven.handlers.logging import SentryHandler
from raven.middleware import Sentry
from raven.conf import setup_logging, EXCLUDE_LOGGER_DEFAULTS

# Do NOT use the logger. It will create an endless recursion loop.
_logger = logging.getLogger(__name__)


CLIENT_DSN = config.get('sentry_client_dsn', '').strip()
ENABLE_LOGGING = config.get('sentry_enable_logging', False)
ALLOW_ORM_WARNING = config.get('sentry_allow_orm_warning', False)
INCLUDE_USER_CONTEXT = config.get('sentry_include_context', False)
ERROR_LEVEL = config.get('sentry_error_level', 'WARNING')
ODOO_MAJOR_VERSION = odoo.release.major_version
ODOO_VERSION = odoo.release.version
RELEASE = config.get('sentry_release', False)


def get_user_context():
    """
        get the current user context, if possible
    """
    cxt = {}
    if not request:
        return cxt
    session = getattr(request, 'session', {})
    cxt.update({
        'session': {
            'context': session.get('context', {}),
            'db': session.get('db', None),
            'login': session.get('login', None),
            'password': session.get('uid', None),
        },
    })
    return cxt


def serialize_exception(e):
    """
        overrides `odoo.http.serialize_exception`
        in order to log orm exceptions.
    """
    if isinstance(e, (
        odoo.osv.osv.except_osv,
        odoo.exceptions.Warning,
        odoo.exceptions.AccessError,
        odoo.exceptions.AccessDenied,
        )):
        if INCLUDE_USER_CONTEXT:
            client.extra_context(get_user_context())
        client.captureException(sys.exc_info())
    return odoo.http.serialize_exception(e)


class ContextSentryHandler(SentryHandler):
    """
        extends SentryHandler, to capture logs only if
        `sentry_enable_logging` config options set to true
    """
    def emit(self, rec):
        if INCLUDE_USER_CONTEXT:
            client.extra_context(get_user_context())
        super(ContextSentryHandler, self).emit(rec)

# Get default context and tags from the Odoo configuration
tags = dict(odoo_major_version=ODOO_MAJOR_VERSION, odoo_version=ODOO_VERSION)
context = dict()
for key, value in config.options.iteritems():
    if key.startswith('sentry_context_tags_'):
        tags[key.replace('sentry_context_tags_', '')] = value
        continue
    elif key.startswith('sentry_context_'):
        context[key.replace('sentry_context_', '')] = value

# Get options from the Odoo configuration
options = {key.replace('sentry_options_', ''): value
           for key, value in config.options.iteritems()
           if key.startswith('sentry_options_')}
if RELEASE:
    options['release'] = RELEASE
options['context'] = context
options['tags'] = tags

client = Client(CLIENT_DSN, **options)


if ENABLE_LOGGING:
    # future enhancement: add exclude loggers option
    EXCLUDE_LOGGER_DEFAULTS += ('werkzeug', )
    handler = ContextSentryHandler(client, level=getattr(logging, ERROR_LEVEL))
    setup_logging(handler, exclude=EXCLUDE_LOGGER_DEFAULTS)

if ALLOW_ORM_WARNING:
    odoo.addons.web.controllers.main._serialize_exception = serialize_exception
    odoo.addons.report.controllers.main._serialize_exception = serialize_exception

# wrap the main wsgi app
odoo.service.wsgi_server.application = Sentry(odoo.service.wsgi_server.application, client=client)

if INCLUDE_USER_CONTEXT:
    client.extra_context(get_user_context())
# fire the first message
client.captureMessage('Starting Odoo Server')
