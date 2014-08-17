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


"""Context loaded and saved in WSGI requests"""


import os

import pkg_resources
from suq1 import contexts


__all__ = [
    'Ctx',
    'init_module',
    ]

conv = None  # from ??? import conv


class Ctx(contexts.Ctx):
    default_values = contexts.Ctx.default_values.copy()
    default_values.update(dict(
        _session = UnboundLocalError,
        _user = UnboundLocalError,
        ))
    env_keys = contexts.Ctx.env_keys + ('_session', '_user')
    translators_infos = contexts.Ctx.translators_infos + [
        ('suqui1', os.path.join(pkg_resources.get_distribution('suqui1').location, 'suqui1', 'i18n')),
        ]

    def session_del(self):
        del self._session
        package_name = self.conf['package_name']
        if self.req is not None and self.req.environ.get(package_name) is not None \
                and '_session' in self.req.environ[package_name]:
            del self.req.environ[package_name]['_session']

    def session_get(self):
        if self._session is UnboundLocalError:
            if self.req is None:
                self.session = None
            else:
                from . import model
                session, error = conv.pipe(
                    conv.input_to_uuid_str,
                    conv.not_none,
                    model.Session.token_to_instance,
                    )(self.req.cookies.get(conf['cookie']), state = self)
                self.session = session if error is None else None
        return self._session

    def session_set(self, session):
        self._session = session
        if self.req is not None:
            self.req.environ.setdefault(self.conf['package_name'], {})['_session'] = session

    session = property(session_get, session_set, session_del)

    def user_del(self):
        del self._user
        package_name = self.conf['package_name']
        if self.req is not None and self.req.environ.get(package_name) is not None \
                and '_user' in self.req.environ[package_name]:
            del self.req.environ[package_name]['_user']

    def user_get(self):
        return self._user

    def user_set(self, user):
        self._user = user
        if self.req is not None:
            self.req.environ.setdefault(self.conf['package_name'], {})['_user'] = user

    user = property(user_get, user_set, user_del)


def init_module(components):
    contexts.init_module(components)

    global conv
    conv = components['conv']

