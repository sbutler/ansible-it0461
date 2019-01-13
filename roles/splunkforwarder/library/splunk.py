#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>, and others
# (c) 2016, Toshio Kuratomi <tkuratomi@ansible.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function, unicode_literals
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '0.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: splunk
short_description: Run a splunk command, optionally passing auth.
version_added: 2.4.2
description:
    - This module uses the splunk command to talk to splunkd running
      on a system. Use one of the C(command), C(shell), or C(argv)
      arguments to specify the command.
options:
    username:
        description:
            - Username used to authenticate to C(splunkd). This is
              required for many commands.
    password:
        description:
            - Password used to authenticate to C(splunkd). This is
              required for many commands.
    chdir:
        description:
            - Change into this directory before running the command.
    command:
        description:
            - Run a C(splunk) command using C(shlex.split) to break
              apart the arguments.
            - The command will not be processed through the shell, so
              variables like C($HOME) and operations like C("<"),
              C(">"), C("|"), C(";") and C("&") will not work. Use the
              C(shell) argument if you need these features.
    argv:
        description:
            - Run a C(splunk) command by specifying the arguments as
              a list.
            - The command will not be processed through the shell, so
              variables like C($HOME) and operations like C("<"),
              C(">"), C("|"), C(";") and C("&") will not work. Use the
              C(shell) argument if you need these features.
    shell:
        description:
            - Run a C(splunk) command by specifying the arguments as a
              shell command. This runs the command using the shell
              so any shell metacharacters must be escaped to be safely
              used.
    creates:
        description:
            - A filename or glob pattern. If it already exists, this
              step B(won't) be run.
    removes:
        description:
            - A filename or glob pattern. If it already exists, this
              step B(will) be run.
    splunk_bin:
        description:
            - Path to the splunk command on the machine. This is to
              the administrative CLI and not C(splunkd).
        default: /opt/splunkforwarder/bin/splunk
author:
    - Stephen J. Butler
'''

EXAMPLES = '''
'''

import datetime
import glob
import json
import os
import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils import six
from ansible.module_utils.six.moves.urllib_parse import quote as urlquote
from ansible.module_utils.six.moves import shlex_quote


def main():
    module = AnsibleModule(
        argument_spec=dict(
            username=dict(required=False, aliases=['user']),
            password=dict(required=False, aliases=['pass'], no_log=True),

            command=dict(required=False),
            argv=dict(type='list', required=False),
            shell=dict(required=False),

            creates=dict(type='path', required=False),
            removes=dict(type='path', required=False),
            chdir=dict(type='path', required=False),
            splunk_bin=dict(type='path', required=False, default='/opt/splunkforwarder/bin/splunk'),
        ),
        supports_check_mode=True,
    )

    s_user = module.params['username']
    s_pass = module.params['password']
    s_bin = module.params['splunk_bin']
    s_chdir = module.params['chdir']
    s_creates = module.params['creates']
    s_removes = module.params['removes']

    s_command = module.params['command']
    s_argv = module.params['argv']
    s_shell = module.params['shell']

    use_unsafe_shell = False
    if s_command or s_shell:
        if s_command and (s_shell or s_argv):
            module.fail_json(rc=256, msg='can only use one of command, argv, or shell')
        elif s_shell and s_argv:
            module.fail_json(rc=256, msg='can only use one of command, argv, or shell')

        args = '{0} {1}'.format(s_bin, s_command)
        if s_user and s_pass:
            args += ' -auth ' + shlex_quote(':'.join([s_user, s_pass]))
        use_unsafe_shell = (not s_command) and s_shell
    elif s_argv:
        args = [s_bin]
        args.extend(s_argv)
        if s_user and s_pass:
            args.extend([
                '-auth',
                shlex_quote(':'.join([s_user, s_pass]))
            ])
    else:
        module.fail_json(rc=256, msg='no command, argv, or shell specified')


    if s_chdir:
        s_chdir = os.path.abspath(s_chdir)
        os.chdir(s_chdir)

    if s_creates:
        # do not run the command if the line contains creates=filename
        # and the filename already exists.  This allows idempotence
        # of command executions.
        if glob.glob(s_creates):
            module.exit_json(
                cmd=args,
                stdout='skipped, since {0} exists'.format(s_creates),
                changed=False,
                rc=0
            )

    if s_removes:
        # do not run the command if the line contains removes=filename
        # and the filename does not exist.  This allows idempotence
        # of command executions.
        if not glob.glob(s_removes):
            module.exit_json(
                cmd=args,
                stdout='skipped, since {0} does not exist'.format(s_removes),
                changed=False,
                rc=0
            )

    startd = datetime.datetime.now()

    if not module.check_mode:
        rc, out, err = module.run_command(args, use_unsafe_shell=use_unsafe_shell, encoding=None)
    elif s_creates or s_removes:
        rc = 0
        out = err = b'Command would have run if not in check mode'
    else:
        module.exit_json(msg="skipped, running in check mode", skipped=True)

    endd = datetime.datetime.now()
    delta = endd - startd

    apps = {}
    result = dict(
        cmd=args,
        stdout=out.rstrip(b"\r\n"),
        stderr=err.rstrip(b"\r\n"),
        rc=rc,
        start=str(startd),
        end=str(endd),
        delta=str(delta),
        changed=True,
    )

    if rc != 0:
        module.fail_json(msg='non-zero return code', **result)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
