# Illini Secure Linux Server Logging

This ansible playbook helps configure your system to meet the
requirements in [IT04 Server Security Standard](https://go.illinois.edu/secstd-IT04),
section 4.6.1 Logging.

It has been tested on these platforms:

- CentOS: 7.x
- openSUSE Leap: 15.x
- Ubuntu: 18.04.x

## Roles

There are several ways to meet the standards auditing requirement. You
only need to choose one of these methods.

### auditbeat

This role installs auditbeat and disables auditd logging. The security
events are stored in `/var/log/auditbeat/events.json`.

### wazuh

TODO
