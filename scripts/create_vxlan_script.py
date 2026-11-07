
from extras.scripts import Script, StringVar, IntegerVar, ObjectVar, ChoiceVar
from ipam.models import VLAN, VLANGroup, Role, Prefix
from vpn.models import L2VPN, L2VPNTermination
from tenancy.models import Tenant

class CreateVXLANScript(Script):
    class Meta:
        name = "Create VXLAN VLAN"
        description = "Creates a VLAN with a VNI, bound to an L2VPN, and optionally a subnet"
        field_order = ['vlan_group', 'l2vpn', 'description', 'vlan_mode', 'manual_vlan_start', 'subnet', 'vlan_role']

    vlan_group = ObjectVar(model=VLANGroup, label="VLAN group")
    l2vpn = ObjectVar(model=L2VPN, label="L2VPN")
    description = StringVar(label="Description")
    vlan_mode = ChoiceVar(
        choices=(('auto', 'Auto'), ('manual', 'Manual')),
        default='auto',
        label="VLAN creation mode"
    )
    manual_vlan_start = IntegerVar(required=False, label="Manual VLAN ID")
    subnet = StringVar(required=False, label="Subnet CIDR")
    vlan_role = ObjectVar(model=Role, required=False, label="VLAN role")

    def run(self, data, commit):
        tenant = data['l2vpn'].tenant
        group = data['vlan_group']
        description = data['description']
        vlan_role = data.get('vlan_role')
        subnet = data.get('subnet')

        # Determine the VLAN ID
        if data['vlan_mode'] == 'manual':
            vlan_id = data['manual_vlan_start']
        else:
            vlan_id = self.find_available_vlan(group)
            if vlan_id is None:
                self.log_failure("No VLAN ID available in the ranges defined for this group.")
                return

        vlan_id_str = f"{vlan_id:04d}"
        vni = int(f"{data['l2vpn'].identifier}{vlan_id_str}")
        vlan_name = f"V_{group.slug.upper()}_{tenant.slug.upper()}_{vlan_id_str}"

        vlan = VLAN.objects.create(
            name=vlan_name,
            vid=vlan_id,
            group=group,
            tenant=tenant,
            description=description,
            role=vlan_role,
            custom_field_data={"vni": vni}
        )
        self.log_success(f"VLAN created: {vlan.name}")

        # Create or update the subnet
        if subnet:
            prefix, created = Prefix.objects.get_or_create(
                prefix=subnet,
                defaults={
                    "vlan": vlan,
                    "tenant": tenant,
                    "role": vlan_role,
                    "status": "active"
                }
            )
            if not created:
                prefix.vlan = vlan
                prefix.tenant = tenant
                prefix.save()
                self.log_info(f"Subnet updated: {prefix}")
            else:
                self.log_success(f"Subnet created: {prefix}")

        # L2VPN termination
        L2VPNTermination.objects.create(
            l2vpn=data['l2vpn'],
            assigned_object=vlan
        )
        self.log_success("L2VPN termination created successfully")

    def find_available_vlan(self, group):
        used_vids = set(VLAN.objects.filter(group=group).values_list('vid', flat=True))
        for start, end in group.vid_ranges:
            for vid in range(start, end + 1):
                if vid not in used_vids:
                    return vid
        return None
