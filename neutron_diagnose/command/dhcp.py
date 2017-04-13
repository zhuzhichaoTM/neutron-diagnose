#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#

from neutron_diagnose.command import commandmanager
from neutron_diagnose.common import exceptions
from neutron_diagnose.common import utils
from neutron_diagnose.i18n import _


class CheckVmIp(commandmanager.ShowOne):
    _description = _("Check the the reason that specified "
                     "instance can't get ip address.")

    def get_parser(self, prog_name):
        parser = super(CheckVmIp, self).get_parser(prog_name)
        parser.add_argument(
            'instance_id',
            metavar='<instance-id>',
            help=_('the instance uuid.'),
        )
        parser.add_argument(
            'fixed_ip',
            metavar='<fixed-ip>',
            help=_('the fixed ip of instance.'),
        )
        return parser

    def take_action(self, parsed_args):
        utils.validate_uuid(parsed_args.instance_id)
        utils.validate_ip_address(parsed_args.fixed_ip)

        compute_client = self.app.client_manager.compute
        network_client = self.app.client_manager.network
        ssh_client = self.app.client_manager.ssh

        server = compute_client.servers.get(parsed_args.instance_id)
        project_id = server.tenant_id
        host = server._info.get('OS-EXT-SRV-ATTR:host')
        if not host:
            raise exceptions.DiagnoseException(
                'the instance: %s has no host.', server.id)
        network_name = None
        port_mac = None
        port_id = None
        for network, details in server._info.get('addresses', dict()).items():
            for ip_infs in details:
                if ip_infs.get('addr') == parsed_args.fixed_ip:
                    network_name = network_name
                    port_mac = ip_infs.get('OS-EXT-IPS-MAC:mac_addr')
        port_filters = {'device_owner': 'compute:nova',
                        'device_id': server.id,
                        'mac_address': port_mac,
                        'project_id': project_id}
        ports = network_client.ports(**port_filters)
        port_len = 0
        for port in ports:
            port_len += 1
            fixed_ips = port.fixed_ips
            for ip_info in fixed_ips:
                if ip_info['ip_address'] == parsed_args.fixed_ip:
                    port_id = port.id
                    break

        if port_len > 1:
            raise exceptions.DiagnoseException(
                'The tenant: %s has more one instances use same IP and MAC,'
                'it does not support in current version.' % project_id)
        if not port_id:
            raise exceptions.DiagnoseException(
                "Can't retrieve related Neutron port id.")
        result = {
            'host': host,
            'port id': port_id,
        }
        return commandmanager.set_result(result)
