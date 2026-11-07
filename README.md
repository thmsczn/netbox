# netbox

Collection of my [NetBox](https://github.com/netbox-community/netbox) projects.

## Structure

```
.
├── scripts/                    # NetBox scripts (custom scripts, signals)
│   ├── create_vxlan_script.py  # Creates a VLAN/VNI bound to an L2VPN (+ optional subnet)
│   ├── vxlan.py                # Provisions a VXLAN ("New VXLAN")
│   └── auto_device_naming.py   # Automatic device naming (pre_save signal)
├── export-templates/           # NetBox export templates (Jinja2)
│   └── ip_addresses.j2         # CSV export of IP addresses
└── README.md
```

More directories can be added at the root for future projects
(e.g. `reports/`, `plugins/`, `ansible/`…).

## Scripts

### `create_vxlan_script.py` / `vxlan.py`

NetBox custom scripts (`extras.scripts.Script`). Place them in NetBox's
`SCRIPTS_ROOT` directory or upload them via *Customization → Scripts*.

### `auto_device_naming.py`

Automatically generates a device (`Device`) name on creation when none is set,
using the format:

```
<region>-<site>-<location>-<role>-NN
```

(object slugs; `noregion`, `nosite`, `nolocation`, `norole` when missing).
For patch panels mounted in a rack: `<base>-<rack>-<position>`.

The `pre_save` receiver is registered when the module is imported, so NetBox
must load it (for example from `SCRIPTS_ROOT`).

## Export templates

### `ip_addresses.j2`

CSV export of IP addresses (`;` delimiter, opens directly in Excel with
European locale settings):

| Column | Source |
|---|---|
| IP | address with mask |
| VRF | VRF name (`Global` when none) |
| Status | IP status |
| Tenant | IP tenant |
| DNS | IP `dns_name` |
| Tags | IP tags, comma-separated |
| Subnet | most specific prefix containing the IP in the same VRF |
| Subnet Tenant | subnet tenant |
| Subnet Role | subnet role |
| Subnet Site | subnet site (Site scope, or the Location's site; empty for a Region / Site Group scope) |
| Subnet Tags | subnet tags, comma-separated |
| VLAN ID / VLAN | VLAN assigned to that prefix |

Setup in NetBox: *Customization → Export Templates → Add*

- **Object types**: `IPAM > IP Address`
- **Template code**: contents of `export-templates/ip_addresses.j2`
  (or sync it through a *Data Source* pointing at this repository)
- **MIME type**: `text/csv`
- **File extension**: `csv`
- **As attachment**: checked

Usage: *IPAM → IP Addresses → Export →* template name (the current list filter
is applied).

> Requires a NetBox version that exposes models in the template context
> (access to `ipam.Prefix`), which is the case for recent 4.x releases.
