# =============================================================================
# views/login.py — Vista de inicio de sesión
# =============================================================================
# Esta vista es la primera que ve el usuario al abrir la aplicación.
# Se divide en dos paneles:
#   - Izquierdo (decorativo): logo, nombre del sistema y lista de características
#   - Derecho (funcional): formulario de usuario y contraseña con validación
# Tras autenticarse exitosamente, reconstruye la página mostrando el shell
# principal (sidebar + dashboard).

import flet as ft
from app.config import Colors, APP_NAME   # Paleta de colores y nombre del sistema
from app.state import app_state           # Estado global para ejecutar el login
from app.components.ui import input_field, show_snack  # Componentes reutilizables


def show_login(page: ft.Page, router):
    """
    Reemplaza el contenido de la página con la vista de login.
    Limpia todos los controles previos y dibuja el layout de dos paneles.
    """

    # ── Referencias (Refs) para acceder a los controles desde callbacks ───────
    # Los Refs permiten leer/modificar controles Flet desde funciones externas
    username_ref = ft.Ref[ft.TextField]()  # Campo de usuario
    password_ref = ft.Ref[ft.TextField]()  # Campo de contraseña
    error_ref    = ft.Ref[ft.Text]()       # Texto de error (oculto por defecto)
    btn_ref      = ft.Ref[ft.Container]()  # Botón de submit (referencia reservada)

    def handle_login(e=None):
        """
        Maneja el intento de inicio de sesión.
        Lee los valores de los campos, valida que no estén vacíos y llama
        a app_state.login(). Si tiene éxito, carga el shell principal.
        Si falla, muestra el mensaje de error en la UI.
        `e=None` permite llamar a esta función tanto desde on_click como desde on_key.
        """
        # Lee y limpia espacios de los campos
        u = username_ref.current.value.strip()
        p = password_ref.current.value.strip()

        # Validación básica: ambos campos deben tener contenido
        if not u or not p:
            error_ref.current.value   = "Completá todos los campos"
            error_ref.current.visible = True
            error_ref.current.update()  # Actualiza solo este control para eficiencia
            return

        # Intenta autenticar contra los datos del estado global
        ok, msg = app_state.login(u, p)

        if ok:
            # Nota: en Flet moderno podría guardarse la sesión en page.session,
            # pero actualmente se usa app_state como fuente de verdad.
            # Las líneas comentadas son el código para sesión persistente futura.

            error_ref.current.visible = False  # Oculta cualquier error previo
            error_ref.current.update()
            _load_main_app(page, router)        # Carga el shell principal de la app
        else:
            # Muestra el mensaje de error retornado por app_state.login()
            error_ref.current.value   = msg
            error_ref.current.visible = True
            error_ref.current.update()

    def on_key(e: ft.KeyboardEvent):
        """
        Permite enviar el formulario presionando Enter.
        Registrado en page.on_keyboard_event para capturar teclas globalmente.
        """
        if e.key == "Enter":
            handle_login()

    # Registra el handler de teclado en la página
    page.on_keyboard_event = on_key

    # ── Panel izquierdo — decorativo ──────────────────────────────────────────
    # Contiene efectos visuales de fondo (círculo glow, texto grande semi-transparente)
    # y la información descriptiva del sistema (logo, nombre, características).
    left_panel = ft.Container(
        expand=2,                       # Ocupa 2/3 del ancho total de la ventana
        bgcolor=Colors.BG_SIDEBAR,
        content=ft.Stack([              # Stack permite superponer elementos
            # ── Círculo decorativo de fondo (glow naranja) ─────────────────
            ft.Container(
                content=ft.Column([
                    ft.Container(
                        width=300, height=300, border_radius=150,
                        bgcolor=Colors.ACCENT_GLOW,    # Naranja semi-transparente
                        margin=ft.margin.only(top=-80, left=-80),  # Parcialmente fuera de la vista
                    ),
                ]),
            ),
            # ── Texto "GYM PRO" semi-transparente de fondo ─────────────────
            # Crea un efecto tipográfico decorativo con opacidad muy baja
            ft.Container(
                content=ft.Column([
                    ft.Text("Olimp", color=Colors.ACCENT, size=96,
                            weight=ft.FontWeight.BOLD, font_family="Bebas Neue",
                            opacity=0.08),        # Solo 8% de opacidad — casi invisible
                    ft.Text("OS", color=Colors.TEXT_PRIMARY, size=96,
                            weight=ft.FontWeight.BOLD, font_family="Bebas Neue",
                            opacity=0.04),        # Solo 4% de opacidad
                ], spacing=-20),
                alignment=ft.Alignment.CENTER,
                expand=True,
            ),
            # ── Contenido principal del panel izquierdo ─────────────────────
            ft.Container(
                content=ft.Column([
                    # Logo cuadrado con "O"
                    ft.Container(
                        content=ft.Text("O", color=Colors.BG_DARK, size=32,
                                        weight=ft.FontWeight.BOLD),
                        width=60, height=60, border_radius=16,
                        bgcolor=Colors.ACCENT,
                        alignment=ft.Alignment.CENTER,
                    ),
                    ft.Container(height=24),
                    # Nombre de la app en fuente Bebas Neue grande
                    ft.Text(APP_NAME, color=Colors.TEXT_PRIMARY, size=48,
                            weight=ft.FontWeight.BOLD, font_family="Bebas Neue"),
                    # Subtítulo descriptivo
                    ft.Text("Sistema de Gestión\nIntegral para Gimnasios",
                            color=Colors.TEXT_SECONDARY, size=16,
                            text_align=ft.TextAlign.LEFT),
                    ft.Container(height=32),
                    # Lista de características principales con íconos
                    _feature_row(ft.Icons.GROUP_ROUNDED, "Gestión completa de socios"),
                    ft.Container(height=12),
                    _feature_row(ft.Icons.FITNESS_CENTER_ROUNDED, "Rutinas y seguimiento"),
                    ft.Container(height=12),
                    _feature_row(ft.Icons.RESTAURANT_MENU_ROUNDED, "Planes nutricionales"),
                    ft.Container(height=12),
                    _feature_row(ft.Icons.ANALYTICS_ROUNDED, "Dashboard con estadísticas"),
                ], horizontal_alignment=ft.CrossAxisAlignment.START),
                padding=ft.padding.all(52),
                alignment=ft.Alignment.CENTER_LEFT,
                expand=True,
            ),
        ]),
    )

    # ── Panel derecho — formulario de login ───────────────────────────────────
    login_form = ft.Container(
        expand=1,                       # Ocupa 1/3 del ancho total (complemento del expand=2)
        bgcolor=Colors.BG_DARK,
        content=ft.Column([
            ft.Container(expand=True),  # Espacio flexible para centrar verticalmente la tarjeta
            # Tarjeta de login centrada verticalmente
            ft.Container(
                content=ft.Column([
                    # Encabezado del formulario
                    ft.Text("Bienvenido de nuevo", color=Colors.TEXT_PRIMARY,
                            size=28, weight=ft.FontWeight.BOLD),
                    ft.Text("Ingresá tus credenciales para continuar",
                            color=Colors.TEXT_SECONDARY, size=14),
                    ft.Container(height=32),

                    # Campo de usuario (usando el componente reutilizable input_field)
                    input_field("Usuario", "tu_usuario",
                                icon=ft.Icons.PERSON_OUTLINE_ROUNDED,
                                ref=username_ref),
                    ft.Container(height=16),
                    # Campo de contraseña — password=True oculta el texto
                    input_field("Contraseña", "••••••••", password=True,
                                icon=ft.Icons.LOCK_OUTLINE_ROUNDED,
                                ref=password_ref),
                    ft.Container(height=8),

                    # Texto de error — oculto por defecto, visible solo si hay error
                    ft.Text(ref=error_ref, color=Colors.DANGER, size=12,
                            visible=False, value=""),
                    ft.Container(height=12),

                    # Botón de submit — llama a handle_login al hacer clic
                    ft.Container(
                        ref=btn_ref,
                        content=ft.Row([
                            ft.Text("Iniciar sesión", color=Colors.WHITE, size=15,
                                    weight=ft.FontWeight.W_600),
                        ], alignment=ft.MainAxisAlignment.CENTER),
                        bgcolor=Colors.ACCENT,
                        border_radius=10,
                        height=48,
                        on_click=handle_login,
                        animate=ft.Animation(150, ft.AnimationCurve.EASE_IN_OUT),
                    ),

                    ft.Container(height=24),
                    # Bloque de credenciales demo para facilitar pruebas
                    ft.Container(
                        content=ft.Row([
                            ft.Text("Demo:", color=Colors.TEXT_MUTED, size=12),
                            ft.Text(" admin / admin123  |  trainer / train123",
                                    color=Colors.TEXT_SECONDARY, size=12),
                        ]),
                        bgcolor=Colors.BG_INPUT,
                        border_radius=8,
                        padding=ft.padding.symmetric(horizontal=12, vertical=8),
                    ),
                ], spacing=0,
                   horizontal_alignment=ft.CrossAxisAlignment.STRETCH),  # Estira los hijos al ancho
                width=380,                          # Ancho fijo de la tarjeta
                padding=ft.padding.all(40),
                bgcolor=Colors.BG_CARD,
                border_radius=20,
                border=ft.border.all(1, Colors.BORDER),
            ),
            ft.Container(expand=True),  # Espacio flexible inferior (centra la tarjeta)
            # Footer de copyright
            ft.Text(f"© 2025 {APP_NAME} — Todos los derechos reservados",
                    color=Colors.TEXT_MUTED, size=11,
                    text_align=ft.TextAlign.CENTER),
            ft.Container(height=24),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        padding=ft.padding.symmetric(horizontal=40),
    )

    # ── Reemplaza toda la página con el layout de login ───────────────────────
    page.controls.clear()  # Elimina todos los controles previos de la página
    page.add(
        ft.Container(
            content=ft.Row([left_panel, login_form], spacing=0, expand=True),
            expand=True,
            bgcolor=Colors.BG_DARK,
        )
    )
    page.update()  # Renderiza los cambios en la pantalla


def _load_main_app(page: ft.Page, router):
    """
    Carga la estructura principal de la aplicación tras el login exitoso.
    Construye el shell (sidebar + contenedor de contenido), muestra el Dashboard
    como vista inicial y registra el content_ref en el router para navegación futura.
    """
    from app.config import Routes
    from app.components.layout import build_main_layout
    from app.views.dashboard import DashboardView

    # Referencia al Container de contenido — el router la usará para cambiar vistas
    content_ref = ft.Ref[ft.Container]()

    # Instancia y construye la vista inicial (Dashboard)
    dashboard        = DashboardView(page=page, router=router)
    initial_content  = dashboard.build()

    # Container de contenido referenciado — el router reemplazará su .content al navegar
    content_container = ft.Container(
        ref=content_ref,
        content=initial_content,    # Vista inicial: Dashboard
        expand=True,
        bgcolor=Colors.BG_DARK,
    )

    # Importa y construye el sidebar con "dashboard" como ruta activa
    from app.components.ui import build_sidebar
    sidebar = build_sidebar(page, router, Routes.DASHBOARD)

    # Shell completo: sidebar fijo + área de contenido expandible
    shell = ft.Row([sidebar, content_container], spacing=0, expand=True)

    # Registra el content_ref en el router para que pueda actualizar la vista
    # al llamar router.navigate() desde cualquier parte de la app
    router.setup(content_ref)

    # Reemplaza toda la página con el nuevo shell
    page.controls.clear()
    page.add(ft.Container(content=shell, expand=True))
    page.update()

    # Actualiza el estado global para reflejar que estamos en el Dashboard
    app_state.current_route = Routes.DASHBOARD


def _feature_row(icon: str, text: str) -> ft.Row:
    """
    Crea una fila decorativa con ícono + texto para la lista de características
    del panel izquierdo del login.
    Cada fila tiene un contenedor cuadrado con el ícono y el texto a su derecha.
    """
    from app.config import Colors
    return ft.Row([
        # Contenedor cuadrado con fondo naranja semi-transparente e ícono centrado
        ft.Container(
            content=ft.Icon(icon, color=Colors.ACCENT, size=18),
            width=36, height=36, border_radius=10,
            bgcolor=Colors.ACCENT_GLOW,
            alignment=ft.Alignment.CENTER,
        ),
        # Texto descriptivo de la característica
        ft.Text(text, color=Colors.TEXT_SECONDARY, size=14),
    ], spacing=12)
