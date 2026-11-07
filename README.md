# netbox

Dépôt regroupant l'ensemble de mes projets autour de [NetBox](https://github.com/netbox-community/netbox).

## Structure

```
.
├── scripts/                    # Scripts NetBox (custom scripts, signaux)
│   ├── create_vxlan_script.py  # Création d'un VLAN/VNI associé à un L2VPN (+ subnet optionnel)
│   ├── vxlan.py                # Provisionnement d'un VXLAN (« New VXLAN »)
│   └── naming_fr.py            # Nommage automatique des équipements (signal pre_save)
└── README.md
```

D'autres répertoires pourront être ajoutés à la racine pour les futurs projets
(ex. `reports/`, `export-templates/`, `plugins/`, `ansible/`…).

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
