from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPoint, QRect, QSize, Qt
from PySide6.QtGui import QIcon, QImage, QPainter, QPixmap


BASE_FACE = QRect(8, 8, 8, 8)
HAT_LAYER = QRect(40, 8, 8, 8)


def minecraft_skin_face_pixmap(texture_path: Path | str, size: int = 32) -> QPixmap:
    image = QImage(str(texture_path))
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

    return QPixmap.fromImage(face).scaled(QSize(size, size), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation)


def minecraft_skin_face_icon(texture_path: Path | str, size: int = 32) -> QIcon:
    pixmap = minecraft_skin_face_pixmap(texture_path, size)
    return QIcon(pixmap) if not pixmap.isNull() else QIcon()
