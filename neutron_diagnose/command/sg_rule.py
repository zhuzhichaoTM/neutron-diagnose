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

import logging
from osc_lib import exceptions

from neutron_diagnose.command import commandmanager
from neutron_diagnose.i18n import _


class CheckSgRule(commandmanager.ShowOne):
    _description = _("Compare the security group rule in DataBase with "
                     "iptables rules in related compute node.")

    def get_parser(self, prog_name):
        parser = super(CheckSgRule, self).get_parser(prog_name)
        parser.add_argument(
            'port-id',
            metavar='<port-id>',
            help=_('the port uuid.'),
        )
        return parser

    def take_action(self, parsed_args):
        compute_client = self.app.client_manager.compute
        network_client = self.app.client_manager.network
        ssh_client = self.app.client_manager.ssh
        result = {}
        return commandmanager.set_result(result)
