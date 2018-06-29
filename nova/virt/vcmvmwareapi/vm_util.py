"""
The VMware API VM utility module to build SOAP object specs.
"""


from oslo_log import log as logging
from oslo_config import cfg

from nova import exception
from nova.i18n import _, _LE, _LI, _LW
from nova.virt.vmwareapi import vm_util
from nova.virt.vmwareapi import vim_util

from nova.virt.vcmvmwareapi import vim_util as vcm_vim_util

LOG = logging.getLogger(__name__)
CONF = cfg.CONF


# start live snapshot
def _property_from_propSet(propSet, name='name'):
    for p in propSet:
        if p.name == name:
            return p


def property_from_property_set(property_name, property_set):
    '''Use this method to filter property collector results.

    Because network traffic is expensive, multiple
    VMwareAPI calls will sometimes pile-up properties
    to be collected. That means results may contain
    many different values for multiple purposes.

    This helper will filter a list for a single result
    and filter the properties of that result to find
    the single value of whatever type resides in that
    result. This could be a ManagedObjectReference ID
    or a complex value.

    :param property_name: name of property you want
    :param property_set: all results from query
    :return: the value of the property.
    '''

    for prop in property_set.objects:
        if hasattr(prop, 'propSet'):
            p = _property_from_propSet(prop.propSet, property_name)
            if p is not None:
                return p


def get_current_snapshot_from_vm_ref(session, vm_ref):
    # Get the id of current snapshot, if there is no snapshot
    # on the VM instance, will return None
    current_snapshot_property_name = 'snapshot.currentSnapshot'
    property_set = session._call_method(
            vim_util, "get_object_properties",
            None, vm_ref, vm_ref._type, [current_snapshot_property_name])
    current_snapshot = property_from_property_set(
        current_snapshot_property_name, property_set)
    if current_snapshot is not None:
        snapshot_id = current_snapshot.val.value
        LOG.debug("Find current snapshot %s of vm instance", snapshot_id)
        return snapshot_id


def get_snapshots_from_vm_ref(session, vm_ref):
    """This method allows you to find the snapshots of a VM.

    :param session: a vSphere API connection
    :param vm_ref: a reference object to the running VM
    :return: the list of InstanceSnapshot object
    """

    snapshot_list_property_name = 'snapshot.rootSnapshotList'
    property_set = session._call_method(
            vim_util, "get_object_properties",
            None, vm_ref, vm_ref._type, [snapshot_list_property_name])
    snapshot_id = get_current_snapshot_from_vm_ref(session, vm_ref)

    result = {}
    snapshot_list = property_from_property_set(
        snapshot_list_property_name, property_set)
    if snapshot_list is not None:
        for vmsnap in snapshot_list.val.VirtualMachineSnapshotTree:
            snapshots = build_snapshot_obj(snapshot_id, vmsnap)
            result.update(snapshots)

    LOG.debug("Got total of %s snapshots.", len(result))
    return result


def get_snapshot_by_snapshot_id(session, vm_ref, snapshot_id=None):
    """This method is used to find the VirtualMachineSnapshot
    object via snapshot id.

    """
    all_snapshots = get_snapshots_from_vm_ref(session, vm_ref)
    for snap_ref in all_snapshots:
        snap_obj = all_snapshots[snap_ref]
        if snapshot_id is None:
            if snap_obj['is_current_snapshot']:
                return (snap_ref, snap_obj)
        elif str(snap_obj['snapshot_id']) == str(snapshot_id):
            return (snap_ref, snap_obj)
    if snapshot_id:
        raise exception.NotFound(_("The snapshot %s can not be found")
                                   % snapshot_id)
    else:
        raise exception.NotFound(_("The vm current snapshot can not be found !"))


def get_snapshot_obj_by_snapshot_ref(session, vm_ref, snapshot_ref):
    """This method is used to find the snapshot object via
    VirtualMachineSnapshot object.

    """
    all_snapshots = get_snapshots_from_vm_ref(session, vm_ref)
    for snap_ref in all_snapshots:
        if snap_ref.value == snapshot_ref.value:
            return all_snapshots[snap_ref]
    raise exception.NotFound(_("The snapshot %s can not be found")
                             % snapshot_ref.value)


def get_snapshot_ref_by_snapshot_id(session, vm_ref, snapshot_id):
    """This method is used to find the VirtualMachineSnapshot
    object via snapshot id.

    """
    all_snapshots = get_snapshots_from_vm_ref(session, vm_ref)
    for snap_ref in all_snapshots:
        snap_obj = all_snapshots[snap_ref]
        if str(snap_obj['snapshot_id']) == str(snapshot_id):
            return snap_ref
    raise exception.NotFound(_("The snapshot %s can not be found")
                             % snapshot_id)


def build_snapshot_obj(current_snapshot_id, vm_snapshot_tree,
                        parent_snapshot_id=0):
    """This method is used to build instance_snapshot object from
    VMware VirtualMachineSnapshotTree data object.

    """
    result = {}
    snapshot = {}
    snapshot['parent_snapshot_id'] = parent_snapshot_id
    snapshot['snapshot_id'] = vm_snapshot_tree.id
    snapshot['name'] = vm_snapshot_tree.name
    snapshot['description'] = vm_snapshot_tree.description
    snapshot['create_time'] = vm_snapshot_tree.createTime

    snapshot_value = vm_snapshot_tree.snapshot.value
    snapshot['is_current_snapshot'] = (True if current_snapshot_id ==
        snapshot_value else False)

    snapshot['metadata'] = {}
    snapshot['metadata']['quiesced'] = vm_snapshot_tree.quiesced
    snapshot['metadata']['replaySupported'] = vm_snapshot_tree.replaySupported
    snapshot['metadata']['vm_state'] = vm_snapshot_tree.state
    snapshot['metadata']['snapshot_value'] = snapshot_value

    result[vm_snapshot_tree.snapshot] = snapshot
    LOG.debug("Find a snapshot: %(id)s----%(name)s",
              {'id': snapshot['snapshot_id'], 'name': snapshot['name']})
    if hasattr(vm_snapshot_tree, 'childSnapshotList'):
        for sp in vm_snapshot_tree.childSnapshotList:
            children = build_snapshot_obj(current_snapshot_id, sp,
                                        parent_snapshot_id=vm_snapshot_tree.id)
            result.update(children)
    return result
# stop live snapshot


def get_vnc_port_state(session, req_type):
    min_port = CONF.vmware.vnc_port
    port_total = CONF.vmware.vnc_port_total
    allocated_ports = vm_util._get_allocated_vnc_ports(session)
    max_port = min_port + port_total
    available_port = None
    for port in range(min_port, max_port):
        if port not in allocated_ports:
            available_port = port
            break
    if not available_port:
        raise exception.ConsolePortRangeExhausted(min_port=min_port,
                                                  max_port=max_port)
    vnc_port_state = {}
    vnc_port_state['min_port'] = min_port
    vnc_port_state['max_port'] = max_port
    if req_type is None:
        vnc_port_state['allocated_ports'] = allocated_ports
        vnc_port_state['available_port'] = available_port
    elif req_type == 'allocated':
        vnc_port_state['allocated_ports'] = allocated_ports
    elif req_type == 'available':
        vnc_port_state['available_port'] = available_port
    return vnc_port_state


def get_mor_properties(session, mor_type, aomor, properties=None):
    if not properties:
        properties = ['name']
    LOG.debug(_("Parsing %s properties." % mor_type))
    result_list = []
    if hasattr(aomor, 'ManagedObjectReference'):
        mors = aomor.ManagedObjectReference
        retrieve_result = session._call_method(
                                vim_util, 
                                "get_properties_for_a_collection_of_objects",
                                mor_type,
                                mors,
                                properties)
        result_list = retrieve_result_propset_dict_list(session, retrieve_result)
    return result_list


def get_mor_parent_name(session, sudsobject):
    result_dict = {}
    result = session._call_method(vcm_vim_util, "get_dynamic_properties",
                                  sudsobject, sudsobject._type,
                                  ['name', 'parent'])
    LOG.debug("Parsing parent %s name %s." ,sudsobject, result.get('name'))
    if sudsobject._type == 'Datacenter':
        result_dict['datacenter'] = result.get('name')
    elif sudsobject._type == 'ClusterComputeResource':
        result_dict['cluster'] = result.get('name')
    if 'parent' in result.keys():
        child_result = get_mor_parent_name(session, result.get('parent'))
        result_dict.update(child_result)
    return result_dict


def parsing_mor_propset_dict(session, propset):
    prop_dict = {}
    for prop in propset:
        if prop.name == 'datastore':
            val = get_mor_properties(session, 'Datastore', prop.val)
        elif prop.name == 'network':
            val = get_mor_properties(session, 'Network', prop.val)
        elif prop.name == 'vm':
            val = get_mor_properties(session, 'VirtualMachine', prop.val, ['name','config.instanceUuid'])
        elif prop.name == 'parent':
            val = get_mor_parent_name(session, prop.val)
        else:
            val = prop.val
        prop_dict[prop.name] = val
    return prop_dict


def retrieve_result_propset_dict_list(session, retrieve_result):
    result_list = []
    if hasattr(retrieve_result, 'objects'):
        for obj_content in retrieve_result.objects:
            # the propset attribute "need not be set" by returning API
            if not hasattr(obj_content, 'propSet'):
                continue
            propdict = parsing_mor_propset_dict(session, obj_content.propSet)
            result_list.append(propdict)
    return result_list
