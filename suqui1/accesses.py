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


import calendar
import collections
import datetime

from suq1 import accesses, objects

from . import urls


__all__ = [
    'Account',
    'AuthenticationAccount',
    'Session',
    ]

conv = None  # from ??? import conv
model = None  # from ??? import model


class Account(accesses.Account):
    admin = False

    @classmethod
    def ensure_indexes(cls):
        super(Account, cls).ensure_indexes()
        cls.ensure_index('admin', sparse = True)

    @classmethod
    def get_admin_class_full_url(cls, ctx, *path, **query):
        return urls.get_full_url(ctx, 'admin', 'accounts', *path, **query)

    @classmethod
    def get_admin_class_url(cls, ctx, *path, **query):
        return urls.get_url(ctx, 'admin', 'accounts', *path, **query)

    def get_admin_full_url(self, ctx, *path, **query):
        if self._id is None:
            return None
        return self.get_admin_class_full_url(ctx, self.url_name, self._id, *path, **query)

    def get_admin_url(self, ctx, *path, **query):
        if self._id is None:
            return None
        return self.get_admin_class_url(ctx, self.url_name, self._id, *path, **query)

    def get_title(self, ctx):
        return self.full_name or self.email or self._id

#    @classmethod
#    def make_id_or_slug_or_words_to_instance(cls):
#        def id_or_slug_or_words_to_instance(value, state = None):
#            if value is None:
#                return value, None
#            if state is None:
#                state = conv.default_state
#            id, error = conv.str_to_object_id(value, state = state)
#            if error is None:
#                self = cls.find_one(id, as_class = collections.OrderedDict)
#            else:
#                self = cls.find_one(dict(slug = value), as_class = collections.OrderedDict)
#            if self is None:
#                words = sorted(set(value.split(u'-')))
#                instances = list(cls.find(
#                    dict(
#                        words = {'$all': [
#                            re.compile(u'^{}'.format(re.escape(word)))
#                            for word in words
#                            ]},
#                        ),
#                    as_class = collections.OrderedDict,
#                    ).limit(2))
#                if not instances:
#                    return value, state._(u"No account with ID, slug or words: {0}").format(value)
#                if len(instances) > 1:
#                    return value, state._(u"Too much accounts with words: {0}").format(u' '.join(words))
#                self = instances[0]
#            return self, None
#        return id_or_slug_or_words_to_instance


class AuthenticationAccount(objects.Initable):
    """A fake account created from authentication JSON"""
    access_token = None
    admin = False
    browser_access_token = None
    email = None
    email_verified = None  # Datetime of last email verification
    full_name = None

    def get_admin_url(self, ctx, *path, **query):
        return None

    def to_browser_json(self):
        self_json = self.__dict__.copy()
        self_json.pop('access_token', None)
        return self_json


class Session(objects.JsonMonoClassMapper, objects.Mapper, objects.SmartWrapper):
    _user = UnboundLocalError
    authentication = None
    collection_name = 'sessions'
    expiration = None
    state = None  # Token used to synchronize with Weotu during authentication.
    synchronizer_token = None  # token used to prevent CSRF
    token = None  # the cookie token
    user_id = None

    @classmethod
    def ensure_indexes(cls):
        super(Session, cls).ensure_indexes()
        cls.ensure_index('expiration')
        cls.ensure_index('state', sparse = True, unique = True)
        cls.ensure_index('token', unique = True)

    @classmethod
    def get_admin_class_full_url(cls, ctx, *path, **query):
        return urls.get_full_url(ctx, 'admin', 'sessions', *path, **query)

    @classmethod
    def get_admin_class_url(cls, ctx, *path, **query):
        return urls.get_url(ctx, 'admin', 'sessions', *path, **query)

    def get_admin_full_url(self, ctx, *path, **query):
        if self.token is None:
            return None
        return self.get_admin_class_full_url(ctx, self.token, *path, **query)

    def get_admin_url(self, ctx, *path, **query):
        if self.token is None:
            return None
        return self.get_admin_class_url(ctx, self.token, *path, **query)

    def get_title(self, ctx):
        user = self.user
        if user is None:
            return ctx._(u'Session {0}').format(self.token)
        return ctx._(u'Session {0} of {1}').format(self.token, user.get_title(ctx))

    @classmethod
    def remove_expired(cls, ctx):
        for self in cls.find(
                dict(expiration = {'$lt': datetime.datetime.utcnow()}),
                as_class = collections.OrderedDict,
                ):
            self.delete(ctx)

    def to_bson(self):
        self_bson = self.__dict__.copy()
        self_bson.pop('_user', None)
        return self_bson

    def to_browser_json(self):
        self_json = self.to_json().copy()
        self_json.pop('authentication', None)
        return self_json

    @classmethod
    def token_to_instance(cls, value, state = None):
        if value is None:
            return value, None
        if state is None:
            state = conv.default_state

        # First, delete expired sessions.
        cls.remove_expired(state)

        self = cls.find_one(dict(token = value), as_class = collections.OrderedDict)
        if self is None:
            return value, state._(u"No session with UUID {0}").format(value)
        return self, None

    def turn_to_json_attributes(self, state):
        value, error = conv.object_to_clean_dict(self, state = state)
        if error is not None:
            return value, error
        if value.get('draft_id') is not None:
            value['draft_id'] = unicode(value['draft_id'])
        expiration = value.get('expiration')
        if expiration is not None:
            value['expiration'] = expiration.isoformat() + 'Z'
        id = value.pop('_id', None)
        if id is not None:
            value['id'] = unicode(id)
        if value.get('published') is not None:
            value['published'] = int(calendar.timegm(value['published'].timetuple()) * 1000)
        if value.get('updated') is not None:
            value['updated'] = int(calendar.timegm(value['updated'].timetuple()) * 1000)
        return value, None

    @property
    def user(self):
        if self._user is UnboundLocalError:
            self._user = model.Account.find_one(self.user_id, as_class = collections.OrderedDict) \
                if self.user_id is not None \
                else None
        return self._user


def init_module(components):
    accesses.init_module(components)

    global conv
    conv = components['conv']
    global model
    model = components['model']

