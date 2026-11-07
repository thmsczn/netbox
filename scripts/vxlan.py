from django.utils.text import slugify
from ipam.models import VLANGroup, VLAN, Role, Prefix
from vpn.models import L2VPN, L2VPNTermination
from extras.scripts import *

class NewVXLANScript(Script):

    class Meta:
        name = "New VXLAN"
        description = "Provision a VXLAN"

    vlan_group = ObjectVar(
        description="Fabric of the new VXLAN",
        label="Fabric",
        model=VLANGroup,
        required=True
    )
    
    l2vpn = ObjectVar(
        description="Gateway (L2VPN)",
        model=L2VPN,
        required=True,
        query_params={
            'cf_fabric': '$vlan_group'
        }
    )
    
    description_vlan = StringVar(
        description="VLAN description",
        required=False
    )
    
    vlan_mode = ChoiceVar(
        choices=(('auto', 'Auto'), ('manual', 'Manual')),
        default='auto',
        description="VLAN creation mode"
    )
    
    manual_vlan_start = IntegerVar(
        required=False, 
        label="Manual VLAN ID"
    )
    
    subnet = StringVar(
        required=False, 
        label="Subnet CIDR"
    )
    
    vlan_role = ObjectVar(
        model=Role, 
        required=False, 
        label="VLAN role"
    )

    def run(self, data, commit):
        vlan_group = data['vlan_group']
        l2vpn = data['l2vpn']
        vlan_role = data.get('vlan_role')
        description = data.get('description_vlan') or ""
        subnet = data.get('subnet')
        mode = data['vlan_mode']
        manual_vlan_start = data.get('manual_vlan_start')
        tenant = l2vpn.tenant if hasattr(l2vpn, "tenant") else None
        l2vpn_id = l2vpn.identifier  # adjust to the actual field: .identifier, .pk or .id
        vlan = None

        # 1. Find the next free VLAN ID in auto mode, otherwise check availability in manual mode
        if mode == 'auto':
            # VLAN IDs already used in this VLAN group
            used_vlans = set(VLAN.objects.filter(group=vlan_group).values_list('vid', flat=True))
            # Usable range: usually 2-4094, adjust to your policy
            for vid in range(2, 4095):
                if vid not in used_vlans:
                    vlan_id = vid
                    break
            else:
                self.log_failure("No VLAN available in this group.")
                return
        else:  # manual mode
            vlan_id = manual_vlan_start
            exists = VLAN.objects.filter(group=vlan_group, vid=vlan_id).exists()
            if exists:
                self.log_failure(f"VLAN {vlan_id} is already used in this group.")
                return

        # 2. Build the VLAN name according to the naming convention
        vlan_id_str = f"{vlan_id:04d}"
        vlan_name = f"V_{l2vpn.name}_{vlan_id_str}"

        # 3. Create the VLAN
        vlan = VLAN(
            name=vlan_name,
            vid=vlan_id,
            group=vlan_group,
            tenant=tenant,
            description=description,
            role=vlan_role,
        )
        # Set the "vni" custom field
        vlan.custom_field_data = vlan.custom_field_data or {}
        vlan.custom_field_data["vni"] = int(f"{l2vpn_id}{vlan_id_str}")

        vlan.full_clean()
        vlan.save()

        self.log_success(f"VLAN {vlan_name} (ID {vlan_id}) created in group {vlan_group.name}")
        

        # 4. Subnet: create or associate
        if subnet:
            prefix, created = Prefix.objects.get_or_create(
                prefix=subnet,
                defaults={
                    "vlan": vlan,
                    "tenant": tenant
                }
            )
            if not created:
                prefix.vlan = vlan
                prefix.save()
                self.log_info(f"Prefix {subnet} already exists, associated with the VLAN.")

                output = {
                    "VLAN Name": vlan.name,
                    "VLAN ID": vlan.vid,
                    "VLAN Group": vlan.group.name,
                    "L2VPN": l2vpn.name,
                    "Tenant": tenant.name if tenant else None,
                    "Role": vlan.role.name if vlan.role else None,
                    "Description": vlan.description,
                    "Custom VNI": vlan.custom_field_data.get("vni"),
                    "Subnet": str(prefix.prefix),
                    "Prefix Created": False,
                }
                self.log_success(f"Creation complete. Details: {output}")
                return output

            else:
                self.log_success(f"Prefix {subnet} created and associated with the VLAN.")

# ... final output

        output = {
            "VLAN Name": vlan.name,
            "VLAN ID": vlan.vid,
            "VLAN Group": vlan.group.name,
            "L2VPN": l2vpn.name,
            "Tenant": tenant.name if tenant else None,
            "Role": vlan.role.name if vlan.role else None,
            "Description": vlan.description,
            "Custom VNI": vlan.custom_field_data.get("vni"),
        }

        if subnet:
            output["Subnet"] = prefix.prefix
            output["Prefix Created"] = created

        self.log_success(f"Creation complete. Details: {output}")
        return output
