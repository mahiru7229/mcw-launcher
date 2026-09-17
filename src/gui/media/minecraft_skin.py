from __future__ import annotations

import base64
from pathlib import Path

from PySide6.QtCore import QPoint, QRect, QSize, Qt
from PySide6.QtGui import QIcon, QImage, QPainter, QPixmap

from mcw_core.api.account.account_skin_manager import AccountSkinManager

BASE_FACE = QRect(8, 8, 8, 8)
HAT_LAYER = QRect(40, 8, 8, 8)

STEVE_SKIN_B64 = "iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAESUlEQVR4Xu2avW4TQRSF/RwmKBJFoihNukBBItLwJwEVlFTwMJF4g3QWHSlooIECiRcAIUUCiUeggMaIYvBd6VrH597ZnZ/1KrF9pU/rvXNnds7Z9drr8SiEMGrj4bWj8OT6SdAtvpat8Gz7nmnX3Awz5mXCJJgcA2S7sgZ4oAGyr1t9vRIGoDDZxsTG2tfGgOnXDwusjAEpbwEWr0gbj3fZMAlGDUAjMLcWBih85pW/M7EefRrAx+T2UpqB9Y4dE5gK9odPAXd8zfGEYmj/3H5dGAPwNQuMgW8L7R8zgNt5Qh5o2vMbj+djcV0JcwP07OhrFNBFV/+2dp4Qgv11qwbg+Nwvh86POTnA+NpWw7+fnxt0X9q09tHWHbd/1/g8IcQzwGvnfjm4BqgYyYlQiVfffs8NkNcS0jaUAQ/Gt01tLwboAXCyIubp9l28xFwDtF1qpQ8aJ1sU4JnRNXkcn9uwnfM5uDdBNuDPxceG6Y9PDbrPBqAwNgDHxxxPiGmraWtLxRggiBidvPDry/uG76/fNeg+1mB/HNMbH3M8oaERAxpmE2oSp6enAZlMJgvwAAybwiSEGZOYB37rlDYMp5/LlTYAv3VKW5EBnMg1gA+KYvGZYGPAZTWABStnZ2cNXXkMvtzxoYgZIIxYj9HBwUFgWHQMqcVQcXqnn06nDZgbSLyEEevhGqDs7e25YA2GCpSPOA78WBwojFiPVgP29/ddagwYMIxYj8EMkFh5AyRiBpSK1/tILsER69FqAL/3u+4BEjEDSoN/ZkslOGI9Wg3gM596BfQZLCyV4Ij1GMkZVWF8plm4V8fRtwH8S3MqwRHrMbp1eBhq4Fh7AyT6NIEv7VSCI9Zj9Pb8Tahh2cHCUgmOWA+TGI/HAeH2LiSk38KTCeR4fIbHWzYmIZPY2dlpKJkQisVAA3Z3d11KjleLSdQaoGPEchsDxvayR7jfsnEnhAZ0wQMKXt7LScTavNwyMGc8d58HFLy8l9sYsMoGeHAdGuDB9cug2oAYWpNS21bPE+6bXgyI7QsXx/fDi/OXbjvvM4MZUEtMkIi/OXteWEsDRLgYcOmvAC9Ojo+CwHkvYoJEtOK1e/vMIAaoWERXgfjRV8HaXEG59TzhvjEJYSZ+DrcxKgJhISyY4borb4AnittT4eP1jUnUToCXz9oWVyW4vxRolPzElYtJiOiaSzDHgAjzKPmFJxeT2Biwbgbwe54N6IIF8/8HYmhdRRgxJZgznrvPwhBeaVKwpiKMmBKqDeDVJF47bMNbWcoII6aEagN42YzXDtuQ2oowYkrYGMCCcvdZfK4BvK6fCgspxf0UyIHf/7n3AF7SSoWFlFJtAJ/93CuAhaXCQkrRZ/oF4FHXtDF89kUUXw1qjFfLy9qpsJBS3OVx/dbGvxMw3K8EFpYKCynFhCQniY/DEiwoF760U+G5lGJCkjkG8P8FcmFhqfBcSvkPFyV1FbZn31EAAAAASUVORK5CYII="

ALEX_SKIN_B64 = "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"


def _render_face(image: QImage, size: int) -> QPixmap:
    if image.isNull() or image.width() < 48 or image.height() < 16:
        return QPixmap()

    face = QImage(8, 8, QImage.Format.Format_ARGB32)
    face.fill(Qt.GlobalColor.transparent)
    painter = QPainter(face)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
    painter.drawImage(QPoint(0, 0), image, BASE_FACE)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
    painter.drawImage(QPoint(0, 0), image, HAT_LAYER)
    painter.end()

    return QPixmap.fromImage(face).scaled(
        QSize(size, size),
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.FastTransformation,
    )


def minecraft_skin_face_pixmap(texture_path: Path | str, size: int = 32) -> QPixmap:
    image = QImage(str(texture_path))
    return _render_face(image, size)


def default_skin_face_pixmap(variant: str = "classic", size: int = 32) -> QPixmap:
    b64 = ALEX_SKIN_B64 if str(variant).lower() in ("alex", "slim") else STEVE_SKIN_B64
    try:
        data = base64.b64decode(b64)
        image = QImage.fromData(data, "PNG")
        return _render_face(image, size)
    except Exception:
        return QPixmap()


def default_skin_face_icon(variant: str = "classic", size: int = 32) -> QIcon:
    pixmap = default_skin_face_pixmap(variant, size)
    return QIcon(pixmap) if not pixmap.isNull() else QIcon()


def minecraft_skin_face_icon(texture_path: Path | str, size: int = 32) -> QIcon:
    pixmap = minecraft_skin_face_pixmap(texture_path, size)
    return QIcon(pixmap) if not pixmap.isNull() else QIcon()


def account_skin_face_icon(account: object | None, size: int = 32) -> QIcon:
    if account is None:
        return default_skin_face_icon("classic", size)

    texture_path = AccountSkinManager.cached_texture(account)
    if texture_path is not None:
        icon = minecraft_skin_face_icon(texture_path, size)
        if not icon.isNull():
            return icon

    variant = str(getattr(account, "skin_variant", "classic") or "classic")
    return default_skin_face_icon(variant, size)
