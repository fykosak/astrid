# Docker container

## Vývoj
- nutnost: nainstalovaný `docker` a `docker-compose-plugin`
- vytvoření aktuální image: `docker compose build` (potřeba spustit před prvním spuštěním)
- vytvoření mount složek (případný `chown` pro vlastnění správným uživatelem): `mkdir config containers repos ssh`
- spuštění: `docker compose up`
- spouštění příkazů uvnitř dockeru: `docker exec -it astrid <příkaz>`
     - stáhnutí `fykosak/buildtools` (potřeba před prvním buildem repozitáře): `docker exec -it astrid podman pull docker.io/fykosak/buildtools`
