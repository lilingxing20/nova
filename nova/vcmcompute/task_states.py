# =================================================================
# Licensed Materials - Property of VCM
#
# (c) Copyright VCM Corp. All Rights Reserved
#
# =================================================================

"""Possible task states for instances.

Compute instance task states represent what is happening to the instance at the
current moment. These tasks can be generic, such as 'spawning', or specific,
such as 'block_device_mapping'. These task states allow for a better view into
what an instance is doing and should be displayed to users/administrators as
necessary.

"""


# Possible task states during server snapshot
SERVER_SNAPSHOT_CREATE_PENDING = 'server_snapshot_create_pending'
SERVER_SNAPSHOT_DELETE_PENDING = 'server_snapshot_delete_pending'
SERVER_SNAPSHOT_RESTORE_PENDING = 'server_snapshot_restore_pending'
SERVER_SNAPSHOT_CREATING = 'server_snapshot_creating'
SERVER_SNAPSHOT_DELETING = 'server_snapshot_deleting'
SERVER_SNAPSHOT_RESTORING = 'server_snapshot_restoring'
