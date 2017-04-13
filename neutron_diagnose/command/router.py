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
from osc_lib.command import command
from osc_lib import exceptions

from neutron_diagnose.command import commandmanager
from neutron_diagnose.i18n import _


class CheckRouterBrainSplit(commandmanager.ShowOne):
    _description = _("Check whether the specified router brain split.")

    def get_parser(self, prog_name):
        parser = super(CheckRouterBrainSplit, self).get_parser(prog_name)
        parser.add_argument(
            'router_id',
            metavar='<router-id>',
            help=_('the router uuid.'),
        )
        return parser

    def take_action(self, parsed_args):
        compute_client = self.app.client_manager.compute
        network_client = self.app.client_manager.network
        ssh_client = self.app.client_manager.ssh
        result = {}
        return commandmanager.set_result(result)


class CheckVmFloatingIP(commandmanager.ShowOne):
    _description = _("Check whether the specified instance floating "
                     "ip is ok.")

    def get_parser(self, prog_name):
        parser = super(CheckVmFloatingIP, self).get_parser(prog_name)
        parser.add_argument(
            'floatingip-id',
            metavar='<floatingip-id>',
            help=_('the floatingip uuid.'),
        )
        return parser

    def take_action(self, parsed_args):
        compute_client = self.app.client_manager.compute
        network_client = self.app.client_manager.network
        ssh_client = self.app.client_manager.ssh
        result = {}
        return commandmanager.set_result(result)
