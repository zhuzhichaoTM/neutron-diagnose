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

import logging
import paramiko

from neutron_diagnose.common import constants
from neutron_diagnose.common import exceptions
from neutron_diagnose.i18n import _

DEFAULT_API_VERSION = '1.0'
API_VERSION_OPTION = 'os_ssh_client_version'
API_NAME = 'ssh'


def make_client(instance):
    client = SshClient()
    client.init_client(instance.ssh_key_file)
    return client


class SshClient(object):
    def __init__(self, port=22, user='root'):
        self.port = port
        self.user= user
        self.private_key = None
        self.ssh_client = None

    def init_client(self, key_name='id_rsa'):
        try:
            self.private_key = paramiko.RSAKey.from_private_key_file(key_name)
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(
                paramiko.AutoAddPolicy())
        except Exception:
            raise exceptions.DiagnoseException(
                "Import the ssh key file: %s failed." % key_name)

    def ssh_exec(self, host, command):
        try:
            self.ssh_client.connect(hostname=host, port=self.port,
                                    username=self.user, pkey=self.private_key)
        except Exception:
            raise exceptions.DiagnoseException(
                "Connect remote host: %s failed." % host)
        stdin, stdout, stderr = self.ssh_client.exec_command(command)
        result = stdout.read()
        if not result:
            result = stderr.read()
        self.ssh_client.close()
        return result


def build_option_parser(parser):
    """Hook to add global options"""
    parser.add_argument(
        '--ssh-key-file',
        metavar='<ssh-key-file>',
        default=constants.SSH_PRIVATE_KEY,
        help=_("The ssh key file."))
    return parser


if __name__ == "__main__":
    ssh = SshClient()
    ssh.make_client()
    ssh.ssh_exec()
