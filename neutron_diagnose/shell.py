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

import argparse
import locale
import sys

from osc_lib.api import auth
from osc_lib import shell
from oslo_utils import importutils
import six

import neutron_diagnose
from neutron_diagnose.client import client_config as cloud_config
from neutron_diagnose.client import clientmanager
from neutron_diagnose.command import commandmanager

osprofiler_profiler = importutils.try_import("osprofiler.profiler")


DEFAULT_DOMAIN = 'default'


class NeutronDiagnoeShell(shell.OpenStackShell):

    def __init__(self):

        super(NeutronDiagnoeShell, self).__init__(
            description='Neutron Diagnose Tools.',
            version=neutron_diagnose.__version__,
            command_manager=commandmanager.CommandManager(
                'neutron_diagnose', convert_underscores=False),
            deferred_help=True)

        self.api_version = {}

    def build_option_parser(self, description, version):
        parser = super(NeutronDiagnoeShell, self).build_option_parser(
            description, version)
        parser = clientmanager.build_plugin_option_parser(parser)
        parser = auth.build_auth_plugins_option_parser(parser)
        return parser

    def _final_defaults(self):
        super(NeutronDiagnoeShell, self)._final_defaults()

        # Set the default plugin to token_endpoint if url and token are given
        if (self.options.url and self.options.token):
            # Use service token authentication
            self._auth_type = 'token_endpoint'
        else:
            self._auth_type = 'password'

    def _load_plugins(self):
        # Load plugins via stevedore
        for mod in clientmanager.PLUGIN_MODULES:
            default_version = getattr(mod, 'DEFAULT_API_VERSION', None)
            # Only replace the first instance of "os", some service names will
            # have "os" in their name, like: "antiddos"
            option = mod.API_VERSION_OPTION.replace('os_', '', 1)
            version_opt = str(self.cloud.config.get(option, default_version))
            if version_opt:
                api = mod.API_NAME
                self.api_version[api] = version_opt

                # Add a plugin interface to let the module validate the version
                # requested by the user
                skip_old_check = False
                mod_check_api_version = getattr(mod, 'check_api_version', None)
                if mod_check_api_version:
                    # this throws an exception if invalid
                    skip_old_check = mod_check_api_version(version_opt)

                mod_versions = getattr(mod, 'API_VERSIONS', None)
                if not skip_old_check and mod_versions:
                    if version_opt not in mod_versions:
                        sorted_versions = sorted(
                            mod.API_VERSIONS.keys(),
                            key=lambda s: list(map(int, s.split('.'))))
                        self.log.warning(
                            "%s version %s is not in supported versions: %s"
                            % (api, version_opt, ', '.join(sorted_versions)))

                # Command groups deal only with major versions
                version = '.v' + version_opt.replace('.', '_').split('_')[0]
                cmd_group = (
                    'neutron_diagnose.' + api.replace('-', '_') + version)
                self.command_manager.add_command_group(cmd_group)
                self.log.debug(
                    '%(name)s API version %(version)s, cmd group %(group)s',
                    {'name': api, 'version': version_opt, 'group': cmd_group}
                )

    def _load_commands(self):
        # Load commands via cliff/stevedore
        self.command_manager.add_command_group(
            'neutron_diagnose.command')

    def initialize_app(self, argv):
        super(NeutronDiagnoeShell, self).initialize_app(argv)

        # First, throw away what has already been done with o-c-c and
        # use our own.
        try:
            self.cloud_config = cloud_config.OSC_Config(
                override_defaults={
                    'interface': None,
                    'auth_type': self._auth_type,
                },
            )
        except (IOError, OSError):
            self.log.critical("Could not read clouds.yaml configuration file")
            self.print_help_if_requested()
            raise

        if not self.options.debug:
            self.options.debug = None

        # NOTE(dtroyer): Need to do this with validate=False to defer the
        #                auth plugin handling to ClientManager.setup_auth()
        self.cloud = self.cloud_config.get_one_cloud(
            cloud=self.options.cloud,
            argparse=self.options,
            validate=False,
        )

        # Then, re-create the client_manager with the correct arguments
        self.client_manager = clientmanager.ClientManager(
            cli_options=self.cloud,
            api_version=self.api_version,
            ssh_key_file=self.options.ssh_key_file)

    def prepare_to_run_command(self, cmd):
        kwargs = {}
        if not cmd.auth_required:
            # Build fake token creds to keep ksa and o-c-c hushed
            kwargs['auth_type'] = 'token_endpoint'
            kwargs['auth'] = {}
            kwargs['auth']['token'] = 'x'
            kwargs['auth']['url'] = 'x'

        # Validate auth options
        self.cloud = self.cloud_config.get_one_cloud(
            cloud=self.options.cloud,
            argparse=self.options,
            validate=True,
            **kwargs
        )
        # Push the updated args into ClientManager
        self.client_manager._cli_options = self.cloud

        return super(NeutronDiagnoeShell, self).prepare_to_run_command(cmd)


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
        if six.PY2:
            # Emulate Py3, decode argv into Unicode based on locale so that
            # commands always see arguments as text instead of binary data
            encoding = locale.getpreferredencoding()
            if encoding:
                argv = map(lambda arg: arg.decode(encoding), argv)
    return NeutronDiagnoeShell().run(argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
