import os
import json
import ssl
import hashlib
import base64
import platform
import subprocess
import urllib.request
import urllib.error
import getpass
import time
import sys
import ctypes
from datetime import datetime

# ============================================
# CONFIGURACIÓN
# ============================================

# Configuración del repositorio para la API de GitHub
GITHUB_REPO_OWNER = "a1g52d3x67"
GITHUB_REPO_NAME = "api-a3f6c8e2b8d5014f6e2a8b9c7d3e0f12"
GITHUB_BRANCH = "main"
GITHUB_FILE_PATH = "db.json"

# ⚠️ IMPORTANTE: Coloca aquí tu Personal Access Token (PAT) de GitHub
GITHUB_TOKEN = "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"

# ============================================
# COLORES Y ESTILOS PARA LA TERMINAL
# ============================================

class Colors:
    """Colores ANSI para la terminal."""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    
    # Colores de texto
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Colores brillantes
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    
    # Colores de fondo
    BG_RED = '\033[41m'
    BG_BRIGHT_RED = '\033[101m'

# ============================================
# FUNCIONES DE INTERFAZ
# ============================================

def enable_windows_ansi():
    """Habilita el soporte ANSI en Windows."""
    if os.name == 'nt':
        try:
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except:
            pass

def clear_screen():
    """Limpia la pantalla según el sistema operativo."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    """Imprime el banner principal de Quantum."""
    banner = f"""
{Colors.BRIGHT_RED}{Colors.BOLD}
               █████   █    ██  ▄▄▄       ███▄    █ ▄▄▄█████▓ █    ██  ███▄ ▄███▓
             ▒██▓  ██▒ ██  ▓██▒▒████▄     ██ ▀█   █ ▓  ██▒ ▓▒ ██  ▓██▒▓██▒▀█▀ ██▒
             ▒██▒  ██░▓██  ▒██░▒██  ▀█▄  ▓██  ▀█ ██▒▒ ▓██░ ▒░▓██  ▒██░▓██    ▓██░
             ░██  █▀ ░▓▓█  ░██░░██▄▄▄▄██ ▓██▒  ▐▌██▒░ ▓██▓ ░ ▓▓█  ░██░▒██    ▒██ 
             ░▒███▒█▄ ▒▒█████▓  ▓█   ▓██▒▒██░   ▓██░  ▒██▒ ░ ▒▒█████▓ ▒██▒   ░██▒
             ░░ ▒▒░ ▒ ░▒▓▒ ▒ ▒  ▒▒   ▓▒█░░ ▒░   ▒ ▒   ▒ ░░   ░▒▓▒ ▒ ▒ ░ ▒░   ░  ░
              ░ ▒░  ░ ░░▒░ ░ ░   ▒   ▒▒ ░░ ░░   ░ ▒░    ░    ░░▒░ ░ ░ ░  ░      ░
                ░   ░  ░░░ ░ ░   ░   ▒      ░   ░ ░   ░       ░░░ ░ ░ ░      ░   
                 ░       ░           ░  ░         ░             ░            ░   
{Colors.RESET}
"""
    print(banner)

def print_loading_animation(message, duration=2):
    """Muestra una animación de carga."""
    frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    end_time = time.time() + duration
    
    print(f"\n{Colors.BRIGHT_RED}{Colors.BOLD}{message} ", end='', flush=True)
    
    while time.time() < end_time:
        for frame in frames:
            if time.time() >= end_time:
                break
            print(f"\r{Colors.BRIGHT_RED}{Colors.BOLD}{message} {frame} ", end='', flush=True)
            time.sleep(0.1)
    
    print(f"\r{Colors.BRIGHT_RED}{Colors.BOLD}✓ {message} completado{Colors.RESET}" + " " * 20)

def print_success(message):
    """Imprime mensaje de éxito."""
    print(f"{Colors.BRIGHT_RED}{Colors.BOLD}✓ {message}{Colors.RESET}")

def print_error(message):
    """Imprime mensaje de error."""
    print(f"{Colors.BRIGHT_RED}{Colors.BOLD}✗ {message}{Colors.RESET}")

def print_info(message):
    """Imprime mensaje de información."""
    print(f"{Colors.BRIGHT_RED}{Colors.BOLD}ℹ {message}{Colors.RESET}")

# ============================================
# FUNCIONES DE API DE GITHUB
# ============================================

class GitHubAPI:
    """Maneja todas las operaciones con la API de GitHub."""
    
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
        """Prueba la conexión y valida el token."""
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
        """
        Obtiene el contenido del archivo directamente desde la API de GitHub.
        SIEMPRE hace una petición fresca - SIN CACHÉ.
        """
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
            if e.code == 401:
                print_error("Token inválido o sin permisos")
            elif e.code == 404:
                print_error("db.json no existe en el repositorio")
            elif e.code == 403:
                print_error("Rate limit excedido o permisos insuficientes")
            else:
                print_error(f"Error de la API: {e.code}")
            return None, None
        except json.JSONDecodeError:
            print_error("db.json no tiene formato JSON válido")
            return None, None
        except Exception as e:
            print_error(f"Error al obtener el archivo: {e}")
            return None, None
    
    def update_file_content(self, new_content_dict, sha, commit_message=None):
        """Actualiza el archivo en GitHub usando la API."""
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
                result = json.loads(response.read().decode('utf-8'))
                if response.status in (200, 201):
                    return True
                else:
                    print_error(f"Respuesta inesperada: {response.status}")
                    return False
                    
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            print_error(f"No se pudo actualizar (HTTP {e.code})")
            try:
                error_json = json.loads(error_body)
                if 'message' in error_json:
                    print(f"{Colors.BRIGHT_RED}[DETALLE] {error_json['message']}{Colors.RESET}")
            except:
                print(f"{Colors.BRIGHT_RED}[DETALLE] {error_body[:200]}{Colors.RESET}")
            return False
        except Exception as e:
            print_error(f"Error al actualizar: {e}")
            return False

# ============================================
# FUNCIONES AUXILIARES
# ============================================

def get_hwid():
    """Obtiene un identificador único de hardware (HWID), robusto y sin depender de wmic."""
    try:
        if os.name == 'nt':
            raw = None
            # 1) Intentar con PowerShell (funciona en Win10 y Win11, wmic o no)
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

            # 2) Fallback: MachineGuid del registro (siempre existe y es único por instalación de Windows)
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
            # (tu código actual de Linux/Mac está bien)
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
        # Fallback final: sigue siendo mejor que nada, pero avisa si esto se usa
        fallback = f"{platform.node()}-{platform.processor()}-{platform.machine()}-{uuid_lib.uuid4().hex if False else ''}"
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
        for idx, entry in enumerate(db_data):
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

def launch_tweaks():
    """Ejecuta el módulo tweaks después del login exitoso."""
    clear_screen()
    
    print(f"{Colors.BRIGHT_RED}{Colors.BOLD}")
    print("  Cargando Quantum System...")
    print(f"{Colors.RESET}")
    time.sleep(1)
    
    try:
        # Intentar importar tweaks como módulo
        import tweaks
        
        # Si tweaks tiene una función main, ejecutarla
        if hasattr(tweaks, 'main'):
            tweaks.main()
        # Si tweaks tiene una función run, ejecutarla
        elif hasattr(tweaks, 'run'):
            tweaks.run()
        # Si tweaks es un script simple, ya se ejecutó al importar
        else:
            print(f"{Colors.BRIGHT_RED}{Colors.BOLD}")
            print("  Quantum System cargado.")
            print("  Esperando comandos...")
            print(f"{Colors.RESET}")
            
            # Mantener el programa en ejecución
            while True:
                try:
                    cmd = input(f"{Colors.BRIGHT_RED}Quantum> {Colors.RESET}")
                    if cmd.lower() in ['exit', 'quit', 'salir']:
                        break
                    elif cmd.lower() == 'help':
                        print(f"{Colors.BRIGHT_RED}  Comandos disponibles:{Colors.RESET}")
                        print(f"  {Colors.WHITE}help{Colors.RESET} - Muestra esta ayuda")
                        print(f"  {Colors.WHITE}exit{Colors.RESET} - Sale del sistema")
                    else:
                        print(f"{Colors.BRIGHT_RED}  Comando no reconocido: {cmd}{Colors.RESET}")
                except KeyboardInterrupt:
                    break
                except EOFError:
                    break
    
    except ImportError:
        # Si no se encuentra tweaks.py, mostrar mensaje
        print(f"{Colors.BRIGHT_RED}{Colors.BOLD}")
        print("  ✗ Error: No se encontró el módulo tweaks.py")
        print("  Asegúrate de que tweaks.py esté en el mismo directorio.")
        print(f"{Colors.RESET}")
        input(f"\n{Colors.BRIGHT_RED}Presiona Enter para salir...{Colors.RESET}")
    
    except Exception as e:
        print(f"{Colors.BRIGHT_RED}{Colors.BOLD}")
        print(f"  ✗ Error al ejecutar tweaks: {e}")
        print(f"{Colors.RESET}")
        input(f"\n{Colors.BRIGHT_RED}Presiona Enter para salir...{Colors.RESET}")

def show_access_granted(username, license_key, hwid):
    """Muestra la pantalla de acceso concedido y lanza tweaks."""
    clear_screen()
    print_banner()
    
    print(f"{Colors.BRIGHT_RED}{Colors.BOLD}")
    print("  ACCESO CONCEDIDO")
    print("  " + "-" * 40)
    print(f"  Usuario: {username}")
    print(f"  Licencia: {license_key}")
    print("  " + "-" * 40)
    print(f"{Colors.RESET}")
    
    time.sleep(2)
    
    # Lanzar tweaks.py
    launch_tweaks()

def main():
    """Función principal del sistema de login."""
    enable_windows_ansi()
    
    # Verificar que el token esté configurado
    if GITHUB_TOKEN == "AQUI_VA_TU_PERSONAL_ACCESS_TOKEN":
        clear_screen()
        print_banner()
        print_error("Debes configurar tu Personal Access Token")
        print(f"{Colors.BRIGHT_RED}\n  Pasos:{Colors.RESET}")
        print(f"  {Colors.WHITE}1. GitHub → Settings → Developer settings{Colors.RESET}")
        print(f"  {Colors.WHITE}2. Personal access tokens → Tokens (classic){Colors.RESET}")
        print(f"  {Colors.WHITE}3. Genera nuevo token con permiso 'repo'{Colors.RESET}")
        print(f"  {Colors.WHITE}4. Pega el token en la variable GITHUB_TOKEN{Colors.RESET}")
        input(f"\n{Colors.BRIGHT_RED}Presiona Enter para salir...{Colors.RESET}")
        return
    
    # Inicializar API de GitHub
    github = GitHubAPI(GITHUB_TOKEN, GITHUB_REPO_OWNER, GITHUB_REPO_NAME, GITHUB_BRANCH, GITHUB_FILE_PATH)
    
    # Pantalla de inicio
    clear_screen()
    print_banner()
    print_loading_animation("Conectando con Quantum API", 2)
    
    connected, message = github.test_connection()
    if not connected:
        print_error(message)
        input(f"\n{Colors.BRIGHT_RED}Presiona Enter para salir...{Colors.RESET}")
        return
    
    max_attempts = 5
    attempts = 0
    
    while attempts < max_attempts:
        clear_screen()
        print_banner()
        
        # Login
        print(f"{Colors.BRIGHT_RED}{Colors.BOLD}")
        print("  QUANTUM LOGIN")
        print("  " + "-" * 40)
        print(f"{Colors.RESET}")
        
        print(f"{Colors.WHITE}  Username: {Colors.RESET}", end='', flush=True)
        username = input().strip()
        
        print(f"{Colors.WHITE}  Password: {Colors.RESET}", end='', flush=True)
        password = getpass.getpass('').strip()
        
        if not username or not password:
            print_error("Usuario y contraseña son obligatorios")
            input(f"\n{Colors.BRIGHT_RED}Presiona Enter para continuar...{Colors.RESET}")
            attempts += 1
            continue
        
        print_loading_animation("Validando credenciales", 1)
        
        # OBTENER DATOS FRESCOS DE LA API EN CADA INTENTO
        db_data, sha = github.get_file_content()
        
        if db_data is None:
            print_error("No se pudo cargar la base de datos")
            input(f"\n{Colors.BRIGHT_RED}Presiona Enter para continuar...{Colors.RESET}")
            attempts += 1
            continue
        
        current_hwid = get_hwid()
        user, _ = find_user_in_data(db_data, username)
        
        if not user:
            print_error("Usuario no encontrado")
            attempts += 1
            remaining = max_attempts - attempts
            if remaining > 0:
                print(f"{Colors.BRIGHT_RED}\n  Intentos restantes: {remaining}{Colors.RESET}")
                input(f"\n{Colors.BRIGHT_RED}Presiona Enter para continuar...{Colors.RESET}")
            continue
        
        if user.get("Password") != password:
            print_error("Contraseña incorrecta")
            attempts += 1
            remaining = max_attempts - attempts
            if remaining > 0:
                print(f"{Colors.BRIGHT_RED}\n  Intentos restantes: {remaining}{Colors.RESET}")
                input(f"\n{Colors.BRIGHT_RED}Presiona Enter para continuar...{Colors.RESET}")
            continue
        
        license_key = user.get("License", "")
        if not license_key:
            print_error("No tiene licencia asignada")
            print_error("Los 3 campos son obligatorios")
            attempts += 1
            input(f"\n{Colors.BRIGHT_RED}Presiona Enter para continuar...{Colors.RESET}")
            continue
        
        existing_hwid = user.get("HWID", "")
        
        if existing_hwid:
            if existing_hwid == current_hwid:
                show_access_granted(username, license_key, current_hwid)
                return
            else:
                print_error("Este usuario está vinculado a otro hardware")
                attempts += 1
                remaining = max_attempts - attempts
                if remaining > 0:
                    print(f"{Colors.BRIGHT_RED}\n  Intentos restantes: {remaining}{Colors.RESET}")
                    input(f"\n{Colors.BRIGHT_RED}Presiona Enter para continuar...{Colors.RESET}")
                continue
        else:
            print_success("Primer login detectado")
            print(f"{Colors.BRIGHT_RED}  Registrando HWID: {current_hwid}{Colors.RESET}")
            
            updated_data, encontrado = update_hwid_in_data(db_data, username, current_hwid)
            
            if not encontrado:
                print_error("No se pudo encontrar al usuario")
                input(f"\n{Colors.BRIGHT_RED}Presiona Enter para continuar...{Colors.RESET}")
                attempts += 1
                continue
            
            print_loading_animation("Actualizando base de datos", 1.5)
            success = github.update_file_content(updated_data, sha)
            
            if success:
                show_access_granted(username, license_key, current_hwid)
                return
            else:
                print_error("No se pudo registrar el HWID")
                print(f"{Colors.BRIGHT_RED}  El acceso no será concedido.{Colors.RESET}")
                input(f"\n{Colors.BRIGHT_RED}Presiona Enter para continuar...{Colors.RESET}")
                attempts += 1
                continue
    
    clear_screen()
    print_banner()
    print_error("ACCESO BLOQUEADO")
    print(f"{Colors.BRIGHT_RED}\n  Demasiados intentos fallidos.{Colors.RESET}")
    print(f"{Colors.BRIGHT_RED}  El programa se cerrará.{Colors.RESET}")
    input(f"\n{Colors.BRIGHT_RED}Presiona Enter para salir...{Colors.RESET}")

if __name__ == "__main__":
    main()