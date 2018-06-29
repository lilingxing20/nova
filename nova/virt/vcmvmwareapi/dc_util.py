"""
DataCenter utility functions

"""

from nova.virt.vmwareapi import vim_util

from nova.virt.vcmvmwareapi import vm_util as vcm_vm_util


def get_datacenters(session, properties_list=['name'], detail=False):
    """ Get datacenters for vCenter server. """
    if detail:
        properties_list = ["alarmActionsEnabled","datastore","name","network","overallStatus","parent"]
    if not properties_list:
        return ["alarmActionsEnabled","availableField","configIssue","configStatus","configuration","customValue","datastore","datastoreFolder","declaredAlarmState","disabledMethod","effectiveRole","hostFolder","name","network","networkFolder","overallStatus","parent","permission","recentTask","tag","triggeredAlarmState","value","vmFolder"]
    retrieve_result = session._call_method(vim_util, "get_objects",
                                           "Datacenter", properties_list)
    dcs_info_list = vcm_vm_util.retrieve_result_propset_dict_list(session,
                                                              retrieve_result)
    return dcs_info_list
