# tcc_app/utils.py
from functools import wraps
from flask import session, redirect, url_for, request, g
from datetime import datetime

# -------------------------------------------------
# Idioma / i18n bem leve para templates
# (mantido para compatibilidade, mas textos
# ajustados para PrevSuite e IA)               # [MOD bloco]
# -------------------------------------------------
TRANSLATIONS = {
    "pt": {
        "login_title": "Entrar",
        "login_welcome": "Acesse sua conta para gerenciar estoque, vendas e previsões com IA.",
        "email": "E-mail",
        "password": "Senha",
        "remember_me": "Lembrar de mim",
        "enter": "Entrar",
        "forgot_password": "Esqueceu a senha?",
        "create_free": "Criar conta gratuita",
        # [MOD] antes: "Previsão de Demanda de verdade"
        "hero_title": "Previsão de demanda com IA com PrevSuite!",
        "hero_sub": "Relatórios, Estoque e Previsão com IA",
        "weekly_sales": "Vendas semanais",
        "weekly_revenue": "Receita semanal",
        "low_stock_items": "Itens com pouco estoque",
        "out_of_stock_items": "Itens sem estoque",
        "welcome_banner_title": "Bem-vindo ao Prev Suite!",
        "welcome_banner_sub": "Configure seu estoque para começar",
        "manage_stock": "Gerenciar estoque",
        "next_week_predictions": "Previsões para a próxima semana",
        "no_suggestions": "Sem sugestões no momento",
        "stock_alerts": "Alertas de estoque",
        "dashboard": "Dashboard",
        "inventory": "Estoque",
        "ingredients": "Ingredientes",
        "purchases": "Compras",
        "menu": "Cardápio",
        "catalog": "Catálogo",
        "sales": "Vendas",
        "reports": "Relatórios",
        "forecast": "Previsão",
        "logout": "Sair",
        "powered_by": "Powered by Aurora Tech — uso exclusivo de clientes Aurora Tech",
        "register_title": "Criar conta",
        "register_subtitle": "Preencha os campos abaixo para começar a usar o PrevSuite.",
        "register_name_label": "Nome completo",
        "register_email_label": "E-mail",
        "register_phone_label": "Telefone (opcional)",
        "register_password_label": "Senha",
        "register_confirm_password_label": "Confirmar senha",
        "register_button": "Criar conta",
        "register_login_link": "Já tem conta? Entrar",
        "forgot_password_title": "Recuperar senha",
        "forgot_password_subtitle": "Informe seu e-mail e defina uma nova senha para acessar o PrevSuite.",
        "forgot_password_email_label": "E-mail cadastrado",
        "forgot_password_new_password_label": "Nova senha",
        "forgot_password_confirm_password_label": "Confirmar nova senha",
        "forgot_password_button": "Alterar senha agora",
        "forgot_password_back_to_login": "Voltar para o login",
    },
    "en": {
        "login_title": "Sign in",
        "login_welcome": "Access your account to manage inventory, sales and AI forecasts.",
        "email": "Email",
        "password": "Password",
        "remember_me": "Remember me",
        "enter": "Enter",
        "forgot_password": "Forgot your password?",
        "create_free": "Create free account",
        # [MOD] melhor alinhado com PT/ES e PrevSuite
        "hero_title": "Demand forecasting with AI with PrevSuite!",
        "hero_sub": "Reports, Inventory and Forecast with AI",
        "weekly_sales": "Weekly sales",
        "weekly_revenue": "Weekly revenue",
        "low_stock_items": "Low stock items",
        "out_of_stock_items": "Out of stock items",
        "welcome_banner_title": "Welcome to Prev Suite!",
        "welcome_banner_sub": "Set up your inventory to get started",
        "manage_stock": "Manage Stock",
        "next_week_predictions": "Next week predictions",
        "no_suggestions": "No suggestions now",
        "stock_alerts": "Stock alerts",
        "dashboard": "Dashboard",
        "inventory": "Inventory",
        "ingredients": "Ingredients",
        "purchases": "Purchases",
        "menu": "Menu",
        "catalog": "Catalog",
        "sales": "Sales",
        "reports": "Reports",
        "forecast": "Forecast",
        "logout": "Logout",
        "powered_by": "Powered by Aurora Tech — exclusive use by Aurora Tech clients",
        "register_title": "Create account",
        "register_subtitle": "Fill in the fields below to start using PrevSuite.",
        "register_name_label": "Full name",
        "register_email_label": "Email",
        "register_phone_label": "Phone (optional)",
        "register_password_label": "Password",
        "register_confirm_password_label": "Confirm password",
        "register_button": "Create account",
        "register_login_link": "Already have an account? Sign in",
        "forgot_password_title": "Reset password",
        "forgot_password_subtitle": "Enter your email and choose a new password to access PrevSuite.",
        "forgot_password_email_label": "Registered email",
        "forgot_password_new_password_label": "New password",
        "forgot_password_confirm_password_label": "Confirm new password",
        "forgot_password_button": "Change password now",
        "forgot_password_back_to_login": "Back to login",
    },
    "es": {
        "login_title": "Iniciar sesión",
        "login_welcome": "Accede para gestionar inventario, ventas y pronósticos con IA.",
        "email": "Correo",
        "password": "Contraseña",
        "remember_me": "Recordarme",
        "enter": "Entrar",
        "forgot_password": "¿Olvidaste tu contraseña?",
        "create_free": "Crear cuenta gratuita",
        # [MOD] alinhado com PT/EN e PrevSuite
        "hero_title": "Pronóstico de demanda con IA con PrevSuite!",
        "hero_sub": "Informes, Inventario y Pronóstico con IA",
        "weekly_sales": "Ventas semanales",
        "weekly_revenue": "Ingresos semanales",
        "low_stock_items": "Ítems con poco stock",
        "out_of_stock_items": "Ítems sin stock",
        "welcome_banner_title": "¡Bienvenido a Prev Suite!",
        "welcome_banner_sub": "Configura tu inventario para comenzar",
        "manage_stock": "Administrar stock",
        "next_week_predictions": "Predicciones de la próxima semana",
        "no_suggestions": "Sin sugerencias por ahora",
        "stock_alerts": "Alertas de stock",
        "dashboard": "Panel",
        "inventory": "Inventario",
        "ingredients": "Ingredientes",
        "purchases": "Compras",
        "menu": "Menú",
        "catalog": "Catálogo",
        "sales": "Ventas",
        "reports": "Informes",
        "forecast": "Pronóstico",
        "logout": "Salir",
        "powered_by": "Powered by Aurora Tech — uso exclusivo de clientes de Aurora Tech",
        "register_title": "Crear cuenta",
        "register_subtitle": "Complete los campos para comenzar a usar PrevSuite.",
        "register_name_label": "Nombre completo",
        "register_email_label": "Correo electrónico",
        "register_phone_label": "Teléfono (opcional)",
        "register_password_label": "Contraseña",
        "register_confirm_password_label": "Confirmar contraseña",
        "register_button": "Crear cuenta",
        "register_login_link": "¿Ya tienes cuenta? Iniciar sesión",
        "forgot_password_title": "Recuperar contraseña",
        "forgot_password_subtitle": "Ingrese su correo y elija una nueva contraseña para acceder a PrevSuite.",
        "forgot_password_email_label": "Correo registrado",
        "forgot_password_new_password_label": "Nueva contraseña",
        "forgot_password_confirm_password_label": "Confirmar nueva contraseña",
        "forgot_password_button": "Cambiar contraseña ahora",
        "forgot_password_back_to_login": "Volver al inicio de sesión",
    }
}

def get_locale():
    return session.get("lang", "pt")

def t(key: str) -> str:
    return TRANSLATIONS.get(get_locale(), {}).get(key, key)

# -------------------------------------------------
# Feature flags por tipo de estabelecimento
# -------------------------------------------------
# possíveis valores: restaurante, roupas, mercado, outros
FEATURES_BY_BUSINESS = {
    "restaurante": {
        "dashboard", "inventory", "ingredients", "purchases", "menu", "sales", "reports", "forecast"
    },
    "roupas": {
        "dashboard", "inventory", "catalog", "sales", "reports", "forecast"
    },
    "mercado": {
        "dashboard", "inventory", "purchases", "sales", "reports", "forecast"
    },
    "outros": {
        "dashboard", "inventory", "sales", "reports", "forecast"
    }
}

def get_features_for(user):
    tipo = getattr(user, "tipo_estabelecimento", None) or "outros"
    return FEATURES_BY_BUSINESS.get(tipo, FEATURES_BY_BUSINESS["outros"])

# -------------------------------------------------
# Decorador de login (ajustado para usar usuario_id
# e o blueprint auth_bp.login)                     # [MOD bloco]
# -------------------------------------------------
def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        # [MOD] antes: session.get("user_id")
        if not session.get("usuario_id"):
            # [MOD] antes: url_for("auth.login", ...)
            return redirect(url_for("auth_bp.login", next=request.path))
        return view(**kwargs)
    return wrapped_view

# -------------------------------------------------
# Contexto comum nos templates
# (atualmente não está sendo registrado em create_app,
# mas mantido por compatibilidade se você quiser usar) # [INFO]
# -------------------------------------------------
def inject_template_globals(app):
    @app.context_processor
    def _inject():
        user = getattr(g, "current_user", None)
        feats = get_features_for(user) if user else set()
        return {
            "t": t,
            "current_lang": get_locale(),
            "features": feats,
            "now": datetime.utcnow(),
        }
