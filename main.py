# quatumos_login.py
# pip install PyQt6

import sys
import os
import json
import ssl
import hashlib
import base64
import platform
import subprocess
import urllib.request
import urllib.error
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QFrame
)
from PyQt6.QtGui import QPixmap, QFont, QPainter, QColor, QKeySequence, QShortcut
from PyQt6.QtCore import Qt, QUrl, QTimer
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply


QR_URL = "https://github.com/a1g52d3x67/api-a3f9c8e2b7d5014f6e2a8b9c7d3e0f12/blob/main/QR.png?raw=true"

# ============================================
# CONFIGURACIÓN DE GITHUB
# ============================================
GITHUB_REPO_OWNER = "a1g52d3x67"
GITHUB_REPO_NAME = "api-a3f6c8e2b8d5014f6e2a8b9c7d3e0f12"
GITHUB_BRANCH = "main"
GITHUB_FILE_PATH = "db.json"
GITHUB_TOKEN = "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"


# ============================================
# API DE GITHUB
# ============================================
class GitHubAPI:
    def __init__(self, token, owner, repo, branch, file_path):
        self.token = token
        self.owner = owner
        self.repo = repo
        self.branch = branch
        self.file_path = file_path
        self.base_url = f"https://api.github.com/repos/{owner}/{repo}"
        self.headers = {
            'User-Agent': 'Quantum-App',
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

    def test_connection(self):
        try:
            url = f"{self.base_url}"
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=10, context=self.ssl_context) as response:
                if response.status == 200:
                    return True, "Conexión exitosa"
        except urllib.error.HTTPError as e:
            if e.code == 401:
                return False, "Token inválido o sin permisos"
            elif e.code == 403:
                return False, "Límite de rate limit excedido"
            elif e.code == 404:
                return False, "Repositorio no encontrado"
            else:
                return False, f"Error HTTP: {e.code}"
        except Exception as e:
            return False, f"Error de conexión: {e}"
        return False, "Error desconocido"

    def get_file_content(self):
        try:
            url = f"{self.base_url}/contents/{self.file_path}?ref={self.branch}"
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=15, context=self.ssl_context) as response:
                data = json.loads(response.read().decode('utf-8'))
                content_base64 = data.get('content', '')
                sha = data.get('sha', '')
                content_bytes = base64.b64decode(content_base64)
                content_str = content_bytes.decode('utf-8')
                content_dict = json.loads(content_str)
                return content_dict, sha
        except urllib.error.HTTPError as e:
            return None, None
        except json.JSONDecodeError:
            return None, None
        except Exception as e:
            return None, None

    def update_file_content(self, new_content_dict, sha, commit_message=None):
        if not commit_message:
            commit_message = f"Actualización de HWID - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        try:
            json_str = json.dumps(new_content_dict, indent=2, ensure_ascii=False)
            content_base64 = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
            payload = {
                "message": commit_message,
                "content": content_base64,
                "sha": sha,
                "branch": self.branch
            }
            url = f"{self.base_url}/contents/{self.file_path}"
            data = json.dumps(payload).encode('utf-8')
            headers = self.headers.copy()
            headers['Content-Type'] = 'application/json'
            req = urllib.request.Request(url, data=data, method='PUT', headers=headers)
            with urllib.request.urlopen(req, timeout=20, context=self.ssl_context) as response:
                if response.status in (200, 201):
                    return True
                return False
        except Exception as e:
            return False


# ============================================
# FUNCIONES AUXILIARES
# ============================================
def get_hwid():
    """Obtiene un identificador único de hardware (HWID)."""
    try:
        if os.name == 'nt':
            raw = None
            try:
                ps_cmd = (
                    "(Get-CimInstance Win32_ComputerSystemProduct).UUID + '-' + "
                    "(Get-CimInstance Win32_BIOS).SerialNumber"
                )
                result = subprocess.run(
                    ['powershell', '-NoProfile', '-Command', ps_cmd],
                    capture_output=True, text=True, timeout=10
                )
                out = result.stdout.strip()
                if out and out not in ('-', '', 'Win32_ComputerSystemProduct-Win32_BIOS'):
                    raw = out
            except Exception:
                pass

            if not raw:
                try:
                    import winreg
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography")
                    raw, _ = winreg.QueryValueEx(key, "MachineGuid")
                except Exception:
                    raw = None

            if not raw:
                raise RuntimeError("No se pudo obtener ningún identificador válido")
        else:
            if os.path.exists('/etc/machine-id'):
                with open('/etc/machine-id', 'r') as f:
                    machine_id = f.read().strip()
            else:
                machine_id = platform.node()

            if os.path.exists('/sys/class/dmi/id/product_uuid'):
                with open('/sys/class/dmi/id/product_uuid', 'r') as f:
                    system_uuid = f.read().strip()
            else:
                system_uuid = platform.node()

            raw = f"{machine_id}-{system_uuid}"

        return hashlib.md5(raw.encode()).hexdigest()
    except Exception:
        fallback = f"{platform.node()}-{platform.processor()}-{platform.machine()}"
        return hashlib.md5(fallback.encode()).hexdigest()


def find_user_in_data(db_data, username):
    """Busca un usuario en la estructura de datos."""
    if not db_data:
        return None, None

    if isinstance(db_data, list):
        for idx, entry in enumerate(db_data):
            if isinstance(entry, dict) and entry.get("Username") == username:
                return entry, idx
    elif isinstance(db_data, dict):
        users = db_data.get("users", None)
        if isinstance(users, list):
            for idx, entry in enumerate(users):
                if isinstance(entry, dict) and entry.get("Username") == username:
                    return entry, idx
        elif isinstance(users, dict):
            for key, value in users.items():
                if isinstance(value, dict):
                    if value.get("Username") == username or key == username:
                        return value, key
        else:
            for key, value in db_data.items():
                if isinstance(value, dict):
                    if value.get("Username") == username or key == username:
                        return value, key
    return None, None


def update_hwid_in_data(db_data, username, hwid):
    """Actualiza el HWID del usuario en la estructura de datos."""
    encontrado = False
    if isinstance(db_data, list):
        for entry in db_data:
            if isinstance(entry, dict) and entry.get("Username") == username:
                entry["HWID"] = hwid
                encontrado = True
                break
    elif isinstance(db_data, dict):
        users = db_data.get("users", None)
        if isinstance(users, list):
            for entry in users:
                if isinstance(entry, dict) and entry.get("Username") == username:
                    entry["HWID"] = hwid
                    encontrado = True
                    break
        elif isinstance(users, dict):
            for key, value in users.items():
                if isinstance(value, dict):
                    if value.get("Username") == username or key == username:
                        value["HWID"] = hwid
                        encontrado = True
                        break
        else:
            for key, value in db_data.items():
                if isinstance(value, dict):
                    if value.get("Username") == username or key == username:
                        value["HWID"] = hwid
                        encontrado = True
                        break
    return db_data, encontrado


# ============================================
# VENTANA DE LOGIN
# ============================================
class QuatumOSLogin(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QuatumOS — Iniciar Sesión")
        self.resize(1920, 1080)
        self.setMinimumSize(1100, 700)

        self.bg_pixmap = QPixmap("background.jpg")

        self.network = QNetworkAccessManager(self)
        self.qr_container = None

        # API de GitHub
        self.github = GitHubAPI(GITHUB_TOKEN, GITHUB_REPO_OWNER,
                                GITHUB_REPO_NAME, GITHUB_BRANCH, GITHUB_FILE_PATH)

        self._build_logo()
        self._build_card()
        self._load_qr_from_url()
        self._setup_shortcuts()

    # ---------------------------------------------------------------
    def _setup_shortcuts(self):
        """Atajos: F11 alterna pantalla completa, Esc sale de pantalla completa o cierra."""
        QShortcut(QKeySequence("F11"), self, activated=self._toggle_fullscreen)
        QShortcut(QKeySequence("Esc"), self, activated=self._on_escape)

    def _toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def _on_escape(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.close()

    # ---------------------------------------------------------------
    def paintEvent(self, event):
        painter = QPainter(self)
        if not self.bg_pixmap.isNull():
            scaled = self.bg_pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            x = (scaled.width() - self.width()) // 2
            y = (scaled.height() - self.height()) // 2
            painter.drawPixmap(-x, -y, scaled)
        else:
            painter.fillRect(self.rect(), QColor("#0d0d10"))
        painter.end()

    # ---------------------------------------------------------------
    def _build_logo(self):
        ICON_SIZE = 44
        logo = QLabel(self)
        pix = QPixmap("icon.jpg")
        if pix.isNull():
            pix = QPixmap(ICON_SIZE, ICON_SIZE)
            pix.fill(QColor("#4B4B51"))
        logo.setPixmap(pix.scaled(
            ICON_SIZE, ICON_SIZE,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        ))
        logo.setGeometry(40, 38, ICON_SIZE, ICON_SIZE)
        logo.setStyleSheet("background: transparent;")

        txt = QLabel("QuatumOS", self)
        txt.setFont(QFont("Inter", 16, QFont.Weight.DemiBold))
        txt.setStyleSheet("color: #FFFFFF; background: transparent;")
        txt.setGeometry(40 + ICON_SIZE + 14, 46, 240, 32)

    # ---------------------------------------------------------------
    def _build_card(self):
        self.card = QFrame(self)
        self.card.setObjectName("card")
        self.card.setStyleSheet("""
            QFrame#card {
                background-color: rgba(28, 28, 33, 0.95);
                border-radius: 24px;
            }
        """)
        self.card.setFixedSize(850, 480)

        card_layout = QHBoxLayout(self.card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        # ---------- Columna izquierda ----------
        left = QWidget()
        left.setStyleSheet("background: transparent;")
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(60, 60, 60, 60)
        left_layout.setSpacing(0)
        left_layout.addStretch()

        lbl_user = QLabel("Username")
        lbl_user.setStyleSheet("color: #D1D1D6; font-size: 14px; background: transparent;")
        left_layout.addWidget(lbl_user)
        left_layout.addSpacing(8)

        self.input_user = QLineEdit()
        self.input_user.setFixedHeight(45)
        self.input_user.setStyleSheet(self._input_qss())
        left_layout.addWidget(self.input_user)
        left_layout.addSpacing(20)

        lbl_pass = QLabel("Contraseña")
        lbl_pass.setStyleSheet("color: #D1D1D6; font-size: 14px; background: transparent;")
        left_layout.addWidget(lbl_pass)
        left_layout.addSpacing(8)

        self.input_pass = QLineEdit()
        self.input_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_pass.setFixedHeight(45)
        self.input_pass.setStyleSheet(self._input_qss())
        left_layout.addWidget(self.input_pass)
        left_layout.addSpacing(30)

        self.btn_login = QPushButton("Iniciar Sesion")
        self.btn_login.setFixedHeight(45)
        self.btn_login.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_login.setStyleSheet("""
            QPushButton {
                background-color: #4B4B51;
                color: #FFFFFF;
                font-size: 15px;
                font-weight: bold;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #5A5A61; }
            QPushButton:pressed { background-color: #3F3F46; }
        """)
        self.btn_login.clicked.connect(self._on_login)
        left_layout.addWidget(self.btn_login)
        left_layout.addSpacing(10)

        # Label de estado (mensajes de error/éxito)
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #FF6B6B; font-size: 12px; background: transparent;")
        left_layout.addWidget(self.status_label)

        left_layout.addStretch()

        # ---------- Columna derecha ----------
        right = QWidget()
        right.setStyleSheet("background: transparent;")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(40, 60, 60, 60)
        right_layout.setSpacing(0)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addStretch()

        self.qr_container = QLabel()
        self.qr_container.setFixedSize(200, 200)
        self.qr_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.qr_container.setStyleSheet("""
            background-color: #FFFFFF;
            border-radius: 8px;
        """)

        placeholder = self._generate_placeholder_qr(180)
        self.qr_container.setPixmap(placeholder.scaled(
            180, 180,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        ))

        self._build_qr_logo_overlay(self.qr_container)

        right_layout.addWidget(self.qr_container, alignment=Qt.AlignmentFlag.AlignHCenter)
        right_layout.addSpacing(20)

        title = QLabel("Comprar / Crear cuenta")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #FFFFFF; font-size: 18px; font-weight: bold; background: transparent;")
        right_layout.addWidget(title)
        right_layout.addSpacing(8)

        subtitle = QLabel("Comprar licencia\no crear cuenta")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #A1A1A6; font-size: 13px; background: transparent;")
        right_layout.addWidget(subtitle)

        right_layout.addStretch()

        card_layout.addWidget(left, 55)
        card_layout.addWidget(right, 45)

    # ---------------------------------------------------------------
    def _on_login(self):
        """Valida usuario, contraseña y HWID contra GitHub. Sin límite de intentos."""
        username = self.input_user.text().strip()
        password = self.input_pass.text().strip()

        # Validación de campos vacíos
        if not username or not password:
            self._set_status("Credenciales no correctas", error=True)
            return

        self._set_status("Validando credenciales...", error=False)
        self.btn_login.setEnabled(False)
        QApplication.processEvents()

        # 1) Obtener datos frescos de GitHub
        db_data, sha = self.github.get_file_content()
        if db_data is None:
            self._set_status("Error: No se pudo conectar con la base de datos", error=True)
            self.btn_login.setEnabled(True)
            return

        current_hwid = get_hwid()
        user, _ = find_user_in_data(db_data, username)

        # 2) Usuario no encontrado
        if not user:
            self._set_status("Credenciales no correctas", error=True)
            self.btn_login.setEnabled(True)
            return

        # 3) Contraseña incorrecta
        if user.get("Password") != password:
            self._set_status("Credenciales no correctas", error=True)
            self.btn_login.setEnabled(True)
            return

        # 4) Sin licencia
        license_key = user.get("License", "")
        if not license_key:
            self._set_status("Esta cuenta no tiene una Key asignada", error=True)
            self.btn_login.setEnabled(True)
            return

        existing_hwid = user.get("HWID", "")

        # 5) Ya registrada en otro PC
        if existing_hwid:
            if existing_hwid == current_hwid:
                self._set_status("Acceso concedido. Cerrando...", error=False)
                QApplication.processEvents()
                QTimer.singleShot(800, QApplication.quit)
                return
            else:
                self._set_status("Esta cuenta ya está registrada en otro PC", error=True)
                self.btn_login.setEnabled(True)
                return

        # 6) Primer login: registrar HWID
        self._set_status("Primer login detectado. Registrando HWID...", error=False)
        QApplication.processEvents()

        updated_data, encontrado = update_hwid_in_data(db_data, username, current_hwid)
        if not encontrado:
            self._set_status("Error: No se pudo registrar el HWID", error=True)
            self.btn_login.setEnabled(True)
            return

        success = self.github.update_file_content(updated_data, sha)
        if success:
            self._set_status("HWID registrado. Acceso concedido. Cerrando...", error=False)
            QApplication.processEvents()
            QTimer.singleShot(800, QApplication.quit)
            return
        else:
            self._set_status("Error: No se pudo registrar el HWID", error=True)
            self.btn_login.setEnabled(True)
            return

    def _set_status(self, message, error=True):
        """Muestra un mensaje en el label de estado."""
        color = "#FF6B6B" if error else "#6BFF8F"
        self.status_label.setStyleSheet(
            f"color: {color}; font-size: 12px; background: transparent;"
        )
        self.status_label.setText(message)

    # ---------------------------------------------------------------
    def _load_qr_from_url(self):
        url = QUrl(QR_URL)
        request = QNetworkRequest(url)
        request.setAttribute(
            QNetworkRequest.Attribute.RedirectPolicyAttribute,
            QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy
        )
        request.setRawHeader(b"User-Agent", b"QuatumOS-Client/1.0")
        reply = self.network.get(request)
        reply.finished.connect(lambda: self._on_qr_downloaded(reply))

    def _on_qr_downloaded(self, reply: QNetworkReply):
        if reply.error() == QNetworkReply.NetworkError.NoError:
            data = reply.readAll()
            pix = QPixmap()
            if pix.loadFromData(data):
                self.qr_container.setPixmap(pix.scaled(
                    180, 180,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                ))
                for child in self.qr_container.children():
                    if isinstance(child, QLabel):
                        child.raise_()
        reply.deleteLater()

    # ---------------------------------------------------------------
    def _input_qss(self):
        return """
            QLineEdit {
                background-color: #28282E;
                border: 1px solid #3A3A40;
                border-radius: 8px;
                padding: 0 12px;
                color: #FFFFFF;
                font-size: 14px;
            }
            QLineEdit:focus { border: 1px solid #5A5A61; }
        """

    # ---------------------------------------------------------------
    def _build_qr_logo_overlay(self, parent: QLabel):
        overlay = QLabel(parent)
        overlay.setFixedSize(44, 44)
        overlay.setStyleSheet("""
            background-color: #000000;
            border-radius: 22px;
        """)
        overlay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        inner = QLabel(overlay)
        pix = QPixmap("icon.jpg")
        if pix.isNull():
            pix = QPixmap(24, 24)
            pix.fill(QColor("#4B4B51"))
        inner.setPixmap(pix.scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio,
                                   Qt.TransformationMode.SmoothTransformation))
        inner.setGeometry(10, 10, 24, 24)

        overlay.move(
            parent.width() // 2 - overlay.width() // 2,
            parent.height() // 2 - overlay.height() // 2
        )
        overlay.raise_()

    # ---------------------------------------------------------------
    @staticmethod
    def _generate_placeholder_qr(size: int) -> QPixmap:
        import random
        random.seed(42)
        pix = QPixmap(size, size)
        pix.fill(QColor("#FFFFFF"))
        painter = QPainter(pix)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#000000"))
        cell = size // 21
        for y in range(21):
            for x in range(21):
                if 8 <= x <= 12 and 8 <= y <= 12:
                    continue
                if random.random() < 0.45:
                    painter.drawRect(x * cell, y * cell, cell, cell)
        painter.end()
        return pix

    # ---------------------------------------------------------------
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.card.move(
            (self.width() - self.card.width()) // 2,
            (self.height() - self.card.height()) // 2
        )
        self.update()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Inter", 10))
    w = QuatumOSLogin()
    w.showFullScreen()   # <-- Full Screen
    sys.exit(app.exec())