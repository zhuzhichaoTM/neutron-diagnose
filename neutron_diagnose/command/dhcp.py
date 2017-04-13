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
        network = network_client.find_network()
        result = {
            'vif': 'OK',
            'ovs flow': 'OK',
            'iptables rule': 'OK'
        }
        return commandmanager.set_result(result)
