import base64
import win32crypt


class TokenCipher:

    @staticmethod
    def encrypt(value: str) -> str:
        if not value:
            return ""

        try:
            encrypted_data = win32crypt.CryptProtectData(
                value.encode("utf-8"),
                "Zen Launcher Token",
                None,
                None,
                None,
                0
            )

            return base64.b64encode(encrypted_data).decode("utf-8")

        except Exception as e:
            raise RuntimeError("Failed to encrypt token.") from e

    @staticmethod
    def decrypt(value: str) -> str:
        if not value:
            return ""

        try:
            encrypted_data = base64.b64decode(value)

            _, decrypted_data = win32crypt.CryptUnprotectData(
                encrypted_data,
                None,
                None,
                None,
                0
            )

            return decrypted_data.decode("utf-8")

        except Exception as e:
            raise RuntimeError("Failed to decrypt token.") from e