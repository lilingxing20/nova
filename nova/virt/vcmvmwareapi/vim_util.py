"""
The VMware API utility module.
"""

from oslo_config import cfg
from oslo_log import log as logging
from oslo_vmware import vim_util as vutil

from nova.virt.vmwareapi import vim_util

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


# rewrite start
def get_objects(vim, type_, properties_to_collect=None, all=False):
    """Gets the list of objects of the type specified."""
    # return vutil.get_objects(vim, type, CONF.vmware.maximum_objects,
    #                          properties_to_collect, all)
    # (Community use oslo.vmware utils will miss the build_recursive_traversal_spec which is Vsettan-only)
    if not properties_to_collect:
        properties_to_collect = ["name"]

    client_factory = vim.client.factory
    recur_trav_spec = build_recursive_traversal_spec(client_factory)
    object_spec = vutil.build_object_spec(client_factory,
                                          vim.service_content.rootFolder,
                                          [recur_trav_spec])
    property_spec = vutil.build_property_spec(
            client_factory,
            type_=type_,
            properties_to_collect=properties_to_collect,
            all_properties=all)
    property_filter_spec = vutil.build_property_filter_spec(client_factory,
                                                            [property_spec],
                                                            [object_spec])
    options = client_factory.create('ns0:RetrieveOptions')
    options.maxObjects = CONF.vmware.maximum_objects
    return vim.RetrievePropertiesEx(vim.service_content.propertyCollector,
                                    specSet=[property_filter_spec],
                                    options=options)

# add start
def build_recursive_traversal_spec(client_factory):
    """Builds the Recursive Traversal Spec to traverse the object managed
    object hierarchy.
    """
    # Get the assorted traversal spec which takes care of the objects to
    # be searched for from the rootFolder
    traversal_spec = vutil.build_recursive_traversal_spec(client_factory)

    visit_folders_select_spec = vutil.build_selection_spec(client_factory,
                                                           'visitFolders')
    # For getting to datastoreFolder from datacenter
    dc_to_df = vutil.build_traversal_spec(client_factory,
                                          "dc_to_df",
                                          "Datacenter",
                                          "datastoreFolder",
                                          False,
                                          [visit_folders_select_spec])
    traversal_spec.selectSet.append(dc_to_df)

    return traversal_spec


def build_recursive_resource_pool_traversal_spec(client_factory):
    """Builds a Recursive Traversal Spec to traverse the object managed
    object hierarchy, starting from a ResourcePool and going to
    VirtualMachines via root and child ResourcePools
    """

    rp_to_rp_select_spec = vutil.build_selection_spec(client_factory, "rp_to_rp")
    rp_to_vm_select_spec = vutil.build_selection_spec(client_factory, "rp_to_vm")

     # For getting to Virtual Machine from the Resource Pool
    rp_to_vm = vutil.build_traversal_spec(client_factory, "rp_to_vm", "ResourcePool",
                                "vm", False,
                                [rp_to_rp_select_spec, rp_to_vm_select_spec])

    # For getting to child res pool from the parent res pool
    rp_to_rp = vutil.build_traversal_spec(client_factory, "rp_to_rp", "ResourcePool",
                                "resourcePool", False,
                                [rp_to_rp_select_spec, rp_to_vm_select_spec])

    return [rp_to_rp, rp_to_vm]


def build_recursive_cluster_traversal_spec(client_factory):
    """Builds a Recursive Traversal Spec to traverse the object managed
    object hierarchy, starting from a ClusterComputeResource and going to
    VirtualMachines via root and child ResourcePools
    """

    # For getting to resource pool from Compute Resource
    cr_to_rp = vutil.build_traversal_spec(client_factory, "cr_to_rp",
                                "ClusterComputeResource", "resourcePool", False,
                                build_recursive_resource_pool_traversal_spec(client_factory))

    return [cr_to_rp]


def get_objects_from_cluster(vim, type_, cluster, properties_to_collect=None, all=False):
    """Gets the list of objects of the type specified."""
    if not properties_to_collect:
        properties_to_collect = ["name"]

    client_factory = vim.client.factory
    object_spec = vutil.build_object_spec(client_factory,
                        cluster,
                        build_recursive_cluster_traversal_spec(client_factory))
    property_spec = vutil.build_property_spec(client_factory, type_=type_,
                                properties_to_collect=properties_to_collect,
                                all_properties=all)
    property_filter_spec = vutil.build_property_filter_spec(client_factory,
                                [property_spec],
                                [object_spec])
    options = client_factory.create('ns0:RetrieveOptions')
    options.maxObjects = CONF.vmware.maximum_objects
    return vim.RetrievePropertiesEx(
            vim.service_content.propertyCollector,
            specSet=[property_filter_spec], options=options)


def get_objects_from_resource_pool(vim, type_, resource_pool, properties_to_collect=None, all=False):
    """Gets the list of objects of the type specified."""
    if not properties_to_collect:
        properties_to_collect = ["name"]

    client_factory = vim.client.factory
    object_spec = vutil.build_object_spec(client_factory,
                        resource_pool,
                        build_recursive_resource_pool_traversal_spec(client_factory))
    property_spec = vutil.build_property_spec(client_factory, type_=type_,
                                properties_to_collect=properties_to_collect,
                                all_properties=all)
    property_filter_spec = vutil.build_property_filter_spec(client_factory,
                                [property_spec],
                                [object_spec])
    options = client_factory.create('ns0:RetrieveOptions')
    options.maxObjects = CONF.vmware.maximum_objects
    return vim.RetrievePropertiesEx(
            vim.service_content.propertyCollector,
            specSet=[property_filter_spec], options=options)


def get_contained_objects(vim, mobj, nested_type, recursive=True):
    """Gets the descendant Managed Objects of a Managed Entity."""
    client_factory = vim.client.factory
    collector = vim.service_content.propertyCollector
    view_mgr = vim.service_content.viewManager
    container_view = vim.CreateContainerView(view_mgr, container=mobj,
                                             type=[nested_type],
                                             recursive=recursive)

    # Create a filter spec for the requested properties
    property_spec = vutil.build_property_spec(client_factory, type_=nested_type,
                                        properties_to_collect=["name"],
                                        all_properties=False)

    # Traversal spec determines the object traversal path to search for the
    # specified property. The following is the default for a container view
    traversal_spec = vutil.build_traversal_spec(client_factory, "view",
                                          "ContainerView", "view", False, None)

    # Create an object spec with the traversal spec
    object_spec = vutil.build_object_spec(client_factory, container_view,
                                          [traversal_spec])
    object_spec.skip = True

    # Create a property filter spec with the property spec & object spec
    property_filter_spec = client_factory.create('ns0:PropertyFilterSpec')
    property_filter_spec.propSet = [property_spec]
    property_filter_spec.objectSet = [object_spec]
    options = client_factory.create('ns0:RetrieveOptions')
    options.maxObjects = CONF.vmware.maximum_objects
    return vim.RetrievePropertiesEx(collector, specSet=[property_filter_spec],
                                    options=options)


# Vsettan-only add
def continue_to_get_objects(vim, token):
    """Continues to get the list of objects of the type specified."""
    return vim.ContinueRetrievePropertiesEx(
            vim.service_content.propertyCollector,
            token=token)


def cancel_retrieve(vim, token):
    """Cancels the retrieve operation."""
    return vim.CancelRetrievePropertiesEx(
            vim.service_content.propertyCollector,
            token=token)


def get_dynamic_properties(vim, mobj, type, property_names):
    """Gets the specified properties of the Managed Object."""
    obj_content = vim_util.get_object_properties(vim, None, mobj, type, property_names)
    if obj_content is None:
        return {}
    if hasattr(obj_content, 'token'):
        cancel_retrieve(vim, obj_content.token)
    property_dict = {}
    if obj_content.objects:
        if hasattr(obj_content.objects[0], 'propSet'):
            dynamic_properties = obj_content.objects[0].propSet
            if dynamic_properties:
                for prop in dynamic_properties:
                    property_dict[prop.name] = prop.val
        # The object may have information useful for logging
        if hasattr(obj_content.objects[0], 'missingSet'):
            for m in obj_content.objects[0].missingSet:
                LOG.warning(_LW("Unable to retrieve value for %(path)s "
                                "Reason: %(reason)s"),
                            {'path': m.path,
                             'reason': m.fault.localizedMessage})
    return property_dict


def get_dynamic_property(vim, mobj, type, property_name):
    """Gets a particular property of the Managed Object."""
    property_dict = get_dynamic_properties(vim, mobj, type, [property_name])
    return property_dict.get(property_name)
