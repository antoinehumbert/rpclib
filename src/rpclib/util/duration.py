
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

import datetime

class XmlDuration(object):
    """Handles the conversion between soap duration and python timedelta."""
    __seq1 = [("Y", "years"), ("M", "months"), ("D", "days")]
    __seq2 = [("H", "hours"), ("M", "minutes"), ("S", "seconds")]

    def __init__(self, years=0, months=0, days=0, hours=0, minutes=0, seconds=0,
                                                                negative=False):
        self.years = years
        self.months = months
        self.days = days
        self.hours = hours
        self.minutes = minutes
        self.seconds = seconds
        self.negative = negative

    def as_timedelta(self):
        seconds = int(self.seconds)
        microseconds = 1000000 * (self.seconds - seconds)
        days = self.days + self.months * 30 + self.years * 365
        res = datetime.timedelta(days=days,
                                 hours=self.hours,
                                 minutes=self.minutes,
                                 seconds=seconds,
                                 microseconds=microseconds)
        if self.negative:
            res = -res
        return res

    def __str__(self):
        def tostr(seq):
            str = ""
            for s, attr in seq:
                n = getattr(self, attr)
                assert n >= 0 and (n == round(n) or attr == "seconds")
                if n:
                    str += (n == round(n) and "%i%s" or "%s%s") % (n, s)

            return str

        s1 = tostr(self.__seq1)
        s2 = tostr(self.__seq2)
        if s2:
            ret = "P%sT%s" % (s1, s2)
        elif s1:
            ret = "P%s" % s1
        else:
            ret = "PT0S"

        if self.negative:
            ret = "-" + ret

        return ret

    def __repr__(self):
        return "%s(%s, %s, %s, %s, %s, %s, %s)" % (
            self.__class__.__name__,
            self.years, self.months, self.days,
            self.hours, self.minutes, self.seconds,
            self.negative
        )

    @classmethod
    def parse(cls, value):
        """Convert a value to a XmlDuration object.

        Valid types are timedelta, XmlDuration and string.
        """
        if isinstance(value, datetime.timedelta):
            return cls.from_timedelta(value)
        elif isinstance(value, cls):
            return value
        else:
            return cls.from_string(str(value))

    @classmethod
    def from_timedelta(cls, timedelta):
        if timedelta.days < 0:
            timedelta = -timedelta
            negative = True
        else:
            negative = False
        seconds = timedelta.seconds % 60
        minutes = timedelta.seconds / 60
        hours = minutes / 60
        minutes = minutes % 60
        seconds = float(seconds) + timedelta.microseconds / 1000000
        years = timedelta.days / 365
        months = (timedelta.days - 365 * years) / 30
        days = timedelta.days - 365 * years - 30 * months
        return cls(years=years, months=months, days=days,
                   hours=hours, minutes=minutes, seconds=seconds, negative=negative)

    @classmethod
    def from_string(cls, string):
        orig_str = string
        ret = cls()

        def parse_token(string):
            n = "0"

            for i in range(len(string)):
                if string[i].isdigit() or string[i] == ".":
                    n += string[i]
                else:
                    break

            return (float(n), string[i], string[i + 1:])

        def parse_seq(string, seq):
            i = 0
            while string:
                n, s, string = parse_token(string)

                while i < len(seq):
                    s1, attr = seq[i]
                    i += 1
                    if s == s1:
                        if n >= 0 and (n == round(n) or attr == "seconds"):
                            setattr(ret, attr, n)
                            break
                        else:
                            raise Exception
                else:
                    raise Exception

        try:
            if string.startswith("-"):
                ret.negative = True
                string = string[1:]

            if string.startswith("P"):
                string = string[1:]
            else:
                raise Exception

            str1, _, str2 = string.partition("T")
            if not (str1 or str2):
                raise Exception
            parse_seq(str1, cls.__seq1)
            parse_seq(str2, cls.__seq2)

        except:
            raise ValueError("Duration %r not in correct format" % orig_str)

        return ret
