"""Python implementation of easy-xray logic from ex.sh."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from collections.abc import Sequence
from typing import Any, Literal


class EasyXrayError(Exception):
    """Base error for easy-xray operations."""


class CommandNotFoundError(EasyXrayError):
    """Required external command is missing."""


FAKE_SITES = {
    1: "duckduckgo.com",
    2: "www.microsoft.com",
    3: "www.google.com",
    4: "www.bing.com",
    5: "www.yahoo.com",
    6: "www.adobe.com",
    7: "aws.amazon.com",
    8: "www.aliexpress.com",
}
DEFAULT_FAKE_SITE = FAKE_SITES[1]
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
    private_key: str | None = None
    public_key: str | None = None
    short_id: str | None = None
    fake_site: str = DEFAULT_FAKE_SITE
    service_name: str | None = None
    email: str = DEFAULT_EMAIL


@dataclass
class StatsResult:
    """Collected traffic statistics."""

    lines: list[str] = field(default_factory=list)
    is_client: bool = False
    is_server: bool = False


class EasyXray:
    """Administrate xray server configs (logic ported from ex.sh)."""

    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root or Path(__file__).resolve().parent)
        self.conf_dir = self.root / "conf"
        self.stats_log = self.root / "stats.log"

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

    def _autogenerate_service_name(self) -> str:
        self.check_command("openssl")
        raw = self._run(
            ["openssl", "rand", "-base64", "9"],
            capture_output=True,
        ).stdout.strip()
        return re.sub(r"[^0-9A-Za-z]", "", raw)

    @staticmethod
    def resolve_fake_site(number: int | None = None, custom: str | None = None) -> str:
        """Map menu choice to a fake site hostname."""
        if number is None:
            return DEFAULT_FAKE_SITE
        if number == 9:
            return custom or DEFAULT_FAKE_SITE
        return FAKE_SITES.get(number, DEFAULT_FAKE_SITE)

    def _require_conf_tools(self) -> None:
        self.check_command(
            "xray",
            "needed for config generation",
            "to install xray, try: sudo ./ex.sh install",
        )
        self.check_command("jq", "needed for operations with configs")
        self.check_command(
            "openssl",
            "needed for strong random numbers excluding some types of attacks",
        )

    def _write_json(self, path: Path, data: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        self._chown_if_sudo(path)

    # ------------------------------------------------------------------
    # Config generation
    # ------------------------------------------------------------------

    def conf(self, params: ConfParams) -> dict[str, Path]:
        """Generate server and client config files."""
        self._require_conf_tools()
        if not params.address:
            raise EasyXrayError("no address given")

        cdn_mode = bool(params.server_name4cdn)
        if cdn_mode:
            self.check_command("sed", "needed to make nginx's site to use cdn")

        user_id = params.user_id or self._xray_uuid()
        if params.private_key and params.public_key:
            private_key, public_key = params.private_key, params.public_key
        else:
            private_key, public_key = self._xray_x25519()
        short_id = params.short_id or self._openssl_rand_hex(8)
        fake_site = params.fake_site
        email = params.email
        service_name = params.service_name

        self.unsafe_mkdir(self.conf_dir)

        if cdn_mode:
            listen = params.address
            service_name = service_name or self._autogenerate_service_name()
            template_site = self.root / "template_site4cdn.conf"
            site_content = template_site.read_text(encoding="utf-8")
            site_content = site_content.replace(
                "server_domain_name", params.server_name4cdn
            )
            site_content = site_content.replace("duckduckgo.com", fake_site)
            site_content = site_content.replace("your_service_name", service_name)
            site_path = self.conf_dir / "site4cdn.conf"
            site_path.write_text(site_content, encoding="utf-8")
            self._chown_if_sudo(site_path)
            NGINX_SITES_ENABLED.mkdir(parents=True, exist_ok=True)
            shutil.copy2(site_path, NGINX_SITES_ENABLED / site_path.name)
        else:
            listen = "0.0.0.0"

        server_config = self.load_jsonc(self.root / "template_config_server.jsonc")
        for inbound_index in (1, 2):
            inbound = server_config["inbounds"][inbound_index]
            inbound["listen"] = listen
            inbound["settings"]["clients"][0]["id"] = user_id
            inbound["settings"]["clients"][0]["email"] = email
            reality = inbound["streamSettings"]["realitySettings"]
            reality["dest"] = (
                f"{fake_site}:443" if inbound_index == 1 else f"{fake_site}:80"
            )
            reality["serverNames"] = [fake_site]
            reality["privateKey"] = private_key
            reality["shortIds"] = [short_id]

        grpc_inbound = server_config["inbounds"][3]
        grpc_inbound["settings"]["clients"][0]["id"] = user_id
        if cdn_mode:
            grpc_inbound["streamSettings"]["grpcSettings"]["serviceName"] = service_name

        server_path = self.conf_dir / "config_server.json"
        self._write_json(server_path, server_config)

        client_config = self.load_jsonc(self.root / "template_config_client.jsonc")
        vnext_entry = {
            "address": params.address,
            "port": 443,
            "users": [
                {
                    "id": user_id,
                    "email": email,
                    "encryption": "none",
                    "flow": "xtls-rprx-vision-udp443",
                }
            ],
        }
        client_reality = {
            "fingerprint": "firefox",
            "serverName": fake_site,
            "show": False,
            "publicKey": public_key,
            "shortId": short_id,
        }
        for outbound in client_config["outbounds"]:
            if outbound.get("settings", {}).get("vnext") is not None:
                outbound["settings"]["vnext"] = [vnext_entry]
            if outbound.get("streamSettings", {}).get("realitySettings") is not None:
                outbound["streamSettings"]["realitySettings"] = client_reality

        client_path = self.conf_dir / "config_client.json"
        self._write_json(client_path, client_config)

        result = {"server": server_path, "client": client_path}

        if cdn_mode:
            cdn_config = self.load_jsonc(
                self.root / "template_config_client_cdn.jsonc"
            )
            cdn_outbound = cdn_config["outbounds"][0]
            cdn_outbound["settings"]["vnext"][0]["address"] = params.server_name4cdn
            cdn_outbound["settings"]["vnext"][0]["users"][0]["id"] = user_id
            cdn_outbound["streamSettings"]["grpcSettings"]["serviceName"] = (
                service_name
            )
            cdn_path = self.conf_dir / "config_client_cdn.json"
            self._write_json(cdn_path, cdn_config)
            result["client_cdn"] = cdn_path

        if not server_path.is_file() or not client_path.is_file():
            raise EasyXrayError("config files are not generated")

        return result

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

    def _existing_usernames(self, server_config: dict[str, Any]) -> set[str]:
        usernames: set[str] = set()
        for client in server_config["inbounds"][1]["settings"]["clients"]:
            email = client.get("email", "")
            if "@" in email:
                usernames.add(email.split("@", 1)[0])
        return usernames

    def add(
        self,
        usernames: Sequence[str],
        *,
        resume: bool = False,
    ) -> list[str]:
        """Add users or resume suspended users."""
        self._require_conf_tools()
        self._server_config_path()
        self._client_config_path()

        if not usernames:
            raise EasyXrayError(
                "usernames not set\n"
                "For default user, use config_client.json generated "
                "by install command. Otherwise use non-void usernames, "
                "preferably of letters and digits only."
            )

        server_path = self.conf_dir / "config_server.json"
        self.cp_to_backup(server_path)
        updated: list[str] = []

        server_config = json.loads(server_path.read_text(encoding="utf-8"))
        existing = self._existing_usernames(server_config)

        for username in usernames:
            if username in existing:
                continue

            client_user_path = self.conf_dir / f"config_client_{username}.json"
            if resume:
                if not client_user_path.is_file():
                    raise EasyXrayError(
                        f"no {client_user_path} found, can't resume"
                    )
                client_user = json.loads(client_user_path.read_text(encoding="utf-8"))
                user_id = client_user["outbounds"][0]["settings"]["vnext"][0][
                    "users"
                ][0]["id"]
                short_id = client_user["outbounds"][0]["streamSettings"][
                    "realitySettings"
                ]["shortId"]
            else:
                user_id = self._xray_uuid()
                short_id = self._openssl_rand_hex(8)
                client_template = json.loads(
                    self._client_config_path().read_text(encoding="utf-8")
                )
                outbound = client_template["outbounds"][0]
                outbound["settings"]["vnext"][0]["users"][0]["id"] = user_id
                outbound["settings"]["vnext"][0]["users"][0]["email"] = (
                    f"{username}@example.com"
                )
                outbound["streamSettings"]["realitySettings"]["shortId"] = short_id
                self._write_json(client_user_path, client_template)

                cdn_template_path = self.conf_dir / "config_client_cdn.json"
                if cdn_template_path.is_file():
                    cdn_config = json.loads(
                        cdn_template_path.read_text(encoding="utf-8")
                    )
                    cdn_config["outbounds"][0]["settings"]["vnext"][0]["users"][0][
                        "id"
                    ] = user_id
                    cdn_user_path = self.conf_dir / f"config_client_{username}_cdn.json"
                    self._write_json(cdn_user_path, cdn_config)

            client_entry = {
                "id": user_id,
                "email": f"{username}@example.com",
                "flow": "xtls-rprx-vision",
            }
            grpc_client_entry = {"id": user_id}

            server_config = json.loads(server_path.read_text(encoding="utf-8"))
            server_config["inbounds"][1]["settings"]["clients"].append(client_entry)
            server_config["inbounds"][1]["streamSettings"]["realitySettings"][
                "shortIds"
            ].append(short_id)
            server_config["inbounds"][3]["settings"]["clients"].append(
                grpc_client_entry
            )
            self._write_json(server_path, server_config)
            existing.add(username)
            updated.append(username)

        return updated

    def remove_users(
        self,
        usernames: Sequence[str],
        *,
        mode: Literal["del", "suspend"] = "del",
    ) -> list[str]:
        """Delete or suspend users."""
        server_path = self.conf_dir / "config_server.json"
        if not server_path.is_file():
            raise EasyXrayError("server config not found")

        if not usernames:
            raise EasyXrayError("usernames not set")

        self.cp_to_backup(server_path)
        affected: list[str] = []

        for username in usernames:
            client_path = self.conf_dir / f"config_client_{username}.json"
            if not client_path.is_file():
                continue

            client_config = json.loads(client_path.read_text(encoding="utf-8"))
            short_id = client_config["outbounds"][0]["streamSettings"][
                "realitySettings"
            ]["shortId"]
            user_id = client_config["outbounds"][0]["settings"]["vnext"][0]["users"][
                0
            ]["id"]
            email = f"{username}@example.com"

            server_config = json.loads(server_path.read_text(encoding="utf-8"))
            clients = server_config["inbounds"][1]["settings"]["clients"]
            server_config["inbounds"][1]["settings"]["clients"] = [
                client for client in clients if client.get("email") != email
            ]
            short_ids = server_config["inbounds"][1]["streamSettings"][
                "realitySettings"
            ]["shortIds"]
            server_config["inbounds"][1]["streamSettings"]["realitySettings"][
                "shortIds"
            ] = [sid for sid in short_ids if sid != short_id]
            grpc_clients = server_config["inbounds"][3]["settings"]["clients"]
            server_config["inbounds"][3]["settings"]["clients"] = [
                client for client in grpc_clients if client.get("id") != user_id
            ]
            self._write_json(server_path, server_config)

            if mode == "del":
                client_path.unlink(missing_ok=True)
                cdn_path = self.conf_dir / f"config_client_{username}_cdn.json"
                cdn_path.unlink(missing_ok=True)

            affected.append(username)

        return affected

    def import_users(self, from_dir: str | Path, to_dir: str | Path) -> list[str]:
        """Import user configs from one directory into another."""
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
            server_config["inbounds"][1]["settings"]["clients"].append(
                {
                    "id": user_id,
                    "email": f"{username}@example.com",
                    "flow": "xtls-rprx-vision",
                }
            )
            server_config["inbounds"][1]["streamSettings"]["realitySettings"][
                "shortIds"
            ].append(short_id)
            server_config["inbounds"][3]["settings"]["clients"].append({"id": user_id})
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

        if network == "tcp":
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

        service_name = outbound["streamSettings"]["grpcSettings"]["serviceName"]
        return (
            f"vless://{user_id}@{address}:443"
            f"?security=tls&encryption=none&fp=chrome&type=grpc"
            f"&serviceName={service_name}#easy-xray+%F0%9F%97%BD+CDN"
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

    def push(
        self,
        config_name: str = "config_server.json",
        *,
        require_root: bool = True,
    ) -> None:
        """Copy config to xray's directory and restart xray."""
        if require_root and os.geteuid() != 0:
            raise EasyXrayError(
                "you should have root privileges for that, try\nsudo ./ex.sh push"
            )

        source = self.conf_dir / config_name
        if not source.is_file():
            raise EasyXrayError(f"config file not found: {source}")

        XRAY_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, XRAY_CONFIG_PATH)
        self._run(["systemctl", "restart", "xray"], check=False)
        self._run(
            ["journalctl", "-u", "xray"],
            capture_output=True,
            check=False,
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
            for client in server_config["inbounds"][1]["settings"]["clients"]:
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

    def install_xray(
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

        if shutil.which("xray") and not force_reinstall:
            raise EasyXrayError("xray detected; set force_reinstall=True to continue")

        self.check_command(
            "curl",
            "required to download the xray installation script",
        )
        install_script = self._run(
            ["curl", "-L", XRAY_INSTALL_URL],
            capture_output=True,
        ).stdout
        self._run(["bash", "-c", install_script, "@", "install"])

        XRAY_DAT_DIR.mkdir(parents=True, exist_ok=True)
        customgeo = self.root / "customgeo.dat"
        if not customgeo.is_file():
            raise EasyXrayError(f"customgeo.dat not copied to {XRAY_DAT_DIR}")
        shutil.copy2(customgeo, XRAY_DAT_DIR / customgeo.name)

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
