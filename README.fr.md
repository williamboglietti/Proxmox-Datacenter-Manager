<div align="center">
<img src="https://raw.githubusercontent.com/williamboglietti/proxmox-datacenter-manager/main/.github/banner.png" alt="Proxmox Datacenter Manager" width="100%" />

[![Docker Pulls](https://img.shields.io/docker/pulls/williamboglietti/proxmox-datacenter-manager?style=flat&logo=docker&label=Docker%20Pulls)](https://hub.docker.com/r/williamboglietti/proxmox-datacenter-manager)
[![Stars](https://img.shields.io/github/stars/williamboglietti/proxmox-datacenter-manager?style=flat&logo=github&label=Stars)](https://github.com/williamboglietti/proxmox-datacenter-manager)
[![Release](https://img.shields.io/github/v/release/williamboglietti/proxmox-datacenter-manager?style=flat&logo=github&label=Release)](https://github.com/williamboglietti/proxmox-datacenter-manager/releases)
[![License](https://img.shields.io/github/license/williamboglietti/proxmox-datacenter-manager?style=flat&label=License)](https://github.com/williamboglietti/proxmox-datacenter-manager/blob/main/LICENSE)
[![Build](https://img.shields.io/github/actions/workflow/status/williamboglietti/proxmox-datacenter-manager/docker-publish.yml?style=flat&logo=githubactions&label=Build)](https://github.com/williamboglietti/proxmox-datacenter-manager/actions/workflows/docker-publish.yml)

**Proxmox Datacenter Manager dans Docker.**
Gérez plusieurs clusters PVE depuis une seule interface web — sans VM dédiée.

🇬🇧 [Read in English](README.md)
</div>

---

<!-- Ajoutez une capture d'écran de votre dashboard PDM ici : ![Dashboard PDM](https://raw.githubusercontent.com/williamboglietti/proxmox-datacenter-manager/main/.github/screenshot.png) -->

## ✨ Fonctionnalités

- 🖥️ **Interface PDM complète** — l'interface web intégrale de Proxmox Datacenter Manager, servie en HTTPS sur le port 8443.
- 🔒 **Adaptée pour Docker** — le popup d'abonnement, les boutons d'alimentation, l'onglet mises à jour, l'édition réseau et l'onglet dépôts sont masqués par défaut (tous configurables via variables d'environnement). Le cycle de vie du conteneur est géré par Docker, pas par l'UI.
- 🔄 **Mises à jour automatiques** — un workflow GitHub Actions hebdomadaire détecte les nouvelles versions PDM en amont et reconstruit l'image automatiquement.
- 📌 **Builds versionnés** — chaque tag d'image correspond à la version PDM embarquée (ex. `1.1.4`). Construisez n'importe quelle version historique avec `--build-arg PDM_VERSION=x.y.z`.
- 🏥 **Healthcheck intégré** — l'endpoint API `/api2/json/ping` est surveillé nativement.
- ⚡ **Sans systemd** — exécute deux daemons légers sous `tini`, comme une installation native mais sans overhead d'init system.

## 📦 Images

| Registre | Référence |
|---|---|
| Docker Hub | `docker pull williamboglietti/proxmox-datacenter-manager` |
| GHCR | `docker pull ghcr.io/williamboglietti/proxmox-datacenter-manager` |

Les tags suivent la version PDM amont : `latest`, `1.1`, `1.1.4`.

> **Architecture :** `linux/amd64` uniquement. Proxmox ne publie pas de paquets PDM pour arm64.

## 🚀 Démarrage rapide

### Docker Compose (recommandé)

```bash
# Cloner et configurer
git clone https://github.com/williamboglietti/proxmox-datacenter-manager.git
cd proxmox-datacenter-manager
cp .env.example .env   # éditez .env pour définir votre mot de passe

# Lancer
docker compose up -d
```

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

> Ouvrir `https://<hôte>:8443` (certificat auto-signé), se connecter avec le realm `root@pam` et le mot de passe configuré.

> **Astuce :** `--hostname pdm` définit le nom du nœud affiché par PDM. Sans cela, c'est l'ID du conteneur qui est utilisé. `--tmpfs /run` évite l'avertissement `shmem is not on tmpfs` de PDM.

## ⚙️ Configuration

| Variable | Défaut | Description |
|---|---|---|
| `PDM_ROOT_PASSWORD` | — | Mot de passe `root@pam`, (ré)appliqué à chaque démarrage. |
| `PDM_PORT` | `8443` | Port HTTPS de l'UI/API. |
| `DISABLE_SUBSCRIPTION_NAG` | `false` | Masque le popup « Aucun abonnement en cours de validité ». |
| `DISABLE_UPDATES_TAB` | `true` | Masque l'onglet « Mises à jour » (MAJ par image). |
| `DISABLE_POWER_BUTTONS` | `true` | Masque les boutons « Redémarrer »/« Arrêter » (cycle de vie via Docker). |
| `DISABLE_SUBSCRIPTION_PANEL` | `true` | Masque l'entrée de menu « Abonnement » locale. |
| `DISABLE_NETWORK_EDIT` | `true` | Verrouille la vue « Réseau et heure » en lecture seule (géré via Docker). |
| `DISABLE_REPOSITORIES` | `true` | Masque l'onglet « Dépôts » et vide les sources apt. |
| `TZ` | — | Fuseau horaire (ex. `Europe/Paris`), appliqué à chaque démarrage. |

Si `PDM_ROOT_PASSWORD` n'est pas fourni, définir le mot de passe manuellement :

```bash
docker exec -it pdm passwd
docker restart pdm
```

Le DNS se configure côté Docker (`--dns 1.1.1.1 --dns-search lan.local`, ou les clés `dns:`/`dns_search:` en Compose) ; PDM affiche ces valeurs telles quelles.

## 📂 Persistance

| Volume | Contenu |
|---|---|
| `/etc/proxmox-datacenter-manager` | Configuration, certificats, clés |
| `/var/lib/proxmox-datacenter-manager` | État, base de données |

## 🔄 Mises à jour

PDM se met à jour **en changeant d'image**, pas via `apt` dans le conteneur. Un `apt upgrade` depuis l'onglet « Mises à jour » serait écrit dans la couche du conteneur (perdu au prochain recreate) et peut échouer sans systemd.

```bash
docker compose pull && docker compose up -d
```

Les images sont republiées automatiquement quand une nouvelle version de PDM sort (workflow `auto-update`, hebdomadaire). Le timer apt quotidien de PDM est inerte dans le conteneur (aucun systemd/cron n'y tourne).

## 🏗️ Architecture

PDM tourne sous forme de deux daemons, comme sur une installation native, supervisés par un petit point d'entrée sous `tini` :

- `proxmox-datacenter-privileged-api` — exécuté en root, expose le socket UNIX `/run/proxmox-datacenter-manager/priv.sock`.
- `proxmox-datacenter-api` — exécuté en `www-data`, sert l'API et l'UI web en HTTPS sur le port 8443.

## 🛠️ Build local

```bash
docker build -t pdm:local .
docker run -d --name pdm -p 8443:8443 -e PDM_ROOT_PASSWORD=change-me pdm:local
```

Pour construire une version historique précise :

```bash
docker build --build-arg PDM_VERSION=1.0.7 -t pdm:1.0.7 .
```

## 📌 Releases

Un tag git `vX.Y.Z` build et publie la version PDM `X.Y.Z` sur GHCR et Docker Hub. `latest` et l'alias `X.Y` ne suivent que la version la plus récente.

```bash
git tag v1.1.4 && git push origin v1.1.4
```

Le workflow `build-versions` (déclenchement manuel via *Actions → Build historical PDM versions*) reconstruit les anciennes versions. Le Dockerfile pinne `proxmox-datacenter-manager=<version>` et choisit automatiquement les paquets `-ui`/`-docs` correspondants.

## 🔧 Bonus : désactiver le popup d'abonnement (bare-metal)

Sans rapport avec l'image conteneur. Deux scripts, à lancer en root sur l'hôte concerné. Options communes : `--persist` (réapplique au démarrage et après `apt`), `--revert` (annule).

### PDM

```bash
curl -fsSL https://raw.githubusercontent.com/williamboglietti/proxmox-datacenter-manager/main/scripts/disable-pdm-popup.sh | bash
```

### PVE / PBS

```bash
curl -fsSL https://raw.githubusercontent.com/williamboglietti/proxmox-datacenter-manager/main/scripts/disable-proxmox-popup.sh | bash
```

> ⚠️ Non supporté par Proxmox ; relire un script avant de l'exécuter en root.

## 📄 Licence

MIT pour les fichiers de packaging de ce dépôt. Les composants Proxmox embarqués sont sous AGPL-3.0 — voir le fichier [`NOTICE`](NOTICE) pour le détail.

Basé sur la [documentation officielle Proxmox](https://pdm.proxmox.com/docs/) et le dépôt de paquets `download.proxmox.com/debian/pdm`. Proxmox® est une marque déposée de Proxmox Server Solutions GmbH ; ce projet n'est ni affilié ni approuvé par Proxmox.

> **Note :** image destinée aux home labs et aux tests. Ce n'est pas une méthode de déploiement officiellement supportée par Proxmox. Pour la production, suivre le [guide d'installation officiel](https://pdm.proxmox.com/docs/installation.html).
