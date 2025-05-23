#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)#!/usr/bin/python
"""
The nxos interfaces fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import re
from copy import deepcopy

from ansible_collections.ansible.netcommon.plugins.module_utils.network.common import (
    utils,
)
from ansible_collections.cisco.nxos.plugins.module_utils.network.nxos.argspec.interfaces.interfaces import (
    InterfacesArgs,
)
from ansible_collections.cisco.nxos.plugins.module_utils.network.nxos.utils.utils import (
    get_interface_type,
)
from ansible_collections.cisco.nxos.plugins.module_utils.network.nxos.nxos import (
    default_intf_enabled,
)


class InterfacesFacts(object):
    """ The nxos interfaces fact class
    """

    def __init__(self, module, subspec="config", options="options"):
        self._module = module
        self.argument_spec = InterfacesArgs.argument_spec
        spec = deepcopy(self.argument_spec)
        if subspec:
            if options:
                facts_argument_spec = spec[subspec][options]
            else:
                facts_argument_spec = spec[subspec]
        else:
            facts_argument_spec = spec

        self.generated_spec = utils.generate_dict(facts_argument_spec)

    def populate_facts(self, connection, ansible_facts, data=None):
        """ Populate the facts for interfaces
        :param connection: the device connection
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """
        objs = []
        if not data:
            data = connection.get("show running-config | section ^interface")

        config = ("\n" + data).split("\ninterface ")
        for conf in config:
            conf = conf.strip()
            if conf:
                obj = self.render_config(self.generated_spec, conf)
                if obj:
                    objs.append(obj)

        ansible_facts["ansible_network_resources"].pop("interfaces", None)
        facts = {}
        facts["interfaces"] = []
        if objs:
            params = utils.validate_config(
                self.argument_spec, {"config": objs}
            )
            for cfg in params["config"]:
                facts["interfaces"].append(utils.remove_empties(cfg))

        ansible_facts["ansible_network_resources"].update(facts)
        return ansible_facts

    def render_config(self, spec, conf):
        """
        Render config as dictionary structure and delete keys
          from spec for null values
        :param spec: The facts tree, generated from the argspec
        :param conf: The configuration
        :rtype: dictionary
        :returns: The generated config
        """
        config = deepcopy(spec)

        match = re.search(r"^(\S+)", conf)
        intf = match.group(1)
        if get_interface_type(intf) == "unknown":
            return {}
        config["name"] = "current_" + intf
        config["description"] = utils.parse_conf_arg(conf, "description")
        config["speed"] = utils.parse_conf_arg(conf, "speed")
        config["mtu"] = utils.parse_conf_arg(conf, "mtu")
        config["duplex"] = utils.parse_conf_arg(conf, "duplex")
        config["mode"] = utils.parse_conf_cmd_arg(
            conf, "switchport", "layer2", "layer3"
        )

        config["enabled"] = utils.parse_conf_cmd_arg(
            conf, "shutdown", False, True
        )

        config["fabric_forwarding_anycast_gateway"] = utils.parse_conf_cmd_arg(
            conf, "fabric forwarding mode anycast-gateway", True
        )
        config["ip_forward"] = utils.parse_conf_cmd_arg(
            conf, "ip forward", True
        )

        interfaces_cfg = utils.remove_empties(config)
        return interfaces_cfg
