from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
import ssl

def get_vcenter_connection(host, user, password, port=443):
    context = ssl._create_unverified_context()
    si = SmartConnect(host=host, user=user, pwd=password, port=port, sslContext=context)
    return si

def get_vms_and_datastores(si):
    content = si.RetrieveContent()

    vm_list = []
    datastore_list = []

    for datacenter in content.rootFolder.childEntity:
        # Get VMs
        vm_folder = datacenter.vmFolder
        vm_view = content.viewManager.CreateContainerView(vm_folder, [vim.VirtualMachine], True)
        for vm in vm_view.view:
            vm_list.append({
                "name": vm.name,
                "power_state": vm.runtime.powerState,
                "guest_os": vm.config.guestFullName if vm.config else "Unknown"
            })
        vm_view.Destroy()

        # Get Datastores
        ds_view = content.viewManager.CreateContainerView(datacenter, [vim.Datastore], True)
        for ds in ds_view.view:
            summary = ds.summary
            datastore_list.append({
                "name": summary.name,
                "capacity_gb": round(summary.capacity / (1024 ** 3), 2),
                "free_space_gb": round(summary.freeSpace / (1024 ** 3), 2),
                "type": summary.type
            })
        ds_view.Destroy()

    return vm_list, datastore_list

def main():
    vcenter_host = "your-vcenter-host"
    username = "your-username"
    password = "your-password"

    si = None
    try:
        si = get_vcenter_connection(vcenter_host, username, password)
        vms, datastores = get_vms_and_datastores(si)

        print("Virtual Machines:")
        for vm in vms:
            print(f"- {vm['name']} ({vm['power_state']}) - {vm['guest_os']}")

        print("\nDatastores:")
        for ds in datastores:
            print(f"- {ds['name']} | Capacity: {ds['capacity_gb']} GB | Free: {ds['free_space_gb']} GB | Type: {ds['type']}")

    finally:
        if si:
            Disconnect(si)

if __name__ == "__main__":
    main()
