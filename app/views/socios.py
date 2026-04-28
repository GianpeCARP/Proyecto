# =============================================================================
# views/socios.py — Gestión de socios del gimnasio
# =============================================================================
# Esta vista muestra la tabla completa de socios registrados en el gimnasio.
# Funcionalidades:
#   - Tabla con columnas: Nombre, Plan, Estado, Vence, Acciones
#   - Barra de búsqueda en tiempo real (filtra por nombre o plan)
#   - Chips de filtro por estado (Todos / Activos / Vencidos)
#   - Modal para crear o editar un socio
#   - Diálogo de confirmación para eliminar

import flet as ft
from app.config import Colors                   # Paleta de colores del sistema
from app.state import app_state                 # Estado global con los datos de socios
# Componentes reutilizables del sistema de diseño
from app.components.ui import (build_topbar, status_badge, primary_button,
                                input_field, show_snack, open_dialog,
                                close_dialog, confirm_dialog)


class SociosView:
    """
    Vista de gestión de socios.
    Mantiene referencias (Refs) a la barra de búsqueda y la tabla
    para poder actualizarlas dinámicamente sin reconstruir la vista completa.
    """

    def __init__(self, page: ft.Page, router):
        self.page   = page
        self.router = router
        # Ref al campo de búsqueda — permite leer su valor al filtrar
        self.search_ref = ft.Ref[ft.TextField]()
        # Ref a la Column que contiene la tabla — permite reemplazar su contenido al filtrar
        self.table_ref  = ft.Ref[ft.Column]()

    def build(self) -> ft.Column:
        """Construye y retorna el árbol completo de controles de la vista."""
        socios = app_state.get_socios()  # Obtiene la lista completa de socios

        # Topbar con título, conteo de socios y botón "Nuevo Socio"
        topbar = build_topbar(
            "Socios",
            f"{len(socios)} socios registrados",
            actions=[
                primary_button("Nuevo Socio", ft.Icons.PERSON_ADD_ROUNDED,
                               on_click=self._open_form),  # Abre el modal de creación
            ]
        )

        # ── Barra de búsqueda + chips de filtro ──────────────────────────────
        search_bar = ft.Container(
            content=ft.Row([
                # Campo de texto con búsqueda en tiempo real (on_change)
                ft.TextField(
                    ref=self.search_ref,
                    hint_text="Buscar por nombre, plan...",
                    prefix_icon=ft.Icons.SEARCH_ROUNDED,
                    color=Colors.TEXT_PRIMARY,
                    hint_style=ft.TextStyle(color=Colors.TEXT_MUTED),
                    bgcolor=Colors.BG_INPUT,
                    border_color=Colors.BORDER,
                    focused_border_color=Colors.ACCENT,
                    border_radius=10,
                    expand=True,
                    height=44,
                    content_padding=ft.padding.symmetric(horizontal=16, vertical=10),
                    on_change=self._on_search,  # Se llama en cada keystroke
                ),
                # Chips de filtro rápido por estado
                _filter_chip("Todos", True),    # Activo por defecto
                _filter_chip("Activos", False),
                _filter_chip("Vencidos", False),
            ], spacing=10),
            padding=ft.padding.only(bottom=16),
        )

        # ── Tabla de socios ───────────────────────────────────────────────────
        # Construye la tabla con todos los socios y la envuelve en un Ref
        table_content = self._build_table(socios)
        table_col = ft.Column(
            ref=self.table_ref,           # Ref para actualizar al filtrar
            controls=[table_content],     # La tabla es el único hijo inicial
        )

        # ── Ensamblado final ──────────────────────────────────────────────────
        body = ft.Column([
            topbar,
            ft.Container(
                content=ft.Column([
                    search_bar,
                    # Container con borde que envuelve la tabla
                    ft.Container(
                        content=table_col,
                        bgcolor=Colors.BG_CARD,
                        border_radius=14,
                        border=ft.border.all(1, Colors.BORDER),
                        padding=0,
                        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,  # Recorta el contenido al borde redondeado
                    ),
                ]),
                padding=ft.padding.all(24),
                expand=True,
            ),
        ], spacing=0, expand=True, scroll=ft.ScrollMode.AUTO)

        return body

    def _build_table(self, socios: list) -> ft.Column:
        """
        Construye la tabla de socios con encabezado y filas.
        Recibe la lista filtrada (puede ser un subconjunto de todos los socios).
        Se llama tanto al construir la vista como al filtrar.
        """
        # Fila de encabezado con los nombres de columna en mayúscula y color muted
        header = ft.Container(
            content=ft.Row([
                ft.Text("Nombre",   color=Colors.TEXT_MUTED, size=12,
                        weight=ft.FontWeight.W_600, expand=3),  # expand=3 → más ancha
                ft.Text("Plan",     color=Colors.TEXT_MUTED, size=12,
                        weight=ft.FontWeight.W_600, expand=2),
                ft.Text("Estado",   color=Colors.TEXT_MUTED, size=12,
                        weight=ft.FontWeight.W_600, expand=2),
                ft.Text("Vence",    color=Colors.TEXT_MUTED, size=12,
                        weight=ft.FontWeight.W_600, expand=2),
                ft.Text("Acciones", color=Colors.TEXT_MUTED, size=12,
                        weight=ft.FontWeight.W_600, expand=2),
            ]),
            padding=ft.padding.symmetric(horizontal=20, vertical=14),
            bgcolor=Colors.BG_SIDEBAR,  # Fondo ligeramente diferente para el header
        )

        # Genera la fila de encabezado seguida de una fila por cada socio
        rows = [header]
        for s in socios:
            rows.append(self._table_row(s))

        return ft.Column(rows, spacing=0)

    def _table_row(self, s: dict) -> ft.Container:
        """
        Construye una fila de la tabla para un socio específico.
        Incluye hover effect y los botones de editar/eliminar.
        """
        initial = s["nombre"][0].upper()  # Inicial para el avatar

        def on_hover(e: ft.HoverEvent):
            """Resalta la fila al pasar el mouse — mejora la legibilidad."""
            e.control.bgcolor = Colors.BG_INPUT if e.data == "true" else ft.Colors.TRANSPARENT
            e.control.update()

        return ft.Container(
            content=ft.Row([
                # Columna Nombre: avatar circular + texto del nombre
                ft.Row([
                    ft.Container(
                        content=ft.Text(initial, color=Colors.WHITE, size=13,
                                        weight=ft.FontWeight.BOLD),
                        width=32, height=32, border_radius=16,
                        bgcolor=Colors.ACCENT, alignment=ft.Alignment.CENTER,
                    ),
                    ft.Text(s["nombre"], color=Colors.TEXT_PRIMARY, size=14),
                ], spacing=10, expand=3),
                # Columna Plan: nombre del plan (Básico, Premium, Anual)
                ft.Container(
                    content=ft.Text(s["plan"], color=Colors.TEXT_SECONDARY, size=13),
                    expand=2,
                ),
                # Columna Estado: badge coloreado según estado
                ft.Container(content=status_badge(s["estado"]), expand=2,
                             alignment=ft.Alignment.CENTER_LEFT),
                # Columna Vence: fecha de vencimiento como texto simple
                ft.Text(s["vence"], color=Colors.TEXT_SECONDARY, size=13, expand=2),
                # Columna Acciones: botones de editar y eliminar
                ft.Row([
                    ft.IconButton(ft.Icons.EDIT_ROUNDED, icon_color=Colors.INFO,
                                  icon_size=18, tooltip="Editar",
                                  on_click=lambda e, x=s: self._open_form(e, x)),
                    ft.IconButton(ft.Icons.DELETE_OUTLINE_ROUNDED, icon_color=Colors.DANGER,
                                  icon_size=18, tooltip="Eliminar",
                                  on_click=lambda e, x=s: self._confirm_delete(x)),
                ], expand=2),
            ]),
            padding=ft.padding.symmetric(horizontal=20, vertical=12),
            border=ft.border.only(bottom=ft.BorderSide(1, Colors.BORDER)),
            on_hover=on_hover,
            animate=ft.Animation(120),
        )

    def _on_search(self, e):
        """
        Callback de búsqueda en tiempo real — se ejecuta en cada keystroke.
        Filtra la lista de socios por nombre o plan (case-insensitive)
        y reconstruye la tabla con los resultados filtrados.
        """
        query  = e.control.value.lower()         # Texto ingresado en minúsculas
        socios = app_state.get_socios()          # Lista completa de socios
        # Filtra socios cuyo nombre o plan contenga el texto buscado
        filtered = [s for s in socios
                    if query in s["nombre"].lower() or query in s["plan"].lower()]
        # Reemplaza el contenido de la tabla con los resultados filtrados
        self.table_ref.current.controls = [self._build_table(filtered)]
        self.table_ref.current.update()  # Renderiza el cambio

    def _open_form(self, e=None, socio: dict = None):
        """
        Abre el modal (AlertDialog) para crear un nuevo socio o editar uno existente.
        Si `socio` es None → modo creación. Si `socio` tiene datos → modo edición.
        Pre-carga los campos con los datos del socio cuando es edición.
        """
        is_edit    = socio is not None
        nombre_ref = ft.Ref[ft.TextField]()   # Ref para pre-cargar el nombre en edición
        plan_ref   = ft.Ref[ft.Dropdown]()   # Ref para pre-cargar el plan en edición

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Editar Socio" if is_edit else "Nuevo Socio",
                          color=Colors.TEXT_PRIMARY, weight=ft.FontWeight.BOLD),
            bgcolor=Colors.BG_CARD,
            content=ft.Container(
                width=420,
                content=ft.Column([
                    input_field("Nombre completo", "Ej: Juan García",
                                icon=ft.Icons.PERSON_OUTLINE_ROUNDED, ref=nombre_ref),
                    ft.Container(height=12),
                    # Dropdown de plan — pre-selecciona el plan del socio en edición
                    ft.Dropdown(
                        ref=plan_ref,
                        label="Plan",
                        options=[
                            ft.dropdown.Option("Básico"),
                            ft.dropdown.Option("Premium"),
                            ft.dropdown.Option("Anual"),
                        ],
                        value=socio["plan"] if is_edit else "Básico",  # Valor inicial
                        color=Colors.TEXT_PRIMARY,
                        bgcolor=Colors.BG_INPUT,
                        border_color=Colors.BORDER,
                        focused_border_color=Colors.ACCENT,
                        border_radius=10,
                    ),
                    ft.Container(height=12),
                    input_field("Email", "ejemplo@mail.com", icon=ft.Icons.EMAIL_OUTLINED),
                    ft.Container(height=12),
                    input_field("Teléfono", "+54 9 000 0000000",
                                icon=ft.Icons.PHONE_OUTLINED),
                ], spacing=0, tight=True),
            ),
            actions=[
                ft.TextButton("Cancelar",
                              style=ft.ButtonStyle(color=Colors.TEXT_SECONDARY),
                              on_click=lambda e: close_dialog(self.page, dlg)),
                ft.TextButton("Guardar",
                              style=ft.ButtonStyle(color=Colors.ACCENT),
                              on_click=lambda e: self._save_socio(dlg)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        # Pre-carga el nombre del socio en el campo si es modo edición
        if is_edit and nombre_ref.current:
            nombre_ref.current.value = socio["nombre"]

        open_dialog(self.page, dlg)  # Agrega al overlay y abre el modal

    def _save_socio(self, dlg):
        """
        Guarda el socio (crear o editar).
        TODO: conectar con POST /api/socios o PUT /api/socios/{id}
        Por ahora solo cierra el modal y muestra una notificación de éxito.
        """
        close_dialog(self.page, dlg)
        show_snack(self.page, "Socio guardado correctamente ✓", Colors.SUCCESS)

    def _confirm_delete(self, socio: dict):
        """
        Abre un diálogo de confirmación antes de eliminar un socio.
        Usa el componente genérico confirm_dialog() del sistema de UI.
        El callback on_confirm muestra el snack de eliminación.
        TODO: conectar con DELETE /api/socios/{id}
        """
        dlg = confirm_dialog(
            self.page,
            "Eliminar Socio",
            f"¿Estás seguro de eliminar a {socio['nombre']}? Esta acción no se puede deshacer.",
            on_confirm=lambda: show_snack(self.page, f"{socio['nombre']} eliminado", Colors.DANGER),
        )
        open_dialog(self.page, dlg)


def _filter_chip(label: str, active: bool) -> ft.Container:
    """
    Construye un chip de filtro para la barra de búsqueda.
    Los chips activos tienen borde y fondo naranja translúcido.
    Los inactivos tienen borde gris y fondo oscuro.
    NOTA: actualmente los chips son decorativos — su lógica de filtrado
    real está pendiente de implementar (TODO).
    """
    return ft.Container(
        content=ft.Text(label,
                        color=Colors.ACCENT if active else Colors.TEXT_SECONDARY,
                        size=13,
                        weight=ft.FontWeight.W_500 if active else ft.FontWeight.NORMAL),
        bgcolor=Colors.ACCENT_GLOW if active else Colors.BG_INPUT,
        border_radius=20,
        padding=ft.padding.symmetric(horizontal=14, vertical=8),
        border=ft.border.all(1, Colors.ACCENT if active else Colors.BORDER),
    )
