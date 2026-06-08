# Proxmox Datacenter Manager (Docker)

**Français** · [English](#english)

Image conteneur de [Proxmox Datacenter Manager](https://proxmox.com/en/products/proxmox-datacenter-manager/overview)
(PDM), construite à partir des paquets `.deb` officiels Proxmox et fonctionnant sans systemd.

> **Note :** image destinée aux home labs et aux tests. Ce n'est pas une méthode de
> déploiement officiellement supportée par Proxmox. Pour la production, suivre le
> [guide d'installation officiel](https://pdm.proxmox.com/docs/installation.html).

> **Architecture :** `linux/amd64` uniquement. Proxmox ne publie pas de paquets PDM pour arm64.

## Images

| Registry   | Référence                                            |
| ---------- | ---------------------------------------------------- |
| GHCR       | `ghcr.io/williamboglietti/proxmox-datacenter-manager`|
| Docker Hub | `williamboglietti/proxmox-datacenter-manager`        |

Les tags suivent la version PDM amont (ex. `1.1.4`, `1.1`, `latest`).

## Démarrage rapide

### docker run

```bash
docker run -d --name pdm \
  -p 8443:8443 \
  --hostname pdm \
  --tmpfs /run:exec,mode=0755 \
  -e PDM_ROOT_PASSWORD=change-me \
  -v pdm-config:/etc/proxmox-datacenter-manager \
  -v pdm-data:/var/lib/proxmox-datacenter-manager \
  ghcr.io/williamboglietti/proxmox-datacenter-manager:latest
```

`--hostname pdm` définit le nom du nœud affiché par PDM (sinon c'est l'ID du
conteneur). Ne pas utiliser de variable d'environnement pour cela : changer le
hostname au runtime exige `CAP_SYS_ADMIN`, alors que `--hostname` le règle sans
privilège. `--tmpfs /run` n'est pas obligatoire mais reproduit le `/run` d'un
vrai système et évite l'avertissement `shmem is not on tmpfs` côté PDM.

Le DNS se configure côté Docker (`--dns 1.1.1.1 --dns-search lan.local`, ou les
clés `dns:`/`dns_search:` en Compose) ; PDM affiche ces valeurs telles quelles.

### Docker Compose

```bash
cp .env.example .env   # définir PDM_ROOT_PASSWORD
docker compose up -d
```

Ouvrir `https://<hôte>:8443` (certificat auto-signé) et se connecter avec le realm
`root@pam` et le mot de passe configuré.

## Configuration

| Variable                   | Défaut  | Description                                                       |
| -------------------------- | ------- | ---------------------------------------------------------------- |
| `PDM_ROOT_PASSWORD`        | —       | Mot de passe `root@pam`, (ré)appliqué à chaque démarrage.        |
| `PDM_PORT`                 | `8443`  | Port HTTPS de l'UI/API.                                          |
| `DISABLE_SUBSCRIPTION_NAG` | `false` | Si `true`, masque le popup « Aucun abonnement en cours de validité ». |
| `DISABLE_UPDATES_TAB`      | `true`  | Masque l'onglet « Mises à jour » (les MAJ se font par image, voir ci-dessous). `false` pour le réafficher. |
| `DISABLE_POWER_BUTTONS`    | `true`  | Masque les boutons « Redémarrer »/« Arrêter » (cycle de vie géré via Docker). `false` pour les réafficher. |
| `DISABLE_SUBSCRIPTION_PANEL` | `true` | Masque l'entrée de menu « Abonnement » locale (sans intérêt ici). N'affecte pas « Subscription Registry ». `false` pour la réafficher. |
| `DISABLE_NETWORK_EDIT`     | `true`  | Verrouille la vue « Réseau et heure » en lecture seule : retire l'édition heure/DNS et la section « Interfaces réseau » (gérés via Docker). |
| `DISABLE_REPOSITORIES`     | `true`  | Masque l'onglet « Dépôts » et vide les sources apt (gestion des dépôts inutile : MAJ par image). `false` pour le réafficher. |
| `TZ`                       | —       | Fuseau horaire (ex. `Europe/Paris`), appliqué à chaque démarrage. |

Si `PDM_ROOT_PASSWORD` n'est pas fourni, définir le mot de passe manuellement :

```bash
docker exec -it pdm passwd
docker restart pdm
```

## Mises à jour

PDM se met à jour **en changeant d'image**, pas via `apt` dans le conteneur :
un `apt upgrade` lancé depuis l'onglet « Mises à jour » serait écrit dans la
couche du conteneur (perdu au prochain recreate) et peut échouer faute de
systemd. C'est pourquoi `DISABLE_UPDATES_TAB=true` masque cet onglet.

Pour mettre à jour :

```bash
docker compose pull && docker compose up -d
```

Les images sont republiées automatiquement quand une nouvelle version de PDM
sort (workflow `auto-update`, hebdomadaire), et le tag de l'image reflète la
version PDM embarquée (ex. `1.1.4`). Le timer apt quotidien de PDM est inerte
dans le conteneur (aucun `systemd`/`cron` n'y tourne), il n'effectue donc aucun
check ni upgrade automatique.

## Persistance

| Volume                                | Contenu                          |
| ------------------------------------- | -------------------------------- |
| `/etc/proxmox-datacenter-manager`     | Configuration, certificats, clés |
| `/var/lib/proxmox-datacenter-manager` | État, base de données            |

## Architecture

PDM tourne sous forme de deux daemons, comme sur une installation native, supervisés
par un petit point d'entrée sous `tini` :

- `proxmox-datacenter-privileged-api` — exécuté en root, expose le socket UNIX
  `/run/proxmox-datacenter-manager/priv.sock`.
- `proxmox-datacenter-api` — exécuté en `www-data`, sert l'API et l'UI web en HTTPS
  sur le port 8443.

## Build local

```bash
docker build -t pdm:local .
docker run -d --name pdm -p 8443:8443 -e PDM_ROOT_PASSWORD=change-me pdm:local
```

## Releases

Un tag git `vX.Y.Z` build et publie la version PDM `X.Y.Z` (GHCR + Docker Hub) ;
`latest` et l'alias `X.Y` ne suivent que la version la plus récente.

```bash
git tag v1.1.4
git push origin v1.1.4
```

La publication sur Docker Hub nécessite les secrets de dépôt `DOCKERHUB_USERNAME`
et `DOCKERHUB_TOKEN`.

### Builds de versions historiques

Le workflow `build-versions` (déclenché manuellement, *Actions → Build historical
PDM versions → Run workflow*) reconstruit d'anciennes versions PDM avec les patches
de ce dépôt. Il prend en entrée une liste de versions (par défaut toute la ligne
`1.x`), build chacune via `--build-arg PDM_VERSION=<version>` et publie le tag exact
(`1.0.7`, `1.1.1`, …). Les alias mobiles (`latest`, `1.0`, `1.1`) restent gérés
exclusivement par le workflow de release ci-dessus.

Le Dockerfile pinne le paquet principal `proxmox-datacenter-manager=<version>` et
choisit automatiquement la `-ui`/`-docs` la plus haute ≤ cette version (leur
numérotation comporte des trous : pas de `-ui` 1.1.4, pas de `-docs` 1.0.3/1.0.4).
Pour un build local d'une version précise :

```bash
docker build --build-arg PDM_VERSION=1.0.7 -t pdm:1.0.7 .
```

## Bonus : désactiver le popup d'abonnement (bare-metal)

Sans rapport avec l'image conteneur. Deux scripts, à lancer en root sur l'hôte
concerné. Options communes : `--persist` (réapplique au démarrage et après `apt`),
`--revert` (annule).

### PDM

```bash
curl -fsSL https://raw.githubusercontent.com/williamboglietti/proxmox-datacenter-manager/main/scripts/disable-pdm-popup.sh -o disable-pdm-popup.sh
bash disable-pdm-popup.sh             # appliquer
bash disable-pdm-popup.sh --persist
bash disable-pdm-popup.sh --revert
```

### PVE / PBS

```bash
curl -fsSL https://raw.githubusercontent.com/williamboglietti/proxmox-datacenter-manager/main/scripts/disable-proxmox-popup.sh -o disable-proxmox-popup.sh
bash disable-proxmox-popup.sh             # appliquer
bash disable-proxmox-popup.sh --persist
bash disable-proxmox-popup.sh --revert
```

> Non supporté par Proxmox ; relire un script avant de l'exécuter en root.

## Licence

MIT pour les fichiers de packaging de ce dépôt. Les composants Proxmox embarqués
sont sous AGPL-3.0 — voir le fichier [`NOTICE`](NOTICE) pour le détail des licences
et des sources. Basé sur la [documentation officielle Proxmox](https://pdm.proxmox.com/docs/)
et le dépôt de paquets `download.proxmox.com/debian/pdm`. Proxmox® est une marque
déposée de Proxmox Server Solutions GmbH ; ce projet n'est ni affilié ni approuvé
par Proxmox.

---

## English

Container image for [Proxmox Datacenter Manager](https://proxmox.com/en/products/proxmox-datacenter-manager/overview)
(PDM), built from the official Proxmox `.deb` packages and running without systemd.

> **Note:** This image is intended for home labs and testing. It is not an
> officially supported Proxmox deployment method. For production use, follow the
> [official installation guide](https://pdm.proxmox.com/docs/installation.html).

> **Architecture:** `linux/amd64` only. Proxmox does not publish PDM packages for arm64.

### Images

| Registry   | Reference                                            |
| ---------- | ---------------------------------------------------- |
| GHCR       | `ghcr.io/williamboglietti/proxmox-datacenter-manager`|
| Docker Hub | `williamboglietti/proxmox-datacenter-manager`        |

Tags follow the upstream PDM version (e.g. `1.1.4`, `1.1`, `latest`).

### Quick start

#### docker run

```bash
docker run -d --name pdm \
  -p 8443:8443 \
  --hostname pdm \
  --tmpfs /run:exec,mode=0755 \
  -e PDM_ROOT_PASSWORD=change-me \
  -v pdm-config:/etc/proxmox-datacenter-manager \
  -v pdm-data:/var/lib/proxmox-datacenter-manager \
  ghcr.io/williamboglietti/proxmox-datacenter-manager:latest
```

`--hostname pdm` sets the node name shown by PDM (otherwise it's the container
ID). Don't use an environment variable for this: changing the hostname at
runtime requires `CAP_SYS_ADMIN`, whereas `--hostname` sets it without any
privilege. `--tmpfs /run` is optional but mirrors a real system's `/run` and
avoids PDM's `shmem is not on tmpfs` warning.

DNS is configured on the Docker side (`--dns 1.1.1.1 --dns-search lan.local`, or
the `dns:`/`dns_search:` keys in Compose); PDM displays those values as-is.

#### Docker Compose

```bash
cp .env.example .env   # set PDM_ROOT_PASSWORD
docker compose up -d
```

Open `https://<host>:8443` (self-signed certificate) and log in with the `root@pam`
realm and the configured password.

### Configuration

| Variable                   | Default | Description                                            |
| -------------------------- | ------- | ------------------------------------------------------ |
| `PDM_ROOT_PASSWORD`        | —       | `root@pam` password, (re)applied on every start.       |
| `PDM_PORT`                 | `8443`  | HTTPS port for the UI/API.                             |
| `DISABLE_SUBSCRIPTION_NAG` | `false` | When `true`, hides the "No valid subscription" dialog. |
| `DISABLE_UPDATES_TAB`      | `true`  | Hides the "Updates" tab (updates are done by image, see below). Set `false` to show it again. |
| `DISABLE_POWER_BUTTONS`    | `true`  | Hides the "Reboot"/"Shutdown" buttons (lifecycle is managed via Docker). Set `false` to show them. |
| `DISABLE_SUBSCRIPTION_PANEL` | `true` | Hides the local "Subscription" menu entry (pointless here). Does not affect "Subscription Registry". Set `false` to show it. |
| `DISABLE_NETWORK_EDIT`     | `true`  | Locks the "Network & Time" view read-only: removes time/DNS editing and the "Network Interfaces" section (managed via Docker). |
| `DISABLE_REPOSITORIES`     | `true`  | Hides the "Repositories" tab and clears apt sources (repo management is pointless: updates via image). Set `false` to show it. |
| `TZ`                       | —       | Timezone (e.g. `Europe/Paris`), applied on every start. |

If `PDM_ROOT_PASSWORD` is not provided, set the password manually:

```bash
docker exec -it pdm passwd
docker restart pdm
```

#### Updates

PDM is updated **by swapping the image**, not via `apt` inside the container:
an `apt upgrade` run from the "Updates" tab would land in the container layer
(lost on the next recreate) and may fail without systemd. That is why
`DISABLE_UPDATES_TAB=true` hides that tab.

To update:

```bash
docker compose pull && docker compose up -d
```

Images are republished automatically when a new PDM version ships (`auto-update`
workflow, weekly), and the image tag mirrors the bundled PDM version (e.g.
`1.1.4`). PDM's daily apt timer is inert in the container (no `systemd`/`cron`
runs), so it performs no automatic check or upgrade.

### Persistence

| Volume                                | Contents                          |
| ------------------------------------- | --------------------------------- |
| `/etc/proxmox-datacenter-manager`     | Configuration, certificates, keys |
| `/var/lib/proxmox-datacenter-manager` | State, database                   |

### Architecture

PDM runs as two daemons, as on a native installation, supervised by a small
entrypoint under `tini`:

- `proxmox-datacenter-privileged-api` — runs as root, exposes the UNIX socket
  `/run/proxmox-datacenter-manager/priv.sock`.
- `proxmox-datacenter-api` — runs as `www-data`, serves the API and web UI over
  HTTPS on port 8443.

### Building locally

```bash
docker build -t pdm:local .
docker run -d --name pdm -p 8443:8443 -e PDM_ROOT_PASSWORD=change-me pdm:local
```

### Releases

A git tag `vX.Y.Z` builds and publishes PDM version `X.Y.Z` (GHCR + Docker Hub);
`latest` and the `X.Y` alias only track the newest version.

```bash
git tag v1.1.4
git push origin v1.1.4
```

Publishing to Docker Hub requires the `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN`
repository secrets.

#### Building historical versions

The `build-versions` workflow (manual trigger, *Actions → Build historical PDM
versions → Run workflow*) rebuilds older PDM versions with this repo's patches. It
takes a list of versions (default: the whole `1.x` line), builds each via
`--build-arg PDM_VERSION=<version>` and publishes the exact tag (`1.0.7`, `1.1.1`, …).
The moving aliases (`latest`, `1.0`, `1.1`) are owned solely by the release workflow above.

The Dockerfile pins the main package `proxmox-datacenter-manager=<version>` and
auto-selects the highest `-ui`/`-docs` ≤ that version (their versioning has gaps:
no `-ui` 1.1.4, no `-docs` 1.0.3/1.0.4). For a local build of a specific version:

```bash
docker build --build-arg PDM_VERSION=1.0.7 -t pdm:1.0.7 .
```

### Bonus: disable the subscription popup (bare-metal)

Unrelated to the container image. Two scripts, run as root on the relevant host.
Common options: `--persist` (re-applies on boot and after `apt`), `--revert` (undo).

#### PDM

```bash
curl -fsSL https://raw.githubusercontent.com/williamboglietti/proxmox-datacenter-manager/main/scripts/disable-pdm-popup.sh -o disable-pdm-popup.sh
bash disable-pdm-popup.sh             # apply
bash disable-pdm-popup.sh --persist
bash disable-pdm-popup.sh --revert
```

#### PVE / PBS

```bash
curl -fsSL https://raw.githubusercontent.com/williamboglietti/proxmox-datacenter-manager/main/scripts/disable-proxmox-popup.sh -o disable-proxmox-popup.sh
bash disable-proxmox-popup.sh             # apply
bash disable-proxmox-popup.sh --persist
bash disable-proxmox-popup.sh --revert
```

> Not supported by Proxmox; review any script before running it as root.

### License

MIT for the packaging files in this repository. The bundled Proxmox components are
licensed under AGPL-3.0 — see the [`NOTICE`](NOTICE) file for license and source
details. Based on the official [Proxmox documentation](https://pdm.proxmox.com/docs/)
and the `download.proxmox.com/debian/pdm` package repository. Proxmox® is a
registered trademark of Proxmox Server Solutions GmbH; this project is not
affiliated with or endorsed by Proxmox.
