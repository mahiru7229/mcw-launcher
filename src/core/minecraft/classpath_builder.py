from src.models.minecraft.version import Version
from pathlib import Path







class ClasspathBuilder:

    @staticmethod
    def build(version: Version, client_path: Path, libraries_dir: Path) -> str:
        classpath: list[str] = []
        for library in version.libraries:

            downloads = library.get("downloads")
            if downloads is None:
                continue

            artifact = downloads.get("artifact")
            if artifact is None:
                continue

            library_path = libraries_dir / Path(artifact["path"])
            classpath.append(str(library_path))
        classpath.append(str(client_path))
        print(classpath)