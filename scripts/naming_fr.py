from django.db.models.signals import pre_save
from django.dispatch import receiver
from dcim.models import Device

@receiver(pre_save, sender=Device)
def auto_generate_device_name(sender, instance, **kwargs):
    if not instance.name:
        site = instance.site
        region_slug = site.region.slug if site and site.region else 'noregion'
        site_slug = site.slug if site else 'nosite'
        location_slug = instance.location.slug if instance.location else 'nolocation'
        # NetBox >= 3.6 utilise "role", les versions antérieures "device_role"
        role = getattr(instance, 'role', None) or getattr(instance, 'device_role', None)
        role_slug = role.slug if role else 'norole'
        base_name = f"{region_slug}-{site_slug}-{location_slug}-{role_slug}"

        if role_slug == 'patch-panel' and instance.rack and instance.position:
            rack = instance.rack.name
            position = instance.position
            generated_name = f"{base_name}-{rack}-{position}"
        else:
            number = 1
            while True:
                generated_name = f"{base_name}-{str(number).zfill(2)}"
                if not Device.objects.filter(name=generated_name).exists():
                    break
                number += 1
        
        instance.name = generated_name
