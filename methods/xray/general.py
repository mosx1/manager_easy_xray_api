from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from urllib.parse import quote

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from collections.abc import Sequence
from typing import Any

from methods.xray.config_server import ConfigServer

from configparser import ConfigParser

from pydantic import BaseModel
class EasyXrayError(Exception):
    """Base error for easy-xray operations."""


class CommandNotFoundError(EasyXrayError):
    """Required external command is missing."""

DEFAULT_EMAIL = "love@xray.com"
XRAY_CONFIG_PATH = Path("/usr/local/etc/xray/config.json")
XRAY_DAT_DIR = Path("/usr/local/share/xray/")
NGINX_SITES_ENABLED = Path("/etc/nginx/sites-enabled/")
XRAY_INSTALL_URL = (
    "https://github.com/XTLS/Xray-install/raw/main/install-release.sh"
)


@dataclass
class ConfParams:
    """Parameters for config generation (`conf` command)."""

    address: str
    server_name4cdn: str = ""
    user_id: str | None = None
    short_id: str | None = None
    service_name: str | None = None


@dataclass
class StatsResult:
    """Collected traffic statistics."""

    lines: list[str] = field(default_factory=list)
    is_client: bool = False
    is_server: bool = False


class User(BaseModel):
    id: str
    name: str

class ClientReality(BaseModel):
    short_id: str

class BaseClientConfig(BaseModel):
    user: User
    reality: ClientReality


@dataclass
class UserLinks:
    """Share links returned when adding a VPN user."""

    reality: str
    xhttp: str | None = None


class EasyXray:
    """Administrate xray server configs (logic ported from ex.sh)."""

    _xray_process: subprocess.Popen[str] | None = None

    @classmethod
    def is_xray_running(cls) -> bool:
        return cls._xray_process is not None and cls._xray_process.poll() is None

    @classmethod
    def stop_xray(cls) -> None:
        process = cls._xray_process
        if process is None or process.poll() is not None:
            cls._xray_process = None
            return

        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        finally:
            cls._xray_process = None

    def _install_customgeo(self) -> None:
        XRAY_DAT_DIR.mkdir(parents=True, exist_ok=True)
        customgeo = self.root / "customgeo.dat"
        if not customgeo.is_file():
            raise EasyXrayError(f"customgeo.dat not copied to {XRAY_DAT_DIR}")
        shutil.copy2(customgeo, XRAY_DAT_DIR / customgeo.name)

    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root or Path(__file__).resolve().parents[2])
        self.conf_dir = self.root / "conf"
        self.stats_log = self.root / "stats.log"
        self.templates_dir = self.root / "templates"
        config = ConfigParser()
        config.read("config.ini")
        self.config = config

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------

    @staticmethod
    def jsonc2json(filename: str | Path) -> str:
        """Remove lines containing // comments from JSONC."""
        path = Path(filename)
        if not path.is_file():
            raise EasyXrayError(f"jsonc2json: file not found: {path}")
        lines = [
            line
            for line in path.read_text(encoding="utf-8").splitlines()
            if "//" not in line
        ]
        return "\n".join(lines)

    @staticmethod
    def load_jsonc(filename: str | Path) -> Any:
        """Parse JSONC file into a Python object."""
        return json.loads(EasyXray.jsonc2json(filename))

    @staticmethod
    def bytes2mb(value: int | str) -> str:
        """Convert byte count to a human-readable string."""
        raw = str(value).strip()
        if not raw:
            return ""
        if not raw.isdigit():
            raw = EasyXray.strip_quotes(raw)
        if not raw.isdigit():
            return raw
        length = len(raw)
        if length > 9:
            head, tail = raw[:-9], raw[-9:]
            return f"{head}.{tail[:2]} GB"
        if length > 6:
            head, tail = raw[:-6], raw[-6:]
            return f"{head}.{tail[:2]} MB"
        if length > 3:
            head, tail = raw[:-3], raw[-3:]
            return f"{head}.{tail[:2]} kB"
        return f"{raw} bytes"

    @staticmethod
    def strip_quotes(value: str | None) -> str:
        """Drop surrounding double quotes from a string."""
        if not value or len(value) < 2:
            return ""
        if value[0] == '"' and value[-1] == '"':
            return value[1:-1]
        return value

    @classmethod
    def pretty_stats(cls, stats_json: str) -> str:
        """Convert xray stats JSON to a pretty byte string."""
        if not stats_json.strip():
            return ""
        data = json.loads(stats_json)
        return cls.bytes2mb(data.get("stat", {}).get("value", ""))

    @staticmethod
    def check_command(
        cmd: str,
        aim: str = "",
        comment: str = "",
    ) -> None:
        """Ensure an external command exists."""
        if shutil.which(cmd):
            return
        message = f"{cmd} not found"
        if aim:
            message += f"; {aim}"
        if comment:
            message += f"\n{comment}"
        raise CommandNotFoundError(message)

    def _chown_if_sudo(self, path: str | Path) -> None:
        sudo_user = os.environ.get("SUDO_USER")
        if not sudo_user:
            return
        subprocess.run(
            ["chown", f"{sudo_user}:{sudo_user}", str(path)],
            check=False,
        )

    def unsafe_mkdir(self, directory: str | Path) -> Path:
        """Create directory, rotating existing paths through .backup chain."""
        dir_path = Path(directory)
        if dir_path.is_dir():
            backup = dir_path.with_name(f"{dir_path.name}.backup")
            backup_backup = dir_path.with_name(f"{dir_path.name}.backup.backup")
            if backup_backup.is_dir():
                shutil.rmtree(backup_backup)
            if backup.is_dir():
                backup.rename(backup_backup)
                self._chown_if_sudo(backup_backup)
            dir_path.rename(backup)
            self._chown_if_sudo(backup)
        dir_path.mkdir(parents=True, exist_ok=True)
        self._chown_if_sudo(dir_path)
        return dir_path

    def cp_to_backup(self, file_path: str | Path) -> None:
        """Copy file to file.backup with the same rotation logic as unsafe_mkdir."""
        src = Path(file_path)
        if not src.is_file():
            raise EasyXrayError(f"cp_to_backup: file not found: {src}")
        backup = src.with_name(f"{src.name}.backup")
        backup_backup = src.with_name(f"{src.name}.backup.backup")
        if backup.is_file():
            shutil.copy2(backup, backup_backup)
            self._chown_if_sudo(backup_backup)
        shutil.copy2(src, backup)
        self._chown_if_sudo(backup)

    def _run(
        self,
        args: Sequence[str],
        *,
        check: bool = True,
        capture_output: bool = False,
        text: bool = True,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        run_env = os.environ.copy()
        run_env["PATH"] = f"{run_env.get('PATH', '')}:/usr/local/bin/"
        if env:
            run_env.update(env)
        return subprocess.run(
            list(args),
            check=check,
            capture_output=capture_output,
            text=text,
            env=run_env,
        )

    def _xray_uuid(self) -> str:
        self.check_command(
            "xray",
            "needed for config generation",
            "to install xray, try: sudo ./ex.sh install",
        )
        result = self._run(["xray", "uuid"], capture_output=True)
        return result.stdout.strip()

    def _xray_x25519(self) -> tuple[str, str]:
        self.check_command("xray")
        output = self._run(["xray", "x25519"], capture_output=True).stdout.strip()
        parts = output.split()
        if parts and parts[0] == "Private":
            private_key = parts[2]
            public_key = parts[5]
        else:
            private_key = parts[1]
            public_key = parts[3]
        return private_key, public_key

    def _openssl_rand_hex(self, nbytes: int = 8) -> str:
        self.check_command("openssl")
        result = self._run(
            ["openssl", "rand", "-hex", str(nbytes)],
            capture_output=True,
        )
        return result.stdout.strip()

    # def _autogenerate_service_name(self) -> str:
    #     self.check_command("openssl")
    #     raw = self._run(
    #         ["openssl", "rand", "-base64", "9"],
    #         capture_output=True,
    #     ).stdout.strip()
    #     return re.sub(r"[^0-9A-Za-z]", "", raw)

    # @staticmethod
    # def resolve_fake_site(number: int | None = None, custom: str | None = None) -> str:
    #     """Map menu choice to a fake site hostname."""
    #     if number is None:
    #         return DEFAULT_FAKE_SITE
    #     if number == 9:
    #         return custom or DEFAULT_FAKE_SITE
    #     return FAKE_SITES.get(number, DEFAULT_FAKE_SITE)

    def _write_json(self, path: Path, data: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        self._chown_if_sudo(path)

    @staticmethod
    def _inbound_by_tag(config: dict[str, Any], tag: str) -> dict[str, Any]:
        for inbound in config.get("inbounds", []):
            if inbound.get("tag") == tag:
                return inbound
        raise EasyXrayError(f"inbound with tag {tag!r} not found in server config")

    @staticmethod
    def _remove_inbound_by_tag(config: dict[str, Any], tag: str) -> None:
        config["inbounds"] = [
            inbound
            for inbound in config.get("inbounds", [])
            if inbound.get("tag") != tag
        ]

    def _xhttp_enabled(self) -> bool:
        if "Xhttp" not in self.config:
            return False
        return self.config["Xhttp"].get("enabled", "false").strip().lower() in (
            "1",
            "true",
            "yes",
            "on",
        )

    def _xhttp_domain(self) -> str:
        section = self.config["Xhttp"]
        domain = section.get("domain", "").strip()
        if domain:
            return domain
        return self.config["Xray"].get("hostName", "").strip()

    def _xhttp_public_port(self) -> int:
        return int(self.config["Xhttp"].get("public_port", "8443"))

    def _xhttp_internal_port(self) -> int:
        return int(self.config["Xhttp"].get("internal_port", "9443"))

    def _xhttp_mode(self) -> str:
        return self.config["Xhttp"].get("mode", "auto").strip() or "auto"

    def _normalize_xhttp_path(self, path: str) -> str:
        normalized = path.strip()
        if not normalized:
            return f"/{self._openssl_rand_hex(8)}"
        if not normalized.startswith("/"):
            normalized = f"/{normalized}"
        if not normalized.endswith("/"):
            normalized = f"{normalized}/"
        return normalized

    def _xhttp_path_from_config(self) -> str:
        raw = self.config.get("Xhttp", "path", fallback="").strip()
        return self._normalize_xhttp_path(raw)

    def _sync_xhttp_clients_from_reality(
        self,
        server_config: dict[str, Any],
    ) -> None:
        reality = self._inbound_by_tag(server_config, "reality-443")
        xhttp = self._inbound_by_tag(server_config, "xhttp")
        xhttp_clients: list[dict[str, Any]] = []
        for client in reality["settings"]["clients"]:
            xhttp_clients.append(
                {
                    "id": client["id"],
                    "email": client.get("email", DEFAULT_EMAIL),
                }
            )
        xhttp["settings"]["clients"] = xhttp_clients

    def _apply_xhttp_inbound(self, server_config: dict[str, Any]) -> None:
        xhttp = self._inbound_by_tag(server_config, "xhttp")
        xhttp["listen"] = "0.0.0.0"
        xhttp["port"] = self._xhttp_internal_port()
        path = self._xhttp_path_from_config()
        xhttp["streamSettings"]["xhttpSettings"]["mode"] = self._xhttp_mode()
        xhttp["streamSettings"]["xhttpSettings"]["path"] = path
        self._sync_xhttp_clients_from_reality(server_config)

    def _write_xhttp_nginx_site(self) -> None:
        template_path = self.templates_dir / "template_nginx_xhttp.conf"
        if not template_path.is_file():
            raise EasyXrayError(f"nginx template not found: {template_path}")

        domain = self._xhttp_domain()
        path = self._xhttp_path_from_config()
        content = template_path.read_text(encoding="utf-8")
        content = content.replace("server_domain", domain)
        content = content.replace("public_port", str(self._xhttp_public_port()))
        content = content.replace("internal_port", str(self._xhttp_internal_port()))
        content = content.replace("xhttp_path", path)

        self.unsafe_mkdir(self.conf_dir)
        site_path = self.conf_dir / f"nginx_xhttp_{domain}.conf"
        site_path.write_text(content, encoding="utf-8")
        self._chown_if_sudo(site_path)

    def _build_reality_share_link(
        self,
        *,
        user_id: str,
        short_id: str,
        host_name: str,
        public_key: str,
        fake_site: str,
        port: int = 443,
    ) -> str:
        return (
            f"vless://{user_id}@{host_name}:{port}"
            f"?fragment=&security=reality&encryption=none&pbk={public_key}"
            f"&fp=firefox&type=tcp&flow=xtls-rprx-vision-udp443"
            f"&sni={fake_site}&sid={short_id}#{host_name}|kuzmos.ru"
        )

    def _build_xhttp_share_link(
        self,
        *,
        user_id: str,
        domain: str,
        public_port: int,
        path: str,
        mode: str,
    ) -> str:
        encoded_path = quote(path, safe="")
        return (
            f"vless://{user_id}@{domain}:{public_port}"
            f"?encryption=none&security=tls&type=xhttp&host={domain}"
            f"&sni={domain}&fp=chrome&path={encoded_path}&mode={mode}"
            f"#{domain}|xhttp-kuzmos.ru"
        )

    # ------------------------------------------------------------------
    # Config generation
    # ------------------------------------------------------------------

    async def gen_config_server(self, params: ConfParams | None = None) -> None:
        # if not params.address:
        #     raise EasyXrayError("no address given")

        # cdn_mode = bool(params.server_name4cdn)
        # if cdn_mode:
        #     self.check_command("sed", "needed to make nginx's site to use cdn")

        user_id = self._xray_uuid()
        short_id = self._openssl_rand_hex(8)
        fake_site = self.config["Xray"].get("fake_site")
        email = DEFAULT_EMAIL

        self.unsafe_mkdir(self.conf_dir)

        # if cdn_mode:
        #     listen = params.address
        #     service_name = service_name or self._autogenerate_service_name()
        #     template_site = self.root / "template_site4cdn.conf"
        #     site_content = template_site.read_text(encoding="utf-8")
        #     site_content = site_content.replace(
        #         "server_domain_name", params.server_name4cdn
        #     )
        #     site_content = site_content.replace("duckduckgo.com", fake_site)
        #     site_content = site_content.replace("your_service_name", service_name)
        #     site_path = self.conf_dir / "site4cdn.conf"
        #     site_path.write_text(site_content, encoding="utf-8")
        #     self._chown_if_sudo(site_path)
        #     NGINX_SITES_ENABLED.mkdir(parents=True, exist_ok=True)
        #     shutil.copy2(site_path, NGINX_SITES_ENABLED / site_path.name)
        # else:
        listen = "0.0.0.0"

        server_config = self.load_jsonc(self.templates_dir / "template_config_server.jsonc")
        for tag, dest_port in (("reality-443", 443), ("reality-80", 80)):
            inbound = self._inbound_by_tag(server_config, tag)
            inbound["listen"] = listen
            inbound["settings"]["clients"][0]["id"] = user_id
            inbound["settings"]["clients"][0]["email"] = email
            reality = inbound["streamSettings"]["realitySettings"]
            reality["dest"] = f"{fake_site}:{dest_port}"
            reality["serverNames"] = [fake_site]
            reality["privateKey"] = self.config["Xray"].get("private_key")
            reality["shortIds"] = [short_id]

        if self._xhttp_enabled():
            self._apply_xhttp_inbound(server_config)
            self._write_xhttp_nginx_site()
        else:
            self._remove_inbound_by_tag(server_config, "xhttp")

        await ConfigServer.write(server_config)

    # ------------------------------------------------------------------
    # User management
    # ------------------------------------------------------------------

    def _server_config_path(self) -> Path:
        path = self.conf_dir / "config_server.json"
        if not path.is_file():
            raise EasyXrayError(
                "server config and config for default user are needed "
                "but not present; to generate them, try ./ex.sh conf"
            )
        return path

    def _client_config_path(self) -> Path:
        path = self.conf_dir / "config_client.json"
        if not path.is_file():
            raise EasyXrayError(
                "server config and config for default user are needed "
                "but not present; to generate them, try ./ex.sh conf"
            )
        return path

    async def _existing_usernames(self, server_config: dict[str, Any]) -> dict[str, ConfParams]:
        usernames = {}
        reality = self._inbound_by_tag(server_config, "reality-443")
        short_ids = reality["streamSettings"]["realitySettings"]["shortIds"]
        for index, client in enumerate(reality["settings"]["clients"]):
            email = client.get("email", "")
            if "@" in email:
                usernames[email.split("@", 1)[0]] = ConfParams(
                    address=reality["listen"],
                    user_id=client.get("id", ""),
                    short_id=short_ids[index],
                )
        return usernames

    async def add(
        self,
        usernames: Sequence[str],
    ) -> list[UserLinks]:
        if not usernames:
            raise EasyXrayError(
                "usernames not set\n"
                "For default user, use config_client.json generated "
                "by install command. Otherwise use non-void usernames, "
                "preferably of letters and digits only."
            )

        server_config: dict = await ConfigServer.get()
        xray_section = self.config["Xray"]
        xhttp_enabled = self._xhttp_enabled()
        xhttp_inbound: dict[str, Any] | None = None
        xhttp_path = ""
        xhttp_mode = ""
        xhttp_domain = ""
        xhttp_public_port = 8443
        if xhttp_enabled:
            xhttp_inbound = self._inbound_by_tag(server_config, "xhttp")
            xhttp_settings = xhttp_inbound["streamSettings"]["xhttpSettings"]
            xhttp_path = xhttp_settings.get("path") or self._xhttp_path_from_config()
            xhttp_mode = xhttp_settings.get("mode") or self._xhttp_mode()
            xhttp_domain = self._xhttp_domain()
            xhttp_public_port = self._xhttp_public_port()

        existing: dict[str, ConfParams] = await self._existing_usernames(server_config)
        links: list[UserLinks] = []
        update = False
        for username in usernames:
            email = f"{username}@example.com"
            if existing.get(username):
                user_id = existing[username].user_id
                short_id = existing[username].short_id
            else:
                update = True
                user_id = self._xray_uuid()
                short_id = self._openssl_rand_hex(8)

                reality = self._inbound_by_tag(server_config, "reality-443")
                reality["settings"]["clients"].append(
                    {
                        "id": user_id,
                        "email": email,
                        "flow": "xtls-rprx-vision",
                    }
                )
                reality["streamSettings"]["realitySettings"]["shortIds"].append(
                    short_id
                )
                if xhttp_inbound is not None:
                    xhttp_inbound["settings"]["clients"].append(
                        {"id": user_id, "email": email}
                    )

            existing[username] = ConfParams(
                address=self._inbound_by_tag(server_config, "reality-443")["listen"],
                user_id=user_id,
                short_id=short_id,
            )
            reality_link = self._build_reality_share_link(
                user_id=user_id,
                short_id=short_id,
                host_name=xray_section["hostName"],
                public_key=xray_section["public_key"],
                fake_site=xray_section["fake_site"],
            )
            xhttp_link: str | None = None
            if xhttp_enabled:
                xhttp_link = self._build_xhttp_share_link(
                    user_id=user_id,
                    domain=xhttp_domain,
                    public_port=xhttp_public_port,
                    path=xhttp_path,
                    mode=xhttp_mode,
                )
            links.append(UserLinks(reality=reality_link, xhttp=xhttp_link))

        if update:
            await ConfigServer.write(server_config)
            await self.push()
        return links

    async def remove_users(
        self,
        usernames: Sequence[str],
    ) -> None:
        if not usernames:
            raise EasyXrayError("usernames not set")

        for username in usernames:
            server_config = await ConfigServer.get()
            email = f"{username}@example.com"
            reality = self._inbound_by_tag(server_config, "reality-443")
            clients = reality["settings"]["clients"]
            short_ids = reality["streamSettings"]["realitySettings"]["shortIds"]
            kept_clients: list[dict[str, Any]] = []
            kept_short_ids: list[str] = []
            for client, short_id in zip(clients, short_ids, strict=True):
                if client.get("email") != email:
                    kept_clients.append(client)
                    kept_short_ids.append(short_id)
            reality["settings"]["clients"] = kept_clients
            reality["streamSettings"]["realitySettings"]["shortIds"] = kept_short_ids

            if self._xhttp_enabled():
                xhttp = self._inbound_by_tag(server_config, "xhttp")
                xhttp["settings"]["clients"] = [
                    client
                    for client in xhttp["settings"]["clients"]
                    if client.get("email") != email
                ]

            await ConfigServer.write(server_config)
            await self.push()


    def import_users(self, from_dir: str | Path, to_dir: str | Path) -> list[str]:
        source = Path(from_dir)
        target = Path(to_dir)
        if not source.is_dir() or not target.is_dir():
            raise EasyXrayError("both directories (from and to) should be set")

        server_path = target / "config_server.json"
        client_template_path = target / "config_client.json"
        if not server_path.is_file() or not client_template_path.is_file():
            raise EasyXrayError(
                "target directory must contain config_server.json and config_client.json"
            )

        self.cp_to_backup(server_path)
        imported: list[str] = []

        for client_file in sorted(source.glob("config_client_*.json")):
            if client_file.name == "config_client.json":
                continue

            client_data = json.loads(client_file.read_text(encoding="utf-8"))
            email = client_data["outbounds"][0]["settings"]["vnext"][0]["users"][0][
                "email"
            ]
            uname_from_email = email.split("@", 1)[0]
            username = uname_from_email

            target_client = target / f"config_client_{username}.json"
            if target_client.is_file():
                continue

            user_id = client_data["outbounds"][0]["settings"]["vnext"][0]["users"][0][
                "id"
            ]
            short_id = client_data["outbounds"][0]["streamSettings"][
                "realitySettings"
            ]["shortId"]

            client_template = json.loads(
                client_template_path.read_text(encoding="utf-8")
            )
            outbound = client_template["outbounds"][0]
            outbound["settings"]["vnext"][0]["users"][0]["id"] = user_id
            outbound["settings"]["vnext"][0]["users"][0]["email"] = (
                f"{username}@example.com"
            )
            outbound["streamSettings"]["realitySettings"]["shortId"] = short_id
            self._write_json(target_client, client_template)

            cdn_template_path = self.conf_dir / "config_client_cdn.json"
            if cdn_template_path.is_file():
                cdn_config = json.loads(cdn_template_path.read_text(encoding="utf-8"))
                cdn_config["outbounds"][0]["settings"]["vnext"][0]["users"][0][
                    "id"
                ] = user_id
                cdn_user_path = target / f"config_client_{username}_cdn.json"
                self._write_json(cdn_user_path, cdn_config)

            server_config = json.loads(server_path.read_text(encoding="utf-8"))
            reality = self._inbound_by_tag(server_config, "reality-443")
            reality["settings"]["clients"].append(
                {
                    "id": user_id,
                    "email": f"{username}@example.com",
                    "flow": "xtls-rprx-vision",
                }
            )
            reality["streamSettings"]["realitySettings"]["shortIds"].append(short_id)
            try:
                xhttp = self._inbound_by_tag(server_config, "xhttp")
                xhttp["settings"]["clients"].append(
                    {"id": user_id, "email": f"{username}@example.com"}
                )
            except EasyXrayError:
                pass
            self._write_json(server_path, server_config)
            imported.append(username)

        return imported

    # ------------------------------------------------------------------
    # Links, push, stats, install lifecycle
    # ------------------------------------------------------------------

    def generate_link(self, config_file: str | Path) -> str:
        """Generate a vless link from a client config file."""
        path = Path(config_file)
        config = json.loads(path.read_text(encoding="utf-8"))
        outbound = config["outbounds"][0]
        network = outbound["streamSettings"]["network"]

        user = outbound["settings"]["vnext"][0]["users"][0]
        user_id = user["id"]
        address = outbound["settings"]["vnext"][0]["address"]
        if ":" in address:
            address = f"[{address}]"

        if network == "xhttp":
            port = outbound["settings"]["vnext"][0]["port"]
            xhttp_settings = outbound["streamSettings"]["xhttpSettings"]
            path = xhttp_settings.get("path", "/")
            mode = xhttp_settings.get("mode", "auto")
            tls = outbound["streamSettings"].get("tlsSettings") or {}
            domain = tls.get("serverName") or address.strip("[]")
            return self._build_xhttp_share_link(
                user_id=user_id,
                domain=domain,
                public_port=port,
                path=path,
                mode=mode,
            )

        if network != "tcp":
            raise EasyXrayError(f"unsupported client transport network: {network}")

        port = outbound["settings"]["vnext"][0]["port"]
        reality = outbound["streamSettings"]["realitySettings"]
        public_key = reality["publicKey"]
        server_name = reality["serverName"]
        short_id = reality["shortId"]
        return (
            f"vless://{user_id}@{address}:{port}"
            f"?fragment=&security=reality&encryption=none&pbk={public_key}"
            f"&fp=firefox&type=tcp&flow=xtls-rprx-vision-udp443"
            f"&sni={server_name}&sid={short_id}#kuzmos.ru"
        )

    def write_client_links(self, output_file: str | Path | None = None) -> Path:
        """Generate conf/client_links.txt from all config_client_*.json files."""
        output = Path(output_file or self.conf_dir / "client_links.txt")
        client_files = sorted(self.conf_dir.glob("config_client_*.json"))
        if not client_files:
            raise EasyXrayError(
                "no config is given, and there are no any client configs"
            )

        chunks: list[str] = []
        for client_file in client_files:
            if client_file.name == "config_client.json":
                continue
            client_name = client_file.stem.removeprefix("config_client_")
            link = self.generate_link(client_file)
            chunks.append(f"{client_name}\n{link}\n")

        output.write_text("".join(chunks).rstrip("\n"), encoding="utf-8")
        self._chown_if_sudo(output)
        return output

    async def push(
        self,
        require_root: bool = True,
    ) -> None:
        if require_root and os.geteuid() != 0:
            raise EasyXrayError(
                "you should have root privileges for that, try"
            )

        server_config = await ConfigServer.get()
        self._install_customgeo()
        with open(XRAY_CONFIG_PATH, "w") as config_file:
            json.dump(server_config, config_file, indent=2, ensure_ascii=False)

        if shutil.which("systemctl"):
            self._run(["systemctl", "restart", "xray"], check=False)
            return

        self._run(
            ["xray", "run", "-test", "-config", str(XRAY_CONFIG_PATH)],
        )

        process = type(self)._xray_process
        if process is not None and process.poll() is None:
            type(self).stop_xray()

        type(self)._xray_process = subprocess.Popen(
            ["xray", "run", "-config", str(XRAY_CONFIG_PATH)],
            text=True,
        )

    def _xray_api_stats(self, name: str) -> str:
        result = self._run(
            [
                "xray",
                "api",
                "stats",
                "-server=127.0.0.1:8080",
                f"-name={name}",
            ],
            capture_output=True,
            check=False,
        )
        return result.stdout.strip()

    def collect_stats(self, *, reset: bool = False) -> StatsResult:
        """Collect traffic statistics and optionally reset counters."""
        client_proxy_down = self._xray_api_stats(
            "outbound>>>proxy>>>traffic>>>downlink"
        )
        server_direct_down = self._xray_api_stats(
            "outbound>>>direct>>>traffic>>>downlink"
        )

        result = StatsResult()
        timestamp = datetime.now().astimezone().isoformat(sep=" ", timespec="seconds")
        log_lines = ["", "----------", timestamp]

        if client_proxy_down:
            result.is_client = True
            result.lines.extend(
                [
                    f"Downloaded via server: {self.pretty_stats(client_proxy_down)}",
                    f"Uploaded via server: {self.pretty_stats(self._xray_api_stats('outbound>>>proxy>>>traffic>>>uplink'))}",
                    f"Downloaded via client directly: {self.pretty_stats(self._xray_api_stats('outbound>>>direct>>>traffic>>>downlink'))}",
                    f"Uploaded via client directly: {self.pretty_stats(self._xray_api_stats('outbound>>>direct>>>traffic>>>uplink'))}",
                ]
            )
        elif server_direct_down:
            result.is_server = True
            result.lines.append(
                f"Downloaded in total: {self.pretty_stats(server_direct_down)}"
            )
            result.lines.append(
                "Uploaded in total: "
                f"{self.pretty_stats(self._xray_api_stats('outbound>>>direct>>>traffic>>>uplink'))}"
            )

            server_config = json.loads(
                self._server_config_path().read_text(encoding="utf-8")
            )
            reality = self._inbound_by_tag(server_config, "reality-443")
            for client in reality["settings"]["clients"]:
                email = client["email"]
                result.lines.append("")
                result.lines.append(
                    f"Downloaded by {email}: "
                    f"{self.pretty_stats(self._xray_api_stats(f'user>>>{email}>>>traffic>>>downlink'))}"
                )
                result.lines.append(
                    f"Uploaded by {email}: "
                    f"{self.pretty_stats(self._xray_api_stats(f'user>>>{email}>>>traffic>>>uplink'))}"
                )
        else:
            raise EasyXrayError(
                "xray should be running to aquire or reset statistics"
            )

        log_lines.extend(result.lines)
        with self.stats_log.open("a", encoding="utf-8") as log_file:
            log_file.write("\n".join(log_lines) + "\n")

        if reset:
            reset_result = self._run(
                [
                    "xray",
                    "api",
                    "statsquery",
                    "-server=127.0.0.1:8080",
                    "-reset",
                ],
                capture_output=True,
                check=False,
            )
            if reset_result.returncode != 0:
                raise EasyXrayError("statistics reset failed")

        return result

    async def install_xray(
        self,
        *,
        setup_cdn: bool = False,
        force_reinstall: bool = False,
    ) -> None:
        """Download and install xray using the official install script."""
        if os.geteuid() != 0:
            raise EasyXrayError(
                "you should have root privileges to install xray, try"
            )
        await self.gen_config_server()
        self._install_customgeo()

        if shutil.which("xray") and not force_reinstall:
            await self.push()
            return

        self.check_command(
            "curl",
            "required to download the xray installation script",
        )
        install_script = self._run(
            ["curl", "-L", XRAY_INSTALL_URL],
            capture_output=True,
        ).stdout
        self._run(["bash", "-c", install_script, "@", "install"])

        if setup_cdn:
            cert_pem = self.root / "cert.pem"
            cert_key = self.root / "cert.key"
            nginx_conf = self.root / "nginx.conf"
            if not cert_pem.is_file() or not cert_key.is_file() or not nginx_conf.is_file():
                raise EasyXrayError(
                    "no Cloudflare certificates cert.* or no nginx.conf found, aborting"
                )
            Path("/etc/ssl/certs/").mkdir(parents=True, exist_ok=True)
            Path("/etc/ssl/private/").mkdir(parents=True, exist_ok=True)
            NGINX_SITES_ENABLED.mkdir(parents=True, exist_ok=True)
            shutil.copy2(cert_pem, Path("/etc/ssl/certs/cert.pem"))
            shutil.copy2(cert_key, Path("/etc/ssl/private/cert.key"))
            shutil.copy2(nginx_conf, Path("/etc/nginx/nginx.conf"))
            self._run(["systemctl", "enable", "nginx"], check=False)

        await self.push()

    def upgrade_xray(self) -> None:
        """Upgrade xray without touching configs."""
        self.check_command("curl")
        install_script = self._run(
            ["curl", "-L", XRAY_INSTALL_URL],
            capture_output=True,
        ).stdout
        self._run(["bash", "-c", install_script, "@", "install"])

    def remove_xray(self) -> None:
        """Remove xray using the official install script."""
        if os.geteuid() != 0:
            raise EasyXrayError(
                "you should have root privileges for that, try\nsudo ./ex.sh push"
            )
        self.check_command("curl")
        install_script = self._run(
            ["curl", "-L", XRAY_INSTALL_URL],
            capture_output=True,
        ).stdout
        self._run(["bash", "-c", install_script, "@", "remove", "--purge"])

    # async def get_base_client_config(self, base_client_config: BaseClientConfig) -> dict:
    #     client_config = self.load_jsonc(self.templates_dir / "template_config_client.jsonc")
    #     vnext_entry = {
    #         "address": self.config["Xray"].get("hostName"),
    #         "port": 443,
    #         "users": [
    #             {
    #                 "id": base_client_config.user.id,
    #                 "email": f"{base_client_config.user.name}@example.com",
    #                 "encryption": "none",
    #                 "flow": "xtls-rprx-vision-udp443",
    #             }
    #         ],
    #     }
    #     client_reality = {
    #         "fingerprint": "firefox",
    #         "serverName": self.config["Xray"].get("fake_site"),
    #         "show": False,
    #         "publicKey": self.config["Xray"].get("public_key"),
    #         "shortId": base_client_config.reality.short_id,
    #     }
    #     for outbound in client_config["outbounds"]:
    #         if outbound.get("settings", {}).get("vnext") is not None:
    #             outbound["settings"]["vnext"] = [vnext_entry]
    #         if outbound.get("streamSettings", {}).get("realitySettings") is not None:
    #             outbound["streamSettings"]["realitySettings"] = client_reality
    #     return client_config