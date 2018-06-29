"""
Utility functions for ESX Networking.
"""

from oslo_vmware import vim_util as vutil

from nova.virt.vmwareapi import vim_util

from nova.virt.vcmvmwareapi import vim_util as vcm_vim_util


def get_virtual_adapter_network(session):
    """ Get virtual adapters network info. """
    results = session._call_method(vim_util, "get_objects", "HostSystem")
    session._call_method(vutil, 'cancel_retrieval', results)
    host_objects = results.objects

    virtual_networks = {}
    for host_object in host_objects:
        host_name = host_object.propSet[0].val
        vir_net_info = session._call_method(vim_util,
                                            'get_object_properties',
                                            None, host_object.obj,
                                            "HostSystem", ['network'])
        vir_nets = []
        for obj_content in vir_net_info.objects:
            if not hasattr(obj_content, 'propSet'):
                continue
            prop_dict = vm_util.propset_dict(obj_content.propSet)
            network_refs = prop_dict.get('network')
            if network_refs:
                network_refs = network_refs.ManagedObjectReference
                vpg_nets = {}
                for network in network_refs:
                    # Get network properties
                    vpg_nets['type'] = network._type
                    network_name = session._call_method(vcm_vim_util,
                                                "get_dynamic_property", network,
                                                "Network", "summary.name")
                    vpg_nets['name'] = network_name
                    vir_nets.append(vpg_nets)
        virtual_networks[host_name] = vir_nets

    LOG.debug("Get virtual adapters network info.")
    return virtual_networks


def get_physical_adapter_network(session):
    """ Get physical adapters network info. """
    results = session._call_method(vim_util, "get_objects", "HostSystem")
    session._call_method(vutil, 'cancel_retrieval', results)
    host_objects = results.objects

    physical_networks = {}
    for host_object in host_objects:
        host_name = host_object.propSet[0].val
        phy_net_info = session._call_method(vcm_vim_util, "get_dynamic_property",
                                           host_object.obj,
                                           "HostSystem", "config.network")
        phy_net_dict = vim_util.object_to_dict(phy_net_info)
        physical_networks[host_name] = phy_net_dict

    LOG.debug("Get physical adapters network info.")
    return physical_networks
