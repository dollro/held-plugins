# Shared Traefik per server

One Traefik per server terminates TLS and routes to every app stack on that server (staging and production of several apps). App stacks never start their own proxy: two proxies would fight over ports 80 and 443. Locally and in CI each app uses its own small Caddy instead.

Derived from a production setup that has been running for a long time (including its 3.6 → 3.7 upgrade notes), checked against the Traefik v3.7 docs and tested end to end with an app stack (routing, TLS, login, SSE, header-alias protection). Additions such as CrowdSec can go on top later.

## Files

| File | Holds |
|---|---|
| `compose.yml` | Traefik and a Docker socket proxy; creates the shared `proxy` network |
| `traefik.yml` | Static config: entrypoints (HTTP→HTTPS, header-alias protection), Docker provider via the socket proxy, Let's Encrypt resolver `letsencrypt`, logs |
| `dynamic/middlewares.yml` | `default` chain on every route (compression without SSE), opt-in `secure-headers`, dashboard basic auth |
| `dynamic/tls.yml` | TLS 1.2+, AEAD ciphers, modern curves (Mozilla intermediate) |
| `.env.example` | Image versions and the dashboard hostname |

## Set up once per server

1. Copy this directory to the server (e.g. `/opt/traefik`), `cp .env.example .env`, and fill it in: the current Traefik v3 release (at least 3.7.12), a socket-proxy release, the dashboard hostname. Never `latest`.
2. Replace the ACME email in `traefik.yml` with a team mailbox; expiry warnings go there.
3. Create the dashboard login: `htpasswd -nbB admin '<password>' > .htpasswd` (from `apache2-utils`); keep the password in the team's password manager.
4. Point DNS for the dashboard host and every app host to the server; open ports 80 and 443 only.
5. `docker compose up -d --wait`, then check `docker compose ps` (both healthy) and open `https://<dashboard host>`.
6. Limit container log size on the host (`/etc/docker/daemon.json`: `"log-driver": "json-file", "log-opts": {"max-size": "10m", "max-file": "5"}`), since Traefik logs to stdout.

## How an app stack attaches

The app's deploy compose joins the external network and labels its services. The fullstack template (`compose.deploy.yml`) does this already:

```yaml
services:
  django:
    networks:
      default: {}
      proxy: {}
    labels:
      - "traefik.enable=true"
      - "traefik.docker.network=proxy"
      - "traefik.http.routers.<project>-<env>-web.rule=Host(`app.example.com`)"
      - "traefik.http.routers.<project>-<env>-web.entrypoints=websecure"
      - "traefik.http.routers.<project>-<env>-web.tls.certresolver=letsencrypt"
      - "traefik.http.services.<project>-<env>-web.loadbalancer.server.port=5000"
networks:
  proxy:
    external: true
```

Rules:

- **Router and service names are unique per server:** include project and environment, otherwise two stacks overwrite each other's routes.
- **Only services that face the internet join `proxy`;** databases and internal services stay on the stack's default network. Internal calls use a project-unique alias, never a bare service name that other stacks on `proxy` also have.
- **Quote label values** in compose (backticks, `&&`).
- **Publish no ports** on app services in production; Traefik reaches them over `proxy`.

## Operate

- **Update** (security releases promptly):
  1. Compare running and latest version: `docker compose exec traefik traefik version`, the releases page.
  2. Read the migration notes for every minor in between (`docs/content/migrate/v3.md` in the Traefik repo); most breaking changes concern Kubernetes, Gateway API, Consul or Nomad, not the Docker and file providers used here.
  3. Back up `.env`, `compose.yml`, `traefik.yml` and `dynamic/` with a timestamp suffix, outside `dynamic/` (the file provider would load a backup there).
  4. Bump `TRAEFIK_VERSION`, `docker compose config -q`, `docker compose pull`, `docker compose up -d --wait`.
  5. Verify: both services healthy, `traefik version`, no new warn/error lines in `docker compose logs traefik`, and every routed host with `curl -sI --resolve <host>:443:127.0.0.1 https://<host>/`. Fix new warnings: they usually announce a secure default that is off.
  6. Rollback: restore the backups and the previous version, `docker compose up -d`.
- **Config changes:** `dynamic/` is reloaded on save; `traefik.yml` (static) needs `docker compose restart traefik`.
- **Which compose file runs a container:** check `docker inspect -f '{{ index .Config.Labels "com.docker.compose.project.working_dir" }}' <container>` before editing; servers collect duplicate stack directories.
- **Certificates:** the TLS challenge needs port 443 reachable from the internet. Behind a firewall or for wildcard certificates use a DNS challenge instead (provider API token as a secret, not in the file).
- **Backups:** the `acme` volume (certificates) and this directory with its `.env` and `.htpasswd`.
- **Logs:** `docker compose logs -f traefik`. Access logs never include headers (cookies, authorization).

## Pitfalls

- **Compression and SSE:** a compress middleware on the entrypoint applies to every route, and Traefik excludes no content type by default; without the exclusion it gzips `text/event-stream` (tested). Exclude it.
- **Label network not joined:** `traefik.docker.network=proxy` on a service that is not on the `proxy` network gives a 504 for that host, and the log says `Could not find network named "proxy" for container`. Every routed service lists `proxy` under `networks:` (and the compose file declares it `external: true`).
- **Secrets in compose files:** tokens belong in the stack's env file (encrypted where the stack uses SOPS), never inline in `compose.yml`.
- **Header aliases:** without `aliasHeadersStrategy: delete`, a client can send `X_Forwarded_Proto` and WSGI backends read it as `X-Forwarded-Proto` (CVE-2026-88879, fixed in 3.7.12, effective only with the option set).
- **Docker socket:** never mount it into Traefik directly; the socket proxy allows only reading containers and events.
- **HSTS preload** is a domain-wide, practically irreversible decision; not a per-app label.
- **`sniStrict: true`:** a host without a valid certificate gets a TLS error instead of Traefik's invalid default certificate; check DNS and port 443 first when a new host fails right after deploy.
- **Metrics need an explicit entrypoint:** enabling Prometheus metrics (or `api.insecure`) creates an implicit `traefik` entrypoint on :8080. Declare it in `traefik.yml` with `aliasHeadersStrategy: delete` like the others, otherwise the header-alias warning stays and the protection is missing there; never publish :8080.
- **Adding CrowdSec later:** it reads Traefik's access log from a file, so switch `log`/`accessLog` to `filePath` on a host volume (with `maxSize`/`maxBackups`), and set `maxResponseBodySize` and an explicit `trustForwardHeader` on its ForwardAuth middleware (3.6.14+ warns otherwise).
- **Traefik reads one static source:** a file *or* env vars *or* CLI flags, never a mix.
