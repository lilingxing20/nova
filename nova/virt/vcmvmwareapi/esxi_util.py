"""
ESXi utility functions
"""

from nova.virt.vmwareapi import vm_util
from nova.virt.vmwareapi import vim_util

from nova.virt.vcmvmwareapi import vm_util as vcm_vm_util
from nova.virt.vcmvmwareapi import vim_util as vcm_vim_util


def get_esxi_hosts(session, cluster_name=None,
                            properties_list=['name'],
                            detail=False):
    """ Get esxi hosts for vCenter cluster. """
    if detail:
        properties_list = ["name", "parent", "datastore", "vm", "summary.hardware.vendor", "summary.hardware.model", "summary.hardware.uuid", "summary.hardware.memorySize", "summary.hardware.cpuModel", "summary.hardware.cpuMhz", "summary.hardware.numCpuPkgs", "summary.hardware.numCpuThreads", "summary.hardware.numNics", "summary.hardware.numHBAs", "summary.runtime.connectionState","summary.runtime.powerState","summary.runtime.bootTime", "summary.overallStatus", "summary.managementServerIp"]
    if not properties_list:
        return ['alarmActionsEnabled', 'availableField', 'capability', 'config', 'configIssue', 'configManager', 'configStatus', 'customValue', 'datastore', 'datastoreBrowser', 'declaredAlarmState', 'disabledMethod', 'effectiveRole', 'hardware', 'licensableResource', 'name', 'network', 'overallStatus', 'parent', 'permission', 'recentTask', 'runtime', 'summary', 'systemResources', 'tag', 'triggeredAlarmState', 'value', 'vm']

    if cluster_name:
        cluster_obj = vm_util.get_cluster_ref_by_name(session, cluster_name)
        # Get the Host and Resource Pool Managed Object Refs
        host_aomor = session._call_method(vcm_vim_util, "get_dynamic_property",
                                          cluster_obj,
                                          "ClusterComputeResource", "host")
        host_mors = host_aomor.ManagedObjectReference
        retrieve_result =  session._call_method(vim_util,
                                "get_properties_for_a_collection_of_objects",
                                "HostSystem", host_mors, properties_list)
    else:
        retrieve_result = session._call_method(vim_util, 'get_objects', 'HostSystem',
                                     properties_list)
    hosts_list = vcm_vm_util.retrieve_result_propset_dict_list(session,
                                                           retrieve_result)
    return hosts_list
