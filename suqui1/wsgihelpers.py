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


from markupsafe import Markup
from suq1 import wsgihelpers
from suq1.wsgihelpers import errors_title, handle_cross_origin_resource_sharing, respond_json, wsgify
import webob.exc


__all__ = [
    'bad_request',
    'error',
    'errors_title',
    'forbidden',
    'handle_cross_origin_resource_sharing',
    'init_module',
    'internal_error',
    'method_not_allowed',
    'no_content',
    'not_found',
    'redirect',
    'respond_json',
    'unauthorized',
    'wsgify',
    ]

N_ = lambda message: message

errors_explanation = {
    400: N_("Request is faulty"),
    401: N_("Access is restricted to authorized persons."),
    403: N_("Access is forbidden."),
    404: N_("The requested page was not found."),
    }
errors_message = {
    401: N_("You must login to access this page."),
    }
templates = None  # from . import templates


def bad_request(ctx, **kw):
    return error(ctx, 400, **kw)


def error(ctx, code, **kw):
    response = webob.exc.status_map[code](headers = kw.pop('headers', None))
    if code != 204:  # No content
        body = kw.pop('body', None)
        if body is None:
            template_path = kw.pop('template_path', '/http-error.mako')
            explanation = kw.pop('explanation', None)
            if explanation is None:
                explanation = errors_explanation.get(code)
                explanation = ctx._(explanation) if explanation is not None else response.explanation
            message = kw.pop('message', None)
            if message is None:
                message = errors_message.get(code)
                if message is not None:
                    message = ctx._(message)
            title = kw.pop('title', None)
            if title is None:
                title = errors_title.get(code)
                title = ctx._(title) if title is not None else response.status
            body = templates.render(ctx, template_path,
                comment = kw.pop('comment', None),
                explanation = explanation,
                message = message,
                response = response,
                title = title,
                **kw)
        response.body = body.encode('utf-8') if isinstance(body, unicode) else body
    return response


def forbidden(ctx, **kw):
    return error(ctx, 403, **kw)


def init_module(components):
    wsgihelpers.init_module(components)

    global templates
    templates = components['templates']


def internal_error(ctx, **kw):
    return error(ctx, 500, **kw)


def method_not_allowed(ctx, **kw):
    return error(ctx, 405, **kw)


def no_content(ctx, headers = None):
    return error(ctx, 204, headers = headers)


def not_found(ctx, **kw):
    return error(ctx, 404, **kw)


def redirect(ctx, code = 302, location = None, **kw):
    assert location is not None
    location_str = location.encode('utf-8') if isinstance(location, unicode) else location
    response = webob.exc.status_map[code](headers = kw.pop('headers', None), location = location_str)
    body = kw.pop('body', None)
    if body is None:
        template_path = kw.pop('template_path', '/http-error.mako')
        explanation = kw.pop('explanation', None)
        if explanation is None:
            explanation = Markup(ctx._('{0} <a href="{1}">{1}</a>.')).format(
                ctx._(u"You'll be redirected to page"), location)
        message = kw.pop('message', None)
        if message is None:
            message = errors_message.get(code)
            if message is not None:
                message = ctx._(message)
        title = kw.pop('title', None)
        if title is None:
            title = ctx._("Redirection in progress...")
        body = templates.render(ctx, template_path,
            comment = kw.pop('comment', None),
            explanation = explanation,
            message = message,
            response = response,
            title = title,
            **kw)
    response.body = body.encode('utf-8') if isinstance(body, unicode) else body
    return response


def unauthorized(ctx, **kw):
    return error(ctx, 401, **kw)

