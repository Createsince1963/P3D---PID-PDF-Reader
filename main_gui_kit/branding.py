"""BrandingManager / HeaderBanner — logo + product name + version header.

Carried over into main_gui_kit unchanged (relative imports only). Default-name
resolution improvements are scheduled for A6 (kit hygiene)."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget


class BrandingManager:
    """Resolves the logo file to use, with a fallback cascade:
    project-specific asset -> shared kit default -> no logo (text only)."""

    def __init__(self, asset_dir: Optional[Path] = None):
        self.asset_dir = asset_dir

    def resolve_logo(self) -> Optional[Path]:
        if self.asset_dir:
            for name in ("logo.png", "logo_02.png", "logo.jpg"):
                candidate = self.asset_dir / name
                if candidate.exists():
                    return candidate
        return None


class HeaderBanner(QWidget):
    """Header bar: [logo] Product Name  v1.2.3"""

    def __init__(self, product_name: str, version: str,
                 branding: Optional[BrandingManager] = None, parent=None):
        super().__init__(parent)
        self.setObjectName("HeaderBanner")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)

        logo_path = branding.resolve_logo() if branding else None
        if logo_path:
            logo = QLabel()
            logo.setPixmap(QPixmap(str(logo_path)).scaledToHeight(32, Qt.SmoothTransformation))
            layout.addWidget(logo)

        title = QLabel(product_name)
        title.setStyleSheet("font-size: 14pt; font-weight: 600;")
        layout.addWidget(title)

        ver = QLabel(f"v{version}")
        ver.setStyleSheet("color: palette(mid);")
        layout.addWidget(ver)

        layout.addStretch(1)
