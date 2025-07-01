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
        description="Description du VLAN",
        required=False
    )
    
    vlan_mode = ChoiceVar(
        choices=(('auto', 'Auto'), ('manual', 'Manuel')),
        default='auto',
        description="Mode de création du VLAN"
    )
    
    manual_vlan_start = IntegerVar(
        required=False, 
        label="ID VLAN manuel"
    )
    
    subnet = StringVar(
        required=False, 
        label="Subnet CIDR"
    )
    
    vlan_role = ObjectVar(
        model=Role, 
        required=False, 
        label="Rôle du VLAN"
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
        l2vpn_id = l2vpn.identifier  # ajuster selon champ réel, parfois .identifier, .pk, ou .id
        vlan = None

        # 1. Recherche du prochain VLAN ID dispo si auto, sinon vérifie la disponibilité en manuel
        if mode == 'auto':
            # Cherche les VLAN IDs utilisés dans ce VLANGroup
            used_vlans = set(VLAN.objects.filter(group=vlan_group).values_list('vid', flat=True))
            # Plage utilisable : 2-4094 en général, ou selon ta politique
            for vid in range(2, 4095):
                if vid not in used_vlans:
                    vlan_id = vid
                    break
            else:
                self.log_failure("Aucun VLAN disponible dans ce groupe.")
                return
        else:  # mode manuel
            vlan_id = manual_vlan_start
            exists = VLAN.objects.filter(group=vlan_group, vid=vlan_id).exists()
            if exists:
                self.log_failure(f"Le VLAN {vlan_id} est déjà pris dans ce groupe.")
                return

        # 2. Création du nom VLAN selon convention
        vlan_id_str = f"{vlan_id:04d}"
        vlan_name = f"V_{l2vpn.name}_{vlan_id_str}"

        # 3. Création du VLAN
        vlan = VLAN(
            name=vlan_name,
            vid=vlan_id,
            group=vlan_group,
            tenant=tenant,
            description=description,
            role=vlan_role,
        )
        # Ajout custom field "vni"
        vlan.custom_field_data = vlan.custom_field_data or {}
        vlan.custom_field_data["vni"] = int(f"{l2vpn_id}{vlan_id_str}")

        vlan.full_clean()
        vlan.save()

        self.log_success(f"VLAN {vlan_name} (ID {vlan_id}) créé dans le groupe {vlan_group.name}")
        

        # 4. Subnet : gestion création/association
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
                self.log_info(f"Prefix {subnet} déjà existant, associé au VLAN.")

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
                self.log_success(f"Création terminée. Détails : {output}")
                return output

            else:
                self.log_success(f"Prefix {subnet} créé et associé au VLAN.")

# ... tu continues avec le output final si nécessaire

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

        self.log_success(f"Création terminée. Détails : {output}")
        return output
