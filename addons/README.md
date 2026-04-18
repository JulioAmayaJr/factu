# Addons opcionales

Por defecto, `docker-compose.yml` monta la **raíz del repositorio** en `/mnt/extra-addons`, de modo que los módulos `tgr_l10n_sv*`, `om_*`, etc. quedan en el addons path sin mover carpetas.

Use esta carpeta solo si desea añadir módulos de terceros adicionales o enlaces simbólicos; no es obligatoria para el flujo Docker descrito en `DOCKER.md`.
