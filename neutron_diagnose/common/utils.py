#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.
#

import re
import netaddr

from oslo_utils import uuidutils

from neutron_diagnose.common import exceptions


def validate_uuid(data):
    """Validate data is UUID like."""

    if not uuidutils.is_uuid_like(data):
        raise exceptions.DiagnoseException(
            "'%s' is not a valid UUID" % data)


def validate_no_whitespace(data):
    """Validates that input has no whitespace."""
    if re.search(r'\s', data):
        raise exceptions.DiagnoseException(
            "'%s' contains whitespace" % data)
    return data


def validate_ip_address(data, valid_values=None):
    """Validate data is an IP address."""

    msg = None
    try:
        # netaddr.core.ZEROFILL is only applicable to IPv4.
        # it will remove leading zeros from IPv4 address octets.
        ip = netaddr.IPAddress(validate_no_whitespace(data),
                               flags=netaddr.core.ZEROFILL)
        # The followings are quick checks for IPv6 (has ':') and
        # IPv4.  (has 3 periods like 'xx.xx.xx.xx')
        # NOTE(yamamoto): netaddr uses libraries provided by the underlying
        # platform to convert addresses.  For example, inet_aton(3).
        # Some platforms, including NetBSD and OS X, have inet_aton
        # implementation which accepts more varying forms of addresses than
        # we want to accept here.  The following check is to reject such
        # addresses.  For Example:
        #   >>> netaddr.IPAddress('1' * 59)
        #   IPAddress('199.28.113.199')
        #   >>> netaddr.IPAddress(str(int('1' * 59) & 0xffffffff))
        #   IPAddress('199.28.113.199')
        #   >>>
        if ':' not in data and data.count('.') != 3:
            msg = "'%s' is not a valid IP address" % data
        # A leading '0' in IPv4 address may be interpreted as an octal number,
        # e.g. 011 octal is 9 decimal. Since there is no standard saying
        # whether IP address with leading '0's should be interpreted as octal
        # or decimal, hence we reject leading '0's to avoid ambiguity.
        elif ip.version == 4 and str(ip) != data:
            msg = ("'%(data)s' is not an accepted IP address, "
                   "'%(ip)s' is recommended") % {"data": data, "ip": ip}
    except Exception:
        msg = "'%s' is not a valid IP address" % data
    if msg:
        raise exceptions.DiagnoseException(msg)
