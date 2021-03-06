
#
# rpclib - Copyright (C) Rpclib contributors.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301
#

"""
The rpclib.model.table module is EXPERIMENTAL. Please report any issues you
might find.
"""

import logging
logger = logging.getLogger(__name__)

import sqlalchemy
from sqlalchemy import Column

from sqlalchemy.ext.declarative import DeclarativeMeta

from sqlalchemy.dialects.postgresql import UUID

from rpclib.model.complex import TypeInfo
from rpclib.model.complex import ComplexModelBase
from rpclib.model.complex import ComplexModelMeta
from rpclib.model import primitive
from rpclib.model import complex

_type_map = {
    sqlalchemy.Text: primitive.String,
    sqlalchemy.String: primitive.String,
    sqlalchemy.Unicode: primitive.String,
    sqlalchemy.UnicodeText: primitive.String,

    sqlalchemy.Float: primitive.Float,
    sqlalchemy.Numeric: primitive.Decimal,
    sqlalchemy.Integer: primitive.Integer,
    sqlalchemy.SmallInteger: primitive.Integer,

    sqlalchemy.Boolean: primitive.Boolean,
    sqlalchemy.DateTime: primitive.DateTime,
    sqlalchemy.orm.relation: complex.Array,
    UUID: primitive.String
}

def _process_item(v):
    if v.type in _type_map:
        rpc_type = _type_map[v.type]
    elif type(v.type) in _type_map:
        rpc_type = _type_map[type(v.type)]
    else:
        raise Exception("soap_type was not found. maybe _type_map needs a new "
                        "entry. %r" % v)

    return rpc_type

class TableSerializerMeta(DeclarativeMeta,ComplexModelMeta):
    def __new__(cls, cls_name, cls_bases, cls_dict):
        if cls_dict.get("__type_name__", None) is None:
            cls_dict["__type_name__"] = cls_name

        if cls_dict.get("_type_info", None) is None:
            cls_dict["_type_info"] = _type_info = TypeInfo()

            for k, v in cls_dict.items():
                if (not k.startswith('__')) and isinstance(v, Column):
                    _type_info[k] = _process_item(v)

            table = cls_dict.get('__table__', None)
            if not (table is None):
                for c in table.c:
                    _type_info[c.name] = _process_item(c)

            # mixin inheritance
            for b in cls_bases:
                for k,v in vars(b).items():
                    if isinstance(v, Column):
                        _type_info[k] = _process_item(v)

            # same table inheritance
            for b in cls_bases:
                table = getattr(b, '__table__', None)

                if not (table is None):
                    for c in table.c:
                        _type_info[c.name] = _process_item(c)

        return DeclarativeMeta.__new__(cls, cls_name, cls_bases, cls_dict)

class TableSerializer(ComplexModelBase):
    __metaclass__ = TableSerializerMeta
    _decl_class_registry = {}

    @classmethod
    def customize(cls, **kwargs):
        cls_name, cls_bases, cls_dict = ComplexModelBase._s_customize(
                                                                  cls, **kwargs)

        retval = ComplexModelMeta.__new__(ComplexModelMeta, cls_name,
                                                            cls_bases, cls_dict)

        return retval
