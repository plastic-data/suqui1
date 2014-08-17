# -*- coding: utf-8 -*-


# SuqUI1 -- An ad hoc Python toolbox for a web user interface
# By: Emmanuel Raviart <emmanuel@raviart.com>
#
# Copyright (C) 2009, 2010, 2011, 2012 Easter-eggs & Emmanuel Raviart
# Copyright (C) 2013, 2014 Easter-eggs, Etalab & Emmanuel Raviart
# https://github.com/eraviart/suqui1
#
# This file is part of SuqUI1.
#
# SuqUI1 is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# SuqUI1 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


"""Helpers for URLs"""


import re

from suq1 import urls
from suq1.urls import get_base_url, get_full_url, get_url, relative_query  # iter_full_urls
import webob

from . import wsgihelpers


__all__ = [
    'get_base_url',
    'get_full_url',
    'get_url',
    # 'iter_full_urls',
    'make_router',
    'relative_query',
    ]

contexts = None  # from ??? import contexts


def init_module(components):
    urls.init_module(components)

    global contexts
    contexts = components['contexts']


# To use in Python 3:
# def make_router(*routings, error_format = None):
def make_router(*routings, **kwargs):
    """Return a WSGI application that dispatches requests to controllers """
    error_format = kwargs.get('error_format')
    routes = []
    for routing in routings:
        methods, regex, app = routing[:3]
        if isinstance(methods, basestring):
            methods = (methods,)
        vars = routing[3] if len(routing) >= 4 else {}
        routes.append((methods, re.compile(unicode(regex)), app, vars))

    def router(environ, start_response):
        """Dispatch request to controllers."""
        req = webob.Request(environ)
        split_path_info = req.path_info.split('/')
        if split_path_info[0]:
            # When path_info doesn't start with a "/" this is an error or a attack => Reject request.
            # An example of an URL with such a invalid path_info: http://127.0.0.1http%3A//127.0.0.1%3A80/result?...
            ctx = contexts.Ctx(req)
            if error_format == 'json':
                headers = wsgihelpers.handle_cross_origin_resource_sharing(ctx)
                return wsgihelpers.respond_json(ctx,
                    dict(
                        apiVersion = '1.0',
                        error = dict(
                            code = 400,  # Bad Request
                            message = ctx._(u"Invalid path: {0}").format(req.path_info),
                            ),
                        ),
                    headers = headers,
                    )(environ, start_response)
            return wsgihelpers.bad_request(ctx, explanation = ctx._(u"Invalid path: {0}").format(
                req.path_info))(environ, start_response)
        for methods, regex, app, vars in routes:
            if methods is None or req.method in methods:
                match = regex.match(req.path_info)
                if match is not None:
                    if getattr(req, 'urlvars', None) is None:
                        req.urlvars = {}
                    req.urlvars.update(match.groupdict())
                    req.urlvars.update(vars)
                    req.script_name += req.path_info[:match.end()]
                    req.path_info = req.path_info[match.end():]
                    return app(req.environ, start_response)
        ctx = contexts.Ctx(req)
        if error_format == 'json':
            headers = wsgihelpers.handle_cross_origin_resource_sharing(ctx)
            return wsgihelpers.respond_json(ctx,
                dict(
                    apiVersion = '1.0',
                    error = dict(
                        code = 404,  # Not Found
                        message = ctx._(u"Path not found: {0}").format(req.path_info),
                        ),
                    ),
                headers = headers,
                )(environ, start_response)
        return wsgihelpers.not_found(ctx, explanation = ctx._(u"Page not found: {0}").format(
            req.path_info))(environ, start_response)

    return router

