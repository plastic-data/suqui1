# -*- coding: utf-8 -*-


# ElectData-UI -- Popularity-based data & datasets
# By: Emmanuel Raviart <emmanuel@raviart.com>
#
# Copyright (C) 2014 Emmanuel Raviart
# https://gitorious.org/electdata
#
# This file is part of ElectData-UI.
#
# ElectData-UI is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# ElectData-UI is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


"""WSGI Middlewares"""


import re
import urllib

from paste.cascade import Cascade
from paste.urlparser import StaticURLParser
import webob
from weberror.errormiddleware import ErrorMiddleware

from . import urls


conf = None  # from ??? import conf
contexts = None  # from ??? import contexts
lang_re = re.compile('^/(?P<lang>en|fr)(?=/|$)')
model = None  # from ??? import model
percent_encoding_re = re.compile('%[\dA-Fa-f]{2}')


def environment_setter(app):
    """WSGI middleware that sets request-dependant environment."""
    def set_environment(environ, start_response):
        req = webob.Request(environ)
        ctx = contexts.Ctx(req)
#        if conf['host_urls'] is not None:
#            host_url = req.host_url + '/'
#            if host_url not in conf['host_urls']:
#                return wsgihelpers.bad_request(ctx, explanation = ctx._('Web site not found.'))(environ,
#                    start_response)
        model.configure(ctx)
        try:
            return app(req.environ, start_response)
        except webob.exc.WSGIHTTPException as wsgi_exception:
            return wsgi_exception(environ, start_response)

    return set_environment


def init_module(components):
    global conf
    conf = components['conf']
    global contexts
    contexts = components['contexts']
    global model
    model = components['model']


def language_detector(app):
    """WSGI middleware that detect language symbol in requested URL or otherwise in Accept-Language header."""
    def detect_language(environ, start_response):
        req = webob.Request(environ)
        ctx = contexts.Ctx(req)
        match = lang_re.match(req.path_info)
        if match is None:
            ctx.lang = [
                req.accept_language.best_match([('fr-FR', 1), ('fr', 1), ('en-US', 1), ('en', 1)],
                    default_match = 'fr').split('-', 1)[0],
                ]
        else:
            ctx.lang = [match.group('lang')]
            req.script_name += req.path_info[:match.end()]
            req.path_info = req.path_info[match.end():]
        return app(req.environ, start_response)

    return detect_language


def request_query_encoding_fixer(app):
    """WSGI middleware that repairs a badly encoded query in request URL."""
    def fix_request_query_encoding(environ, start_response):
        req = webob.Request(environ)
        query_string = req.query_string
        if query_string is not None:
            try:
                urllib.unquote(query_string).decode('utf-8')
            except UnicodeDecodeError:
                req.query_string = percent_encoding_re.sub(
                    lambda match: urllib.quote(urllib.unquote(match.group(0)).decode('iso-8859-1').encode('utf-8')),
                    query_string)
        return app(req.environ, start_response)

    return fix_request_query_encoding


def wrap_app(app):
    """Encapsulate main WSGI application within WSGI middlewares."""
    # Initialize request-dependant environment.
    app = environment_setter(app)
    app = language_detector(app)

    # Repair badly encoded query in request URL.
    app = request_query_encoding_fixer(app)

    # CUSTOM MIDDLEWARE HERE (filtered by error handling middlewares)

    # Handle Python exceptions
    if not conf['debug']:
        app = ErrorMiddleware(app, global_conf, **conf['errorware'])

    if conf['static_files']:
        # Serve static files
        static_app = StaticURLParser(conf['static_files_dir'])
        app = Cascade([static_app, app])

    return app

