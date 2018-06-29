"""
A connection to the VMware vCenter platform.
"""

from nova.virt.vmwareapi import driver

from nova.virt.vcmvmwareapi import vm_util as vcm_vm_util
from nova.virt.vcmvmwareapi import dc_util as vcm_dc_util
from nova.virt.vcmvmwareapi import ds_util as vcm_ds_util
from nova.virt.vcmvmwareapi import esxi_util as vcm_esxi_util
from nova.virt.vcmvmwareapi import network_util as vcm_network_util
from nova.virt.vcmvmwareapi import vmops as vcm_vmops


class VCMVMwareVCDriver(driver.VMwareVCDriver):
    """The VC host connection object."""

    def __init__(self, virtapi, scheme="https"):
        super(VCMVMwareVCDriver, self).__init__(virtapi, scheme=scheme)
        self._vmops = vcm_vmops.VMwareVMOps(self._session,
                                            virtapi,
                                            self._volumeops,
                                            self._cluster_ref,
                                            datastore_regex=self._datastore_regex)


    def get_all_power_state(self):
        """Return power state of all the VM instances."""
        return self._vmops.get_all_power_state()

    # live snapshot start
    def list_instance_snapshots(self, context, instance):
        """List snapshots of the instance."""
        return self._vmops.list_instance_snapshots(context, instance)

    def create_instance_snapshot(self, context, instance, snapshot_name,
                                 description, metadata):
        """Create snapshots of the instance."""
        return self._vmops.create_instance_snapshot(context,
            instance, snapshot_name=snapshot_name,
            description=description, metadata=metadata)

    def delete_instance_snapshot(self, context, instance, snapshot_id):
        """Delete snapshot of the instance."""
        return self._vmops.delete_instance_snapshot(context,
                                               instance,
                                               snapshot_id)

    def restore_instance_snapshot(self, context, instance, snapshot_id):
        """Restore snapshot of the instance."""
        return self._vmops.restore_instance_snapshot(context,
                                               instance,
                                               snapshot_id)

    # extension API interface start
    def get_datacenters(self, context, detail=False):
        """ Get datacenters for vCenter server. """
        datacenters = vcm_dc_util.get_datacenters(self._session, detail=detail)
        return datacenters

    def get_datastores(self, context, detail=False):
        """ Get datastores for vCenter cluster. """
        datastores = vcm_ds_util.get_datastores(self._session, detail=detail)
        return datastores

    def get_datastore_clusters(self, context, detail=False):
        """ Get datastore clusters for vCenter server. """
        ds_clusters = vcm_ds_util.get_datastore_clusters(self._session, detail=detail)
        return ds_clusters

    def get_esxi_hosts(self, context, detail=False):
        """ Get esxi hosts for vCenter cluster. """
        esxi_hosts = vcm_esxi_util.get_esxi_hosts(self._session, self._cluster_name, detail=detail)
        return esxi_hosts

    def get_vnc_port_state(self, context, req_type):
        """ Get vnc available port for vCenter cluster. """
        vnc_port_state = vcm_vm_util.get_vnc_port_state(self._session, req_type)
        return vnc_port_state

    def get_virtual_adapter_network(self, context):
        """ Get virtual network """
        networks = vcm_network_util.get_virtual_adapter_network(self._session)
        return networks

    def get_physical_adapter_network(self, context):
        """ Get physical network """
        networks = vcm_network_util.get_physical_adapter_network(self._session)
        return networks
