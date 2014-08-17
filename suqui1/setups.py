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


"""Helpers to handle setups and upgrades"""


from suq1 import objects, setups

from . import accesses, contexts, middlewares, urls, wsgihelpers


def configure(ctx):
    setups.configure(ctx)


def init(components):
    accesses.init_module(components)
    contexts.init_module(components)
    middlewares.init_module(components)
    objects.init_module(components)
    urls.init_module(components)
    wsgihelpers.init_module(components)

