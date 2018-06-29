"""
Class for VM tasks like spawn, snapshot, suspend, resume etc.
"""

from oslo_log import log as logging
from oslo_vmware import vim_util as vutil

from nova.compute import vm_states
from nova.virt.vmwareapi import vmops
from nova.virt.vmwareapi import vm_util
from nova.virt.vmwareapi import vim_util

from nova.virt.vcmvmwareapi import vm_util as vcm_vm_util
from nova.virt.vcmvmwareapi import vim_util as vcm_vim_util

LOG = logging.getLogger(__name__)

VMWARE_POWER_STATES = vmops.VMWARE_POWER_STATES
VMWARE_VM_STATES = {'poweredOff': vm_states.STOPPED,
                    'poweredOn': vm_states.ACTIVE,
                    'suspended': vm_states.SUSPENDED}


class VMwareVMOps(vmops.VMwareVMOps):
    """Management class for VM-related tasks."""
    def __init__(self, session, virtapi, volumeops, cluster=None,
                 datastore_regex=None):
        super(VMwareVMOps, self).__init__(session, virtapi, volumeops,
                                             cluster=cluster,
                                             datastore_regex=datastore_regex)

    # init power state
    def get_all_power_state(self):
        """Return power state of all the VM instances."""
        LOG.debug("get all vm power state.")
        lst_properties = ["name", "runtime.powerState"]
        results = self._session._call_method(vim_util,
                                             "get_objects",
                                             "VirtualMachine",
                                             lst_properties)
        power_states = {}
        while results:
            for obj in results.objects:
                # VM name may have display name as its prefix, uuid is the
                # last 36 characters.
                uuid = obj.propSet[0].val[-36:]
                state = obj.propSet[1].val
                power_states[uuid] = VMWARE_POWER_STATES[state]
            results = self._session._call_method(vutil,
                                                 'continue_retrieval',
                                                 results)
        LOG.debug(power_states)
        return power_states

    # live snapshot start
    def list_instance_snapshots(self, context, instance):
        """get all the snapshots of the specified VM instance."""
        LOG.debug("Getting Snapshots of the VM instance", instance=instance)
        vm_ref = vm_util.get_vm_ref(self._session, instance)

        snapshots = self._get_vm_snapshots(vm_ref)
        LOG.debug("Got Snapshots of the VM instance", instance=instance)
        return snapshots

    def _get_vm_snapshots(self, vm_ref):
        # Get snapshots of the VM
        snapshot_dict = vcm_vm_util.get_snapshots_from_vm_ref(self._session,
                                                          vm_ref)
        return snapshot_dict.values()

    def create_instance_snapshot(self, context, instance, **kwargs):
        """Create the snapshot of the specified VM instance."""
        LOG.debug("Creating Snapshot of the VM instance", instance=instance)
        vm_ref = vm_util.get_vm_ref(self._session, instance)
        snapshot_name = kwargs.get('snapshot_name')
        desc = kwargs.get('description')
        metadata = kwargs.get('metadata')
        if 'memory' in metadata:
            memory = metadata.get('memory')
        else:
            memory = False
        if 'quiesce' in metadata:
            quiesce = metadata.get('quiesce')
        else:
            quiesce = True
        snapshot_task = self._session._call_method(self._session.vim,
                                                   "CreateSnapshot_Task",
                                                   vm_ref,
                                                   name=snapshot_name,
                                                   description=desc,
                                                   memory=memory,
                                                   quiesce=quiesce)
        self._session._wait_for_task(snapshot_task)
        LOG.debug("Created Snapshot of the VM instance", instance=instance)
        task_info = self._session._call_method(vcm_vim_util,
                                               "get_dynamic_property",
                                               snapshot_task, "Task", "info")
        snapshot_ref = task_info.result
        return vcm_vm_util.get_snapshot_obj_by_snapshot_ref(self._session, vm_ref,
                                                        snapshot_ref)

    def delete_instance_snapshot(self, context, instance,
                                 snapshot_id):
        """Delete snapshot of the instance."""
        LOG.debug("Deleting snapshot %s of instance", snapshot_id,
                  instance=instance)
        vm_ref = vm_util.get_vm_ref(self._session, instance)
        snapshot_ref = vcm_vm_util.get_snapshot_ref_by_snapshot_id(self._session,
                                                               vm_ref,
                                                               snapshot_id)
        snapshot_task = self._session._call_method(self._session.vim,
                                                   "RemoveSnapshot_Task",
                                                   snapshot_ref,
                                                   removeChildren=False)
        self._session._wait_for_task(snapshot_task)
        LOG.debug("Deleted Snapshot of the VM instance", instance=instance)

    def restore_instance_snapshot(self, context, instance,
                                 snapshot_id=None):
        """Restore snapshot of the instance."""
        LOG.debug("Restore to a snapshot of instance", instance=instance)
        vm_ref = vm_util.get_vm_ref(self._session, instance)
        snapshot_obj = None
        update_state = {}
        if snapshot_id is not None:
            (snapshot_ref, snapshot_obj) = vcm_vm_util.get_snapshot_by_snapshot_id(
                                                                 self._session,
                                                                 vm_ref,
                                                                 snapshot_id)
            snapshot_task = self._session._call_method(self._session.vim,
                                                       "RevertToSnapshot_Task",
                                                       snapshot_ref)
        else:
            (snapshot_ref, snapshot_obj) = vcm_vm_util.get_snapshot_by_snapshot_id(
                                                                 self._session,
                                                                 vm_ref,
                                                                 snapshot_id)
            if snapshot_ref is None:
                raise exception.NotFound(_("This virtual machine does not have"
                                           " a current snapshot."))
            else:
                snapshot_task = self._session._call_method(
                                                self._session.vim,
                                                "RevertToCurrentSnapshot_Task",
                                                vm_ref)
        self._session._wait_for_task(snapshot_task)
        if snapshot_obj:
            snap_vm_state = snapshot_obj["metadata"]["vm_state"]
            update_state['vm_state'] = VMWARE_VM_STATES[snap_vm_state]
            update_state['power_state'] = VMWARE_POWER_STATES[snap_vm_state]
        LOG.debug("Restored the snapshot of the VM instance", instance=instance)
        return update_state
    # live snapshot end
