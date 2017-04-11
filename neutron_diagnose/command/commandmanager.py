#   Copyright 2012-2013 OpenStack Foundation
#
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

"""Modify cliff.CommandManager"""

import prettytable
import pkg_resources
import six

from cliff import columns
import cliff.commandmanager
from cliff import show
from cliff import utils
from osc_lib.command import command


class CommandManager(cliff.commandmanager.CommandManager):
    """Add additional functionality to cliff.CommandManager

    Load additional command groups after initialization
    Add _command_group() methods
    """

    def __init__(self, namespace, convert_underscores=True):
        self.group_list = []
        super(CommandManager, self).__init__(namespace, convert_underscores)

    def load_commands(self, namespace):
        self.group_list.append(namespace)
        return super(CommandManager, self).load_commands(namespace)

    def add_command_group(self, group=None):
        """Adds another group of command entrypoints"""
        if group:
            self.load_commands(group)

    def get_command_groups(self):
        """Returns a list of the loaded command groups"""
        return self.group_list

    def get_command_names(self, group=None):
        """Returns a list of commands loaded for the specified group"""
        group_list = []
        if group is not None:
            for ep in pkg_resources.iter_entry_points(group):
                cmd_name = (
                    ep.name.replace('_', ' ')
                    if self.convert_underscores
                    else ep.name
                )
                group_list.append(cmd_name)
            return group_list
        return list(self.commands.keys())


class ShowOne(command.Command, show.ShowOne):

    def _format_row(self, row):
        new_row = []
        for r in row:
            if isinstance(r, columns.FormattableColumn):
                r = r.human_readable()
            if isinstance(r, six.string_types):
                r = r.replace('\r\n', '\n').replace('\r', ' ')
            new_row.append(r)
        return new_row

    def _width_info(self, term_width, field_count):
        # remove padding and dividers for width available to actual content
        usable_total_width = max(0, term_width - 1 - 3 * field_count)

        # calculate width per column if all columns were equal
        if field_count == 0:
            optimal_width = 0
        else:
            optimal_width = max(0, usable_total_width // field_count)

        return usable_total_width, optimal_width

    def _assign_max_widths(self, stdout, x, max_width, min_width=0):
        if min_width:
            x.min_width = min_width

        if max_width > 0:
            term_width = max_width
        else:
            term_width = utils.terminal_width(stdout)
            if not term_width:
                # not a tty, so do not set any max widths
                return
        field_count = len(x.field_names)

        try:
            first_line = x.get_string().splitlines()[0]
            if len(first_line) <= term_width:
                return
        except IndexError:
            return

        usable_total_width, optimal_width = self._width_info(
            term_width, field_count)

        field_widths = self._field_widths(x.field_names, first_line)

        shrink_fields, shrink_remaining = self._build_shrink_fields(
            usable_total_width, optimal_width, field_widths, x.field_names)

        shrink_to = shrink_remaining // len(shrink_fields)
        # make all shrinkable fields size shrink_to apart from the last one
        for field in shrink_fields[:-1]:
            x.max_width[field] = max(min_width, shrink_to)
            shrink_remaining -= shrink_to

        # give the last shrinkable column shrink_to plus any remaining
        field = shrink_fields[-1]
        x.max_width[field] = max(min_width, shrink_remaining)

    def _emit_one(self, column_names, data, stdout, parsed_args):
        x = prettytable.PrettyTable(field_names=('CheckItem', 'Result'),
                                    print_empty=False)
        x.padding_width = 1
        # Align all columns left because the values are
        # not all the same type.
        x.align['CheckItem'] = 'l'
        x.align['Result'] = 'l'
        for name, value in zip(column_names, data):
            x.add_row(self._format_row((name, value)))

        # Choose a reasonable min_width to better handle a narrow
        # console. The table will overflow the console width in preference
        # to wrapping columns smaller than 16 characters in an attempt to keep
        # the Field column readable.
        min_width = 16
        self._assign_max_widths(
            stdout, x, int(parsed_args.max_width), min_width)

        formatted = x.get_string()
        stdout.write(formatted)
        stdout.write('\n')
        return

    def produce_output(self, parsed_args, column_names, data):
        (columns_to_include, selector) = self._generate_columns_and_selector(
            parsed_args, column_names)
        if selector:
            data = list(self._compress_iterable(data, selector))
        self._emit_one(columns_to_include,
                       data,
                       self.app.stdout,
                       parsed_args)
        return 0


def set_result(result_dic):
    result_keys = []
    result_data = []
    for key, value in result_dic.items():
        result_keys.append(key)
        result_data.append(value)
    return tuple(result_keys), tuple(result_data)
