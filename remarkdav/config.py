from dynaconf import Dynaconf

settings = Dynaconf(
    envvar_prefix="REMARKDAV",
    settings_files=["/etc/remarkdav/settings.toml"],
)
