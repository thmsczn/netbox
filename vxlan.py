from django.utils.text import slugify

from dcim.choices import DeviceStatusChoices, SiteStatusChoices
from dcim.models import Device, DeviceRole, DeviceType, Manufacturer, Site
from extras.scripts import *
from ipam.models import VLAN, VLANGroup, Role, Prefix
from vpn.models import L2VPN, L2VPNTermination
from tenancy.models import Tenant


class NewVXLANScript(Script):

    class Meta:
        name = "New VXLAN"
        description = "Provision a VXLAN"
        field_order = ['site_name', 'switch_count', 'switch_model']

    vlan_group = ObjectVar(
        description="Fabric",
        model=VLANGroup,
        required=True
    )
    
    l2vpn = ObjectVar(
        description="Gateway",
        model=L2VPN,
        required=True
    )
    
    description_vlan = StringVar(
        description="Description of the new VXLAN"
        required=False
    )
    
    vlan_mode = ChoiceVar(
        choices=(('auto', 'Auto'), ('manual', 'Manuel')),
        default='auto',
        description="Mode de création du VXAN"
    )
    
    '''site_name = StringVar(
        description="Name of the new site"
    )
    switch_count = IntegerVar(
        description="Number of access switches to create"
    )
    manufacturer = ObjectVar(
        model=Manufacturer,
        required=False
    )
    switch_model = ObjectVar(
        description="Switch model",
        model=DeviceType,
        query_params={
            'manufacturer_id': '$manufacturer'
        }
    )'''

    def run(self, data, commit):

        # Create the new site
        site = Site(
            name=data['site_name'],
            slug=slugify(data['site_name']),
            status=SiteStatusChoices.STATUS_PLANNED
        )
        site.full_clean()
        site.save()
        self.log_success(f"Created new site: {site}")

        # Create access switches
        switch_role = DeviceRole.objects.get(name='Switch')
        for i in range(1, data['switch_count'] + 1):
            switch = Device(
                device_type=data['switch_model'],
                name=f'{site.slug}-switch{i}',
                site=site,
                status=DeviceStatusChoices.STATUS_PLANNED,
                role=switch_role
            )
            switch.full_clean()
            switch.save()
            self.log_success(f"Created new switch: {switch}")

        # Generate a CSV table of new devices
        output = [
            'name,make,model'
        ]
        for switch in Device.objects.filter(site=site):
            attrs = [
                switch.name,
                switch.device_type.manufacturer.name,
                switch.device_type.model
            ]
            output.append(','.join(attrs))

        return '\n'.join(output)