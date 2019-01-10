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
module: audit_syscall_facts
short_description: Gathers facts about supported syscall auditing
version_added: 2.4.2
description:
    - This module probes the audit system to see if a syscall is
      present. It does this by inserting an audit rule and then
      removing it.
    - It automatically sets the facts syscalls_b32 and syscalls_b64.
options:
    arch:
        description:
            - Architecture to probe for on multiarch systems. Either
              C(b32), C(b64), or C(both).
        default: both
        required: false
    syscalls:
        description:
            - List of syscall names to probe for.
        required: true
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

SYSCALL_FAILED_RE = re.compile(r'name unknown: (?P<name>\w+)')

def main():
    module = AnsibleModule(
        argument_spec=dict(
            arch=dict(choices=['b32', 'b64', 'both'], default='both', required=False),
            syscalls=dict(type='list', required=True),
        )
    )

    sc_arch = module.params['arch']
    sc_b32 = sc_arch == 'both' or sc_arch == 'b32'
    sc_b64 = sc_arch == 'both' or sc_arch == 'b64'
    sc_syscalls = module.params['syscalls']

    a_args = [
        'auditctl',
        '-a', 'always,exit',
        '-F', 'auid=0xDEADBEEF',
    ]
    d_args = [
        'auditctl',
        '-d', 'always,exit',
        '-F', 'auid=0xDEADBEEF',
    ]

    sc_results32 = []
    sc_results64 = []
    sc_warnings = []

    startd = datetime.datetime.now()

    def _test_syscall(arch, name):
        args = list(a_args)
        args.extend(['-F', 'arch={0}'.format(arch), '-S', name])
        rc, out, err = module.run_command(args, use_unsafe_shell=False)

        if rc == 0:
            args = list(d_args)
            args.extend(['-F', 'arch={0}'.format(arch), '-S', name])
            module.run_command(args, use_unsafe_shell=False)
        else:
            m = SYSCALL_FAILED_RE.search(err)
            if not m:
                sc_warnings.append(err)

        return rc == 0

    for name in sc_syscalls:
        if sc_b32 and _test_syscall('b32', name):
            sc_results32.append(name)
        if sc_b64 and _test_syscall('b64', name):
            sc_results64.append(name)

    endd = datetime.datetime.now()
    delta = endd - startd

    result = dict(
        result32=sc_results32,
        result64=sc_results64,
        start=str(startd),
        end=str(endd),
        delta=str(delta),
        changed=True,
        warnings=sc_warnings,
        ansible_facts={},
    )

    if sc_b32:
        result['ansible_facts']['syscalls_b32'] = sc_results32
    if sc_b64:
        result['ansible_facts']['syscalls_b64'] = sc_results64

    module.exit_json(**result)


if __name__ == '__main__':
    main()
