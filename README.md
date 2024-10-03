# Astrid
Astrid (Automatická Sazba Textů -rid) je minimalistický server určen pro
automatickou kompilaci LaTeX souborů v rámci gitového repozitáře v
perzistentním uložišti. Kompilace probíhá v rámci `docker` podporocesu, který
využívá [buildtools image](https://github.com/fykosak/docker-buildtools).

## Spuštění
Aplikace je navržena pro použití uvnitř docker kontejneru. Pro deployment lze
využít sample [docker compose](docker/docker-compose.prod.yml). [Docker
image](https://github.com/fykosak/astrid/pkgs/container/astrid) se vytvoří
automaticky pomocí github actions.

Po spuštění se automaticky ve složce `data` vytvoří potřebné složky
a konfigurace.
- `config` - obsahuje konfiguraci ve formátu `TOML`
- `containers` - složka sloužící jako cache pro docker image uvnitř Astrid
- `log` - log soubory o historii jednotlivých spuštění a posledním spuštění kompilace
- `ssh` - ssh soubory pro uživatele uvnitř Astrid, potřeba pro přístup ke gitovým repozitářům

> [!WARNING]
> Konfigurační soubor `config.toml` obsahuje proměnnou `SECRET_KEY`. Tu je
> potřeba nastavit na dostatečně dlouhý náhodný řetězec znaků, aby byla zajištěno
> bezpečné ukládání `SESSION` a přihlašování.

### Vývoj
Pro lokální spuštění určeno pro vývoj stačí přejít do složky `docker` a v ní
spustit `docker compose up`. Vše ostatní se vytvoří automaticky. Po prvním
spuštění je třeba upravit konfigurační soubor `config.toml`, ve kterém je třeba
odkomentovat proměnnou `SECRET_KEY`. Dále je doporučeno nastavit ostatní
proměnné určené pro vývoj.

## Spuštění buildu
Kompilace repozitáře lze ručně spustit pomocí zadání url
`https://<astridUrl>/build/<repositoryName>`. Automaticky lze spouštět
zavoláním git post-receive hooku, který obdobný request provede.
Sample script je v souboru [touch.sh](touch.sh).

## Implementace
Astrid je napsána v Pythonu pomocí knihovny `Flask` (dříve `CherryPy`).
Společní s ní je využita integrace knihovny `authlib`. Aplikace předpokládá, že
uživatelé se přihlašují pomoci OIDC poskytovatele Keycloak, který pošle při
přihlášení přidělené role, které jsou následně kontrolovány dle nastavení
repozitářů.

Pro automatizovaný přístup (spuštění buildu, stahování PDF) je implementované
i přihlašování přes http basic auth pro uživatele specifikované v `users.toml`.

Při vývoji je spuštěna přímo Flask aplikace, pro produkci Astrid využívá WSGI
server `Gunicorn`, který umožňuje aplikaci běžet na více jádrech a vláknech.
