# netbox

Dépôt regroupant l'ensemble de mes projets autour de [NetBox](https://github.com/netbox-community/netbox).

## Structure

```
.
├── scripts/                    # Scripts NetBox (custom scripts, signaux)
│   ├── create_vxlan_script.py  # Création d'un VLAN/VNI associé à un L2VPN (+ subnet optionnel)
│   ├── vxlan.py                # Provisionnement d'un VXLAN (« New VXLAN »)
│   └── naming_fr.py            # Nommage automatique des équipements (signal pre_save)
├── export-templates/           # Export templates NetBox (Jinja2)
│   └── ip_addresses.j2         # Export CSV des adresses IP
└── README.md
```

D'autres répertoires pourront être ajoutés à la racine pour les futurs projets
(ex. `reports/`, `plugins/`, `ansible/`…).

## Scripts

### `create_vxlan_script.py` / `vxlan.py`

Custom scripts NetBox (`extras.scripts.Script`) à déposer dans le répertoire
`SCRIPTS_ROOT` de NetBox ou à importer via *Customization → Scripts*.

### `naming_fr.py`

Génère automatiquement le nom d'un équipement (`Device`) à sa création s'il n'est
pas renseigné, au format :

```
<region>-<site>-<location>-<role>-NN
```

(slugs des objets ; `noregion`, `nosite`, `nolocation`, `norole` si absents).
Pour les patch panels placés dans une baie : `<base>-<rack>-<position>`.

Le receiver `pre_save` est enregistré à l'import du module : celui-ci doit donc
être chargé par NetBox (par exemple depuis `SCRIPTS_ROOT`).

## Export templates

### `ip_addresses.j2`

Export CSV (séparateur `;`, s'ouvre directement dans Excel FR) des adresses IP :

| Colonne | Source |
|---|---|
| IP | adresse avec masque |
| VRF | nom de la VRF (`Global` si aucune) |
| Status | statut de l'IP |
| Tenant | tenant de l'IP |
| DNS | `dns_name` de l'IP |
| Tags | tags de l'IP, séparés par `,` |
| Subnet | préfixe le plus spécifique contenant l'IP dans la même VRF |
| VLAN ID / VLAN | VLAN associé à ce préfixe |

Création dans NetBox : *Customization → Export Templates → Add*

- **Object types** : `IPAM > IP Address`
- **Template code** : contenu de `export-templates/ip_addresses.j2`
  (ou synchronisation via une *Data Source* pointant sur ce dépôt)
- **MIME type** : `text/csv`
- **File extension** : `csv`
- **As attachment** : coché

Utilisation : *IPAM → IP Addresses → Export →* nom du template (le filtre courant
de la liste est appliqué).

> Nécessite une version de NetBox exposant les modèles dans le contexte des
> templates (accès à `ipam.Prefix`), c'est le cas des versions 4.x récentes.
