from django.db.models.signals import pre_save
from django.dispatch import receiver
from dcim.models import Device

@receiver(pre_save, sender=Device)
def auto_generate_device_name(sender, instance, **kwargs):
    if not instance.name:
        tenant_gr_slug = instance.tenant.group.slug if instance.tenant and instance.tenant.group else 'notenantgroup'
        tenant_slug = instance.tenant.slug if instance.tenant else 'notenant'
        site_slug = instance.site.slug if instance.site else 'nosite'
        role_slug = instance.device_role.slug if instance.device_role else 'norole'
        base_name = f"{tenant_gr_slug}-{site_slug}-{tenant_slug}-{role_slug}"

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
