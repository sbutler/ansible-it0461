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
module: splunk_app_facts
short_description: Gathers facts about the currently installed splunk apps
version_added: 2.4.2
description:
    - This module talks to splunkd running on a system and gathers
      facts about its installed apps.
    - It automatically sets the fact splunk_apps.
options:
    username:
        description:
            - Username used to authenticate to C(splunkd). This is
              required for many commands.
    password:
        description:
            - Password used to authenticate to C(splunkd). This is
              required for many commands.
    app:
        description:
            - Name of the application to get facts about. Default is
              to get the facts for all applications.
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
import shlex

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils import six
from ansible.module_utils.six.moves.urllib_parse import quote as urlquote


def main():
    module = AnsibleModule(
        argument_spec=dict(
            username=dict(required=False, aliases=['user']),
            password=dict(required=False, aliases=['pass'], no_log=True),

            app=dict(required=False, default=''),
            splunk_bin=dict(required=False, default='/opt/splunkforwarder/bin/splunk'),
        ),
        supports_check_mode=True,
    )

    s_user = module.params['username']
    s_pass = module.params['password']
    s_app = module.params['app']
    s_bin = module.params['splunk_bin']

    args = [s_bin, 'display', 'app']
    if s_app:
        args.append(s_app)
    if s_user and s_pass:
        args.extend([
            '-auth',
            ':'.join([s_user, s_pass])
        ])

    startd = datetime.datetime.now()

    rc, out, err = module.run_command(args, use_unsafe_shell=False)

    endd = datetime.datetime.now()
    delta = endd - startd

    apps = {}
    result = dict(
        result=apps,
        stdout=out,
        stderr=err,
        rc=rc,
        start=str(startd),
        end=str(endd),
        delta=str(delta),
        changed=False,
        warnings=[],
    )

    if rc != 0:
        module.fail_json(msg='non-zero return code', **result)

    result['ansible_facts'] = {'splunk_apps': apps}
    for line in out.splitlines():
        line_parts = line.split()
        if (not line_parts[0]) or len(line_parts) != 4:
            result.warnings.append('Bad app line: {0}'.format(line))
            continue

        apps[line_parts[0]] = {
            'configured': line_parts[1] == 'CONFIGURED',
            'enabled': line_parts[2] == 'ENABLED',
            'visible': line_parts[3] == 'VISIBLE',
        }

    module.exit_json(**result)


if __name__ == '__main__':
    main()
