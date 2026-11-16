from __future__ import annotations

import json
from pathlib import Path
import re
import struct
import zipfile


class JavaMajorPolicy:
    SUPPORTED_MAJORS = (8, 17, 21, 25)
    _MOD_JAR_JAVA_CACHE: dict[tuple[str, int, int], int] = {}

    @classmethod
    def required_for_minecraft(cls, game_version: str, metadata_major: object = None) -> int:
        """Return the Java major required by a Minecraft version.

        Mojang's ``javaVersion`` metadata remains authoritative.  The release
        mapping is deliberately only a fallback for older/cached/custom
        profiles that do not carry that field; this is especially important
        while a Forge-family installer is preparing its launch profile.
        """
        if metadata_major not in (None, ""):
            try:
                required = int(metadata_major)
            except (TypeError, ValueError) as error:
                raise RuntimeError(f"Invalid Minecraft Java major version: {metadata_major!r}.") from error
            if required < 1:
                raise RuntimeError(f"Invalid Minecraft Java major version: {metadata_major!r}.")
            return required

        match = re.fullmatch(r"1\.(\d+)(?:\.(\d+))?", str(game_version or "").strip())
        if match is None:
            return 8
        minor = int(match.group(1))
        patch = int(match.group(2) or 0)
        if minor <= 16:
            return 8
        if minor == 17:
            return 16
        if minor < 20 or (minor == 20 and patch <= 4):
            return 17
        return 21

    @classmethod
    def resolve(cls, required_major: int | None) -> int:
        try:
            required = int(required_major or 8)
        except (TypeError, ValueError) as error:
            raise RuntimeError(f"Invalid Java major version: {required_major!r}.") from error

        for managed_major in cls.SUPPORTED_MAJORS:
            if required <= managed_major:
                return managed_major
        supported = ", ".join(str(major) for major in cls.SUPPORTED_MAJORS)
        raise RuntimeError(f"Java {required} is not supported. Supported managed runtimes: {supported}.")

    @classmethod
    def accepted_majors(cls, required_major: int | None, *, allow_higher: bool = False) -> tuple[int, ...]:
        required = int(required_major or 8)
        managed = cls.resolve(required)
        base = (required,) if required == managed else (required, managed)
        if not allow_higher:
            return base
        higher = tuple(major for major in cls.SUPPORTED_MAJORS if major >= required)
        return tuple(dict.fromkeys((*base, *higher)))

    @classmethod
    def required_for_instance(cls, instance: object, metadata_major: object = None) -> int:
        game_version = str(getattr(instance, "version_id", "") or "").strip()
        base_required = cls.required_for_minecraft(game_version, metadata_major)
        mod_loader = getattr(instance, "mod_loader", ("vanilla", "-1")) or ("vanilla", "-1")
        loader_name = str(mod_loader[0] if isinstance(mod_loader, (list, tuple)) and mod_loader else mod_loader).strip().casefold()
        if loader_name not in {"fabric", "quilt"}:
            return base_required

        instance_dir = getattr(instance, "instance_dir", None)
        if not instance_dir:
            return base_required
        mods_dir = Path(instance_dir) / "mods"
        if not mods_dir.is_dir():
            return base_required

        detected_max = base_required
        max_supported = max(cls.SUPPORTED_MAJORS)
        try:
            entries = sorted(mods_dir.iterdir(), key=lambda item: item.name.casefold())
        except OSError:
            return base_required

        for entry in entries:
            if not entry.is_file() or entry.suffix.casefold() != ".jar":
                continue
            mod_major = cls._detect_jar_required_java(entry)
            if mod_major > detected_max:
                detected_max = min(mod_major, max_supported)
        return detected_max

    @classmethod
    def _detect_jar_required_java(cls, jar_path: Path) -> int:
        try:
            stat = jar_path.stat()
            cache_key = (str(jar_path.resolve(strict=False)), int(stat.st_mtime_ns), int(stat.st_size))
        except OSError:
            return 8

        cached = cls._MOD_JAR_JAVA_CACHE.get(cache_key)
        if cached is not None:
            return cached

        detected = 8
        try:
            with zipfile.ZipFile(jar_path, "r") as archive:
                names = archive.namelist()
                name_set = set(names)
                if "fabric.mod.json" in name_set:
                    detected = max(detected, cls._parse_fabric_java_depends(archive.read("fabric.mod.json")))
                if "quilt.mod.json" in name_set:
                    detected = max(detected, cls._parse_quilt_java_depends(archive.read("quilt.mod.json")))

                inspected = 0
                for name in names:
                    if not name.endswith(".class"):
                        continue
                    lower_name = name.casefold()
                    if lower_name == "module-info.class" or lower_name.startswith("meta-inf/versions/"):
                        continue
                    with archive.open(name, "r") as class_stream:
                        header = class_stream.read(8)
                    if len(header) == 8:
                        magic, _minor, major = struct.unpack(">IHH", header)
                        if magic == 0xCAFEBABE and major >= 52:
                            detected = max(detected, int(major) - 44)
                    inspected += 1
                    if inspected >= 12:
                        break
        except (OSError, zipfile.BadZipFile, KeyError, ValueError, struct.error):
            pass

        if len(cls._MOD_JAR_JAVA_CACHE) > 2048:
            cls._MOD_JAR_JAVA_CACHE.clear()
        cls._MOD_JAR_JAVA_CACHE[cache_key] = detected
        return detected

    @staticmethod
    def _parse_fabric_java_depends(raw_bytes: bytes) -> int:
        try:
            payload = json.loads(raw_bytes.decode("utf-8", errors="replace"))
        except ValueError:
            return 8
        if not isinstance(payload, dict):
            return 8
        depends = payload.get("depends")
        if not isinstance(depends, dict):
            return 8
        java_spec = depends.get("java")
        return JavaMajorPolicy._extract_java_spec_major(java_spec)

    @staticmethod
    def _parse_quilt_java_depends(raw_bytes: bytes) -> int:
        try:
            payload = json.loads(raw_bytes.decode("utf-8", errors="replace"))
        except ValueError:
            return 8
        if not isinstance(payload, dict):
            return 8
        loader = payload.get("quilt_loader")
        if not isinstance(loader, dict):
            return 8
        depends = loader.get("depends")
        if not isinstance(depends, list):
            return 8
        best = 8
        for item in depends:
            if isinstance(item, dict) and str(item.get("id") or "") == "java":
                best = max(best, JavaMajorPolicy._extract_java_spec_major(item.get("versions")))
        return best

    @staticmethod
    def _extract_java_spec_major(spec: object) -> int:
        if isinstance(spec, int):
            return max(8, spec)
        if isinstance(spec, list):
            values = [JavaMajorPolicy._extract_java_spec_major(item) for item in spec]
            return min(values) if values else 8
        text = str(spec or "").strip()
        if not text:
            return 8
        matches = [int(value) for value in re.findall(r"(?:>=|>|=|~|\^)?\s*(?:1\.)?(\d+)", text) if int(value) >= 8]
        return max(matches) if matches else 8
