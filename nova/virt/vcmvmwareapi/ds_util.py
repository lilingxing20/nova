"""
Datastore utility functions
"""
from oslo_log import log as logging

from nova.i18n import _, _LE, _LI, _LW
from nova.virt.vmwareapi import vim_util

from nova.virt.vcmvmwareapi import vim_util as vcm_vim_util
from nova.virt.vcmvmwareapi import vm_util as vcm_vm_util

LOG = logging.getLogger(__name__)


def get_datastores(session, cluster=None, host=None,
                   properties_list=['name'], detail=False):
    if detail:
        properties_list = ["alarmActionsEnabled","name","overallStatus","parent","summary.capacity","summary.freeSpace","summary.type","summary.accessible","summary.maintenanceMode","vm"]
    if not properties_list:
        return ["alarmActionsEnabled","availableField","browser","capability","configIssue","configStatus","customValue","declaredAlarmState","disabledMethod","effectiveRole","host","info","iormConfiguration","name","overallStatus","parent","permission","recentTask","summary","tag","triggeredAlarmState","value","vm"]
    """ Get datastores for vCenter cluster. """
    if cluster is None and host is None:
        retrieve_result = session._call_method(vim_util, "get_objects",
                                               "Datastore", properties_list)
    else:
        if cluster is not None:
            datastore_ret = session._call_method(
                                        vcm_vim_util,
                                        "get_dynamic_property", cluster,
                                        "ClusterComputeResource", "datastore")
        else:
            datastore_ret = session._call_method(
                                        vcm_vim_util,
                                        "get_dynamic_property", host,
                                        "HostSystem", "datastore")
        # If there are no hosts in the cluster then an empty string is
        # returned
        if not datastore_ret:
            raise exception.DatastoreNotFound()

        data_store_mors = datastore_ret.ManagedObjectReference
        retrieve_result = vcm_vm_util.get_mor_properties(session,
                                                    "Datastore",
                                                    data_store_mors,
                                                    properties_list)
    datastores_list = vcm_vm_util.retrieve_result_propset_dict_list(session,
                                                                retrieve_result)
    return datastores_list


def get_datastore_clusters(session, properties_list=['name'], detail=False):
    """ Get datastore clusters for vCenter server. """
    if detail:
        properties_list = ["alarmActionsEnabled","childEntity","name","overallStatus","parent","summary.capacity","summary.freeSpace"]
    if not properties_list:
        return ["alarmActionsEnabled","availableField","childEntity","childType","configIssue","configStatus","customValue","declaredAlarmState","disabledMethod","effectiveRole","name","overallStatus","parent","permission","podStorageDrsEntry","recentTask","summary","tag","triggeredAlarmState","value"]

    retrieve_result = session._call_method(vcm_vim_util,
                                           "get_objects",
                                           "StoragePod",
                                           properties_list)
    ds_clusters = vcm_vm_util.retrieve_result_propset_dict_list(session,
                                                            retrieve_result)
    ds_cluster_list = []
    for ds_cluster in ds_clusters:
        try:
            ds_child_aomor = ds_cluster.pop('childEntity')
            ds_datastores = vcm_vm_util.get_mor_properties(session,
                                                       'Datastore',
                                                       ds_child_aomor)
            ds_cluster['datastore'] = ds_datastores
        except Exception as excep:
            LOG.warn(_LE("Failed to get datastore cluster child datastore,\
                          warning references %s."), excep)
        ds_cluster_list.append(ds_cluster)

    return ds_cluster_list
