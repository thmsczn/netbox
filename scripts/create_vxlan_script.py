
from extras.scripts import Script, StringVar, IntegerVar, ObjectVar, ChoiceVar
from ipam.models import VLAN, VLANGroup, Role, Prefix
from vpn.models import L2VPN, L2VPNTermination
from tenancy.models import Tenant

class CreateVXLANScript(Script):
    class Meta:
        name = "Création de VLAN VXLAN"
        description = "Crée un VLAN avec un VNI, associé à un L2VPN, et optionnellement un subnet"
        field_order = ['vlan_group', 'l2vpn', 'description', 'vlan_mode', 'manual_vlan_start', 'subnet', 'vlan_role']

    vlan_group = ObjectVar(model=VLANGroup, label="Groupe de VLAN")
    l2vpn = ObjectVar(model=L2VPN, label="L2VPN")
    description = StringVar(label="Description")
    vlan_mode = ChoiceVar(
        choices=(('auto', 'Auto'), ('manual', 'Manuel')),
        default='auto',
        label="Mode de création du VLAN"
    )
    manual_vlan_start = IntegerVar(required=False, label="ID VLAN manuel")
    subnet = StringVar(required=False, label="Subnet CIDR")
    vlan_role = ObjectVar(model=Role, required=False, label="Rôle du VLAN")

    def run(self, data, commit):
        tenant = data['l2vpn'].tenant
        group = data['vlan_group']
        description = data['description']
        vlan_role = data.get('vlan_role')
        subnet = data.get('subnet')

        # Détermination du VLAN ID
        if data['vlan_mode'] == 'manual':
            vlan_id = data['manual_vlan_start']
        else:
            vlan_id = self.find_available_vlan(group)
            if vlan_id is None:
                self.log_failure("Aucun ID VLAN disponible dans les plages définies pour ce groupe.")
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
        self.log_success(f"VLAN créé : {vlan.name}")

        # Création ou mise à jour du subnet
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
                self.log_info(f"Subnet mis à jour : {prefix}")
            else:
                self.log_success(f"Subnet créé : {prefix}")

        # L2VPN termination
        L2VPNTermination.objects.create(
            l2vpn=data['l2vpn'],
            assigned_object=vlan
        )
        self.log_success("L2VPN termination créée avec succès")

    def find_available_vlan(self, group):
        used_vids = set(VLAN.objects.filter(group=group).values_list('vid', flat=True))
        for start, end in group.vid_ranges:
            for vid in range(start, end + 1):
                if vid not in used_vids:
                    return vid
        return None
