# __PROJECT_TITLE__

Django (web, admin, REST API, auth)
<!-- >>> realtime -->
and a FastAPI realtime service (Server-Sent Events)
<!-- <<< realtime -->
with Vue 3 islands and an SPA under `/app/`, on PostgreSQL, Redis and Celery. Django serves every page; the browser sees one origin.

| Page | Read it when |
|-|-|
| [Architecture](architecture.md) | You change how services, data or login work, or deviate from the reference stack |
| [Environments](environments.md) | You add a setting or secret, or need to know how a value reaches Docker, Django and Vue |
| [Operations](operations.md) | You set up a server, release, deploy, roll back, back up or restore |

## Start

```bash
task setup     # first run: env file, images, dependencies
task dev:up    # background, waits until healthy -> http://localhost:8000
task ci        # everything CI runs before merge
task --list    # all commands
```

The command surface for people and agents is `CLAUDE.md` in the repository root.
