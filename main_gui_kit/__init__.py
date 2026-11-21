"""main_gui_kit — shared Qt6 GUI/logic building blocks for the Engineering /
Fusion tools (renamed from plant3d_gui_kit, v0.2.0; A4/A5 release pending).

Modules:
    theme       -- unified Palette (Light = Slide-17) + build_qss() + ThemeManager
    buttons     -- ButtonKind + action_button(kind=...) + equalize_widths (A2)
    widgets     -- card(), page_title(), section_label(), status_label(), LogPanel
    branding    -- BrandingManager / HeaderBanner
    i18n        -- dictionary-based translation (T() / set_lang() / register())
    main_window -- BaseMainWindow (pre-A1 tab shell) + SidebarMainWindow (A1 sidebar shell)
    navigation  -- TopNavBar, refresh_widget(), placeholder_page(), mark_tab_migration()
    settings    -- JSON-backed named view-layout profiles (A4)
    tables      -- table model, filtering and persistent table layouts (A4);
                   v0.3.0 adds the enforced data-surface standard: one shared
                   value-filter header for tables and trees, per-column value
                   normalizers, a compact tree variant, searchable_list() for
                   selection lists and bind_layout_persistence() for silent,
                   project-scoped column layouts. All additions are additive —
                   configure_table_view() and configure_tree_view() keep their
                   previous signatures and behaviour, so BOMFusion,
                   PlantSpecBridge and AZEngineeringProjectTool need no change.
                   v0.3.1 adds the shared table size control (60-100 %):
                   TableZoomSlider / table_zoom_slider() / apply_table_zoom(),
                   persisted with the remembered column layout. Also additive.
    preview     -- reusable data-preview dialog (A4)
    jobs        -- QThread background-job pattern with progress signals (A5)

Status: A2 + A3 + A4/A5 + A1 implemented (Light mode). Reference consumer for
A1 (SidebarMainWindow) is P3D_Data_Manager. Hygiene (A6) is still open, see
the PhaseA-Detailplan.
"""

__version__ = "0.3.1"
