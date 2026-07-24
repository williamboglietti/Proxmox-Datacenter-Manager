<div align="center">
<img src="https://raw.githubusercontent.com/williamboglietti/proxmox-datacenter-manager/main/.github/banner.png" alt="Proxmox Datacenter Manager" width="100%" />

[![Docker Pulls](https://img.shields.io/docker/pulls/williamboglietti/proxmox-datacenter-manager?style=flat&logo=docker&label=Docker%20Pulls)](https://hub.docker.com/r/williamboglietti/proxmox-datacenter-manager) [![Stars](https://img.shields.io/github/stars/williamboglietti/proxmox-datacenter-manager?style=flat&logo=github&label=Stars)](https://github.com/williamboglietti/proxmox-datacenter-manager) [![Release](https://img.shields.io/github/v/release/williamboglietti/proxmox-datacenter-manager?style=flat&logo=github&label=Release)](https://github.com/williamboglietti/proxmox-datacenter-manager/releases) [![License](https://img.shields.io/github/license/williamboglietti/proxmox-datacenter-manager?style=flat&label=License)](https://github.com/williamboglietti/proxmox-datacenter-manager/blob/main/LICENSE) [![Build](https://img.shields.io/github/actions/workflow/status/williamboglietti/proxmox-datacenter-manager/docker-publish.yml?style=flat&logo=githubactions&label=Build)](https://github.com/williamboglietti/proxmox-datacenter-manager/actions)

**Run Proxmox Datacenter Manager in Docker.**
Manage multiple PVE clusters from a single web UI, no dedicated VM needed.

🇫🇷 [Lire en français](README.fr.md)
</div>

---

<!-- Add a screenshot of your PDM dashboard here: ![PDM Dashboard](https://raw.githubusercontent.com/williamboglietti/proxmox-datacenter-manager/main/.github/screenshot.png) -->

## Features

- **Full PDM web UI:** the complete Proxmox Datacenter Manager interface, served over HTTPS on port 8443.
- **Hardened for Docker:** subscription popup, power buttons, updates tab, network editing, and repositories tab are hidden by default (all toggleable via env vars). The container lifecycle is managed by Docker, not the UI.
- **Automated updates:** a weekly GitHub Actions workflow detects new upstream PDM releases and rebuilds the image automatically.
- **Version-pinned builds:** every image tag matches the bundled PDM version (e.g. `1.1.4`). Build any historical version with `--build-arg PDM_VERSION=x.y.z`.
- **Built-in healthcheck:** the API endpoint `/api2/json/ping` is monitored out of the box.
- **No systemd:** runs two lightweight daemons under `tini`, just like a native install but without init system overhead.

## Images

| Registry | Reference |
|---|---|
| Docker Hub | `docker pull williamboglietti/proxmox-datacenter-manager` |
| GHCR | `docker pull ghcr.io/williamboglietti/proxmox-datacenter-manager` |

Tags follow the upstream PDM version: `latest`, `1.1`, `1.1.4`.

> **Architecture:** `linux/amd64` only. Proxmox does not publish PDM packages for arm64.

## Quick Start

### Docker Compose (recommended)

```bash
# Clone and configure
git clone https://github.com/williamboglietti/proxmox-datacenter-manager.git
cd proxmox-datacenter-manager
cp .env.example .env   # edit .env to set your password

# Launch
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

> Open `https://<host>:8443` (self-signed certificate), log in with realm `root@pam` and the configured password.

> **Tip:** `--hostname pdm` sets the node name displayed by PDM. Without it, the container ID is used. `--tmpfs /run` avoids PDM's `shmem is not on tmpfs` warning.

## Configuration

| Variable | Default | Description |
|---|---|---|
| `PDM_ROOT_PASSWORD` | N/A | `root@pam` password, (re)applied on every start. |
| `PDM_PORT` | `8443` | HTTPS port for the UI/API. |
| `DISABLE_SUBSCRIPTION_NAG` | `false` | Hide the "No valid subscription" dialog. |
| `DISABLE_UPDATES_TAB` | `true` | Hide the "Updates" tab (updates are done by image). |
| `DISABLE_POWER_BUTTONS` | `true` | Hide "Reboot"/"Shutdown" buttons (lifecycle via Docker). |
| `DISABLE_SUBSCRIPTION_PANEL` | `true` | Hide the local "Subscription" menu entry. |
| `DISABLE_NETWORK_EDIT` | `true` | Lock "Network & Time" view read-only (managed via Docker). |
| `DISABLE_REPOSITORIES` | `true` | Hide the "Repositories" tab and clear apt sources. |
| `TZ` | N/A | Timezone (e.g. `Europe/Paris`), applied on every start. |

If `PDM_ROOT_PASSWORD` is not provided, set the password manually:

```bash
docker exec -it pdm passwd
docker restart pdm
```

DNS is configured on the Docker side (`--dns 1.1.1.1 --dns-search lan.local`, or the `dns:`/`dns_search:` keys in Compose); PDM displays those values as-is.

## Persistence

| Volume | Contents |
|---|---|
| `/etc/proxmox-datacenter-manager` | Configuration, certificates, keys |
| `/var/lib/proxmox-datacenter-manager` | State, database |

## Updates

PDM is updated **by swapping the image**, not via `apt` inside the container. An `apt upgrade` from the "Updates" tab would write to the container layer (lost on recreate) and may fail without systemd.

```bash
docker compose pull && docker compose up -d
```

Images are republished automatically when a new PDM version ships (weekly `auto-update` workflow). PDM's daily apt timer is inert in the container (no systemd/cron runs).

## Architecture

PDM runs as two daemons, just like a native install, supervised by a small entrypoint under `tini`:

- `proxmox-datacenter-privileged-api`: runs as root, exposes the UNIX socket `/run/proxmox-datacenter-manager/priv.sock`.
- `proxmox-datacenter-api`: runs as `www-data`, serves the API and web UI over HTTPS on port 8443.

## Building Locally

```bash
docker build -t pdm:local .
docker run -d --name pdm -p 8443:8443 -e PDM_ROOT_PASSWORD=change-me pdm:local
```

To build a specific historical version:

```bash
docker build --build-arg PDM_VERSION=1.0.7 -t pdm:1.0.7 .
```

## Releases

A git tag `vX.Y.Z` builds and publishes PDM version `X.Y.Z` to GHCR and Docker Hub. `latest` and `X.Y` aliases track the newest version only.

```bash
git tag v1.1.4 && git push origin v1.1.4
```

The `build-versions` workflow (manual trigger via *Actions -> Build historical PDM versions*) rebuilds older versions. The Dockerfile pins `proxmox-datacenter-manager=<version>` and auto-selects the matching `-ui`/`-docs` packages.

## Bonus: Disable Subscription Popup (Bare-Metal)

Unrelated to the container image. Two scripts, run as root on the target host. Common options: `--persist` (re-applies on boot and after `apt`), `--revert` (undo).

### PDM

```bash
curl -fsSL https://raw.githubusercontent.com/williamboglietti/proxmox-datacenter-manager/main/scripts/disable-pdm-popup.sh | bash
```

### PVE / PBS

```bash
curl -fsSL https://raw.githubusercontent.com/williamboglietti/proxmox-datacenter-manager/main/scripts/disable-proxmox-popup.sh | bash
```

> ⚠️ Not supported by Proxmox. Review any script before running it as root.

## License

MIT for the packaging files in this repository. The bundled Proxmox components are licensed under AGPL-3.0, see the [`NOTICE`](NOTICE) file for details.

Based on the official [Proxmox documentation](https://pdm.proxmox.com/docs/) and the `download.proxmox.com/debian/pdm` package repository. Proxmox® is a registered trademark of Proxmox Server Solutions GmbH; this project is not affiliated with or endorsed by Proxmox.

> **Note:** This image is intended for home labs and testing. It is not an officially supported Proxmox deployment method. For production use, follow the [official installation guide](https://pdm.proxmox.com/docs/installation.html).
