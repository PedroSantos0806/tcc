# tcc_app/utils.py
from functools import wraps
from flask import session, redirect, url_for, request, g
from datetime import datetime

# -------------------------------------------------
# Idioma / i18n bem leve para templates
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
        "hero_title": "Previsão de Demanda de verdade",
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
        "hero_title": "True Demand Forecasting",
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
        "hero_title": "Pronóstico de Demanda real",
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
# Decorador de login (já existia; mantido)
# -------------------------------------------------
def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if not session.get("user_id"):
            return redirect(url_for("auth.login", next=request.path))
        return view(**kwargs)
    return wrapped_view

# -------------------------------------------------
# Contexto comum nos templates
# (chamado no app/__init__.py ou no blueprint principal)
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
