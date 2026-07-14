class JavaMajorPolicy:
    SUPPORTED_MAJORS = (8, 17, 25)

    @staticmethod
    def resolve(required_major: int | None) -> int:
        if required_major is None or required_major <= 8:
            return 8
        if required_major <= 17:
            return 17
        if required_major <= 25:
            return 25
        raise RuntimeError(f"Java {required_major} is not supported. Supported managed runtimes: 8, 17, 25.")
