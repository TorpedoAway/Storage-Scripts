from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
import ssl
import json

def get_vcenter_connection(host, user, password, port=443):
    context = ssl._create_unverified_context()
    si = SmartConnect(host=host, user=user, pwd=password, port=port, sslContext=context)
    return si

def get_vms_with_datastore_info(si):
    content = si.RetrieveContent()
    vm_data = []

    for datacenter in content.rootFolder.childEntity:
        vm_folder = datacenter.vmFolder
        vm_view = content.viewManager.CreateContainerView(vm_folder, [vim.VirtualMachine], True)

        for vm in vm_view.view:
            vm_info = {
                "name": vm.name,
                "power_state": vm.runtime.powerState,
                "guest_os": vm.config.guestFullName if vm.config else "Unknown",
                "datastores": []
            }

            # Build mapping of datastore to space used by this VM
            ds_usage = {}
            if hasattr(vm, 'storage') and hasattr(vm.storage, 'perDatastoreUsage'):
                for usage in vm.storage.perDatastoreUsage:
                    ds_name = usage.datastore.name
                    used_space_gb = round(usage.committed / (1024 ** 3), 2)
                    ds_usage[ds_name] = used_space_gb

            for ds_name, used_space_gb in ds_usage.items():
                vm_info["datastores"].append({
                    "name": ds_name,
                    "used_gb": used_space_gb
                })

            vm_data.append(vm_info)

        vm_view.Destroy()

    return vm_data

def main():
    vcenter_host = "your-vcenter-host"
    username = "your-username"
    password = "your-password"

    si = None
    try:
        si = get_vcenter_connection(vcenter_host, username, password)
        vms = get_vms_with_datastore_info(si)
        print(json.dumps(vms, indent=4))
    finally:
        if si:
            Disconnect(si)

if __name__ == "__main__":
    main()


SAMPLE OUTPUT...

[
    {
        "name": "VM-Example",
        "power_state": "poweredOn",
        "guest_os": "Microsoft Windows Server 2022 (64-bit)",
        "datastores": [
            {
                "name": "Datastore1",
                "used_gb": 35.12
            },
            {
                "name": "Datastore2",
                "used_gb": 10.53
            }
        ]
    }
]
