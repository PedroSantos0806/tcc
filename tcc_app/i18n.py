from flask import session

I18N = {
    "pt": {
        # Navegação / comuns
        "Dashboard": "Dashboard",
        "Menu": "Menu",
        "Stock": "Estoque",
        "Shopping List": "Lista de Compras",
        "Reports": "Relatórios",
        "Forecast": "Previsão",
        "Logout": "Sair",

        "Sign in": "Entrar",
        "Email": "E-mail",
        "Password": "Senha",
        "Remember me": "Lembrar de mim",
        "Forgot password?": "Esqueceu a senha?",
        "Create free account": "Criar conta gratuita",
        "Or": "ou",
        "Start now": "Começar agora",
        "See demo": "Ver demo",

        "Real demand forecasting": "Previsão de Demanda de verdade",
        "Login subtitle": "Acesse sua conta para gerenciar estoque, vendas e previsões com IA.",
        "Trusted line": "Relatórios, Estoque e Previsão com IA",

        # Cadastro / Onboarding
        "Sign up": "Criar conta",
        "Name": "Nome",
        "Full name": "Nome completo",
        "Business Type": "Tipo de estabelecimento",
        "Restaurant": "Restaurante / Lanchonete",
        "Retail": "Varejo (moda, calçados, etc.)",
        "Bakery": "Padaria / Confeitaria",
        "Pharmacy": "Farmácia",
        "Market": "Mercado / Mercearia",
        "Other": "Outro",
        "Preferred Language": "Idioma preferido",
        "Language": "Idioma",
        "Portuguese": "Português (Brasil)",
        "English": "Inglês",
        "Spanish": "Espanhol",
        "Save and continue": "Salvar e continuar",
        "Profile saved": "Preferências salvas!",
        "Have account?": "Já tem conta?",
        "Sign in now": "Entrar agora",

        "Onboarding Title": "Conte sobre o seu negócio",
        "Onboarding Subtitle": "Personalizamos o PrevSuite conforme seu segmento.",

        # Texto marketing cadastro
        "Create account hero title": "Previsão de demanda com IA com PrevSuite!",
        "Create account hero subtitle": "Cadastre sua conta e comece a controlar estoque, vendas e previsões de forma simples e visual.",
        "Create account bullet 1": "✔ Acompanhe vendas e estoque em tempo real;",
        "Create account bullet 2": "✔ Veja quais produtos mais vendem e quais estão encalhados;",
        "Create account bullet 3": "✔ Use previsões com IA para planejar compras e reduzir desperdício.",
        "It takes less than 2 minutes": "Leva menos de 2 minutos para começar.",

        # Dashboard / KPIs
        "Weekly sales": "Vendas desta Semana",
        "Weekly revenue": "Receita da Semana",
        "Low stock items": "Itens com Estoque Baixo",
        "Out of stock items": "Itens em Falta",

        "Start setup text": "Comece configurando seu estoque e suas categorias.",
        "Configure Menu": "Configurar Cardápio",
        "Manage Stock": "Gerenciar Estoque",
        "Next week predictions": "Previsões para a próxima semana",
        "No suggestions now": "Sem sugestões no momento",
        "Stock alerts": "Alertas de estoque",

        # Estoque / Produtos
        "Products": "Produtos",
        "Product": "Produto",
        "Category": "Categoria",
        "Unit price": "Preço Unit",
        "Unit cost": "Custo Unit",
        "Items": "Itens",
        "Sold %": "% Vendido",
        "In stock": "Em estoque",
        "Status": "Status",
        "OK": "OK",
        "Low": "Baixo",

        # Previsão
        "All": "Todas",
        "Days": "dias",
        "History and Forecast": "Histórico e Previsão",

        # Lista de Compras
        "Safety Margin (%)": "Margem de Segurança (%)",
        "Horizon (days)": "Horizonte (dias)",
        "Recalculate": "Recalcular",
        "Total Items": "Total de Itens",
        "Estimated Cost": "Custo Estimado",
        "Margin": "Margem",
        "Ingredient": "Item",
        "Unit": "Unidade",
        "Suggested Qty": "Qtd Sugerida",
        "Est. Cost": "Custo Estimado",

        # Registrar venda
        "Register Sale": "Registrar venda",
        "Sale date": "Data da venda",
        "Select...": "Selecione...",
        "Quantity": "Quantidade",
        "Add Item": "Adicionar item",
        "Save": "Salvar",

        # Produtos / menu lateral
        "Register Product": "Cadastrar produto",

        # Esqueci senha / reset
        "Reset password": "Redefinir senha",
        "Reset password subtitle": "Informe seu e-mail e defina uma nova senha.",
        "New password": "Nova senha",
        "Confirm new password": "Confirmar nova senha",
        "Change password": "Alterar senha",
        "Back to login": "Voltar ao login",

        # Relatórios
        "Reports subtitle": "Visão geral das vendas, custos e itens mais utilizados.",
        "Total sales": "Total de vendas",
        "Revenue (sold items)": "Receita (itens vendidos)",
        "Total cost": "Custo total",
        "Estimated profit": "Lucro estimado",
        "Usage last 28 days": "Uso de itens nos últimos 28 dias",
        "Usage subtitle": "Lista dos produtos mais utilizados, com quantidade total e custo associado.",
        "Cost": "Custo",
        "No data for reports": "Ainda não há dados suficientes para montar os relatórios.",

        # Outros
        "Financial Dashboard": "Dashboard Financeiro",
    },
    "en": {
        "Dashboard": "Dashboard",
        "Menu": "Menu",
        "Stock": "Stock",
        "Shopping List": "Shopping List",
        "Reports": "Reports",
        "Forecast": "Forecast",
        "Logout": "Logout",

        "Sign in": "Sign in",
        "Email": "Email",
        "Password": "Password",
        "Remember me": "Remember me",
        "Forgot password?": "Forgot password?",
        "Create free account": "Create free account",
        "Or": "or",
        "Start now": "Start now",
        "See demo": "See demo",

        "Real demand forecasting": "Real demand forecasting",
        "Login subtitle": "Access your account to manage inventory, sales and AI forecasts.",
        "Trusted line": "Reports, Inventory and AI Forecasting",

        "Sign up": "Create account",
        "Name": "Name",
        "Full name": "Full name",
        "Business Type": "Business type",
        "Restaurant": "Restaurant / Diner",
        "Retail": "Retail (fashion, shoes, etc.)",
        "Bakery": "Bakery / Pastry",
        "Pharmacy": "Pharmacy",
        "Market": "Grocery / Market",
        "Other": "Other",
        "Preferred Language": "Preferred language",
        "Language": "Language",
        "Portuguese": "Portuguese (Brazil)",
        "English": "English",
        "Spanish": "Spanish",
        "Save and continue": "Save and continue",
        "Profile saved": "Preferences saved!",
        "Have account?": "Already have an account?",
        "Sign in now": "Sign in now",

        "Onboarding Title": "Tell us about your business",
        "Onboarding Subtitle": "We personalize PrevSuite by your segment.",

        "Create account hero title": "AI-powered demand forecasting with PrevSuite!",
        "Create account hero subtitle": "Create your account and start managing inventory, sales and forecasts in a simple, visual way.",
        "Create account bullet 1": "✔ Track sales and stock in real time;",
        "Create account bullet 2": "✔ See which products sell more and which are stuck;",
        "Create account bullet 3": "✔ Use AI forecasts to plan purchases and reduce waste.",
        "It takes less than 2 minutes": "It takes less than 2 minutes to get started.",

        "Weekly sales": "Weekly sales",
        "Weekly revenue": "Weekly revenue",
        "Low stock items": "Low stock items",
        "Out of stock items": "Out of stock items",

        "Start setup text": "Start by setting up your inventory and categories.",
        "Configure Menu": "Configure Menu",
        "Manage Stock": "Manage Stock",
        "Next week predictions": "Next week predictions",
        "No suggestions now": "No suggestions now.",
        "Stock alerts": "Stock alerts",

        "Products": "Products",
        "Product": "Product",
        "Category": "Category",
        "Unit price": "Unit price",
        "Unit cost": "Unit cost",
        "Items": "Items",
        "Sold %": "Sold %",
        "In stock": "In stock",
        "Status": "Status",
        "OK": "OK",
        "Low": "Low",

        "All": "All",
        "Days": "days",
        "History and Forecast": "History and Forecast",

        "Safety Margin (%)": "Safety Margin (%)",
        "Horizon (days)": "Horizon (days)",
        "Recalculate": "Recalculate",
        "Total Items": "Total Items",
        "Estimated Cost": "Estimated Cost",
        "Margin": "Margin",
        "Ingredient": "Item",
        "Unit": "Unit",
        "Suggested Qty": "Suggested Qty",
        "Est. Cost": "Est. Cost",

        "Register Sale": "Register sale",
        "Sale date": "Sale date",
        "Select...": "Select...",
        "Quantity": "Quantity",
        "Add Item": "Add item",
        "Save": "Save",

        "Register Product": "Register product",

        "Reset password": "Reset password",
        "Reset password subtitle": "Enter your email and set a new password.",
        "New password": "New password",
        "Confirm new password": "Confirm new password",
        "Change password": "Change password",
        "Back to login": "Back to login",

        "Reports subtitle": "Overview of sales, costs and most used items.",
        "Total sales": "Total sales",
        "Revenue (sold items)": "Revenue (sold items)",
        "Total cost": "Total cost",
        "Estimated profit": "Estimated profit",
        "Usage last 28 days": "Usage of items in the last 28 days",
        "Usage subtitle": "List of the most used products, with total quantity and associated cost.",
        "Cost": "Cost",
        "No data for reports": "Not enough data to build the reports yet.",

        "Financial Dashboard": "Financial Dashboard",
    },
    "es": {
        "Dashboard": "Panel",
        "Menu": "Menú",
        "Stock": "Inventario",
        "Shopping List": "Lista de Compras",
        "Reports": "Informes",
        "Forecast": "Pronóstico",
        "Logout": "Salir",

        "Sign in": "Iniciar sesión",
        "Email": "Correo",
        "Password": "Contraseña",
        "Remember me": "Recordarme",
        "Forgot password?": "¿Olvidó la contraseña?",
        "Create free account": "Crear cuenta gratis",
        "Or": "o",
        "Start now": "Empezar ahora",
        "See demo": "Ver demo",

        "Real demand forecasting": "Pronóstico de demanda real",
        "Login subtitle": "Accede para gestionar inventario, ventas y pronósticos con IA.",
        "Trusted line": "Informes, Inventario y Pronóstico con IA",

        "Sign up": "Crear cuenta",
        "Name": "Nombre",
        "Full name": "Nombre completo",
        "Business Type": "Tipo de negocio",
        "Restaurant": "Restaurante / Cafetería",
        "Retail": "Retail (moda, calzado, etc.)",
        "Bakery": "Panadería / Pastelería",
        "Pharmacy": "Farmacia",
        "Market": "Mercado / Tienda",
        "Other": "Otro",
        "Preferred Language": "Idioma preferido",
        "Language": "Idioma",
        "Portuguese": "Portugués (Brasil)",
        "English": "Inglés",
        "Spanish": "Español",
        "Save and continue": "Guardar y continuar",
        "Profile saved": "¡Preferencias guardadas!",
        "Have account?": "¿Ya tienes cuenta?",
        "Sign in now": "Iniciar ahora",

        "Onboarding Title": "Cuéntanos sobre tu negocio",
        "Onboarding Subtitle": "Personalizamos PrevSuite según tu segmento.",

        "Create account hero title": "Pronóstico de demanda con IA con PrevSuite!",
        "Create account hero subtitle": "Crea tu cuenta y gestiona inventario, ventas y pronósticos de forma simple y visual.",
        "Create account bullet 1": "✔ Acompaña ventas e inventario en tiempo real;",
        "Create account bullet 2": "✔ Ve qué productos venden más y cuáles están parados;",
        "Create account bullet 3": "✔ Usa pronósticos con IA para planear compras y reducir desperdicio.",
        "It takes less than 2 minutes": "Toma menos de 2 minutos para empezar.",

        "Weekly sales": "Ventas semanales",
        "Weekly revenue": "Ingresos semanales",
        "Low stock items": "Ítems con poco stock",
        "Out of stock items": "Ítems sin stock",

        "Start setup text": "Comienza configurando tu inventario y categorías.",
        "Configure Menu": "Configurar Menú",
        "Manage Stock": "Administrar Inventario",
        "Next week predictions": "Predicciones de la próxima semana",
        "No suggestions now": "Sin sugerencias por ahora.",
        "Stock alerts": "Alertas de inventario",

        "Products": "Productos",
        "Product": "Producto",
        "Category": "Categoría",
        "Unit price": "Precio unitario",
        "Unit cost": "Costo unitario",
        "Items": "Ítems",
        "Sold %": "% Vendido",
        "In stock": "En stock",
        "Status": "Estado",
        "OK": "OK",
        "Low": "Bajo",

        "All": "Todas",
        "Days": "días",
        "History and Forecast": "Histórico y Pronóstico",

        "Safety Margin (%)": "Margen de Seguridad (%)",
        "Horizon (days)": "Horizonte (días)",
        "Recalculate": "Recalcular",
        "Total Items": "Total de Ítems",
        "Estimated Cost": "Costo Estimado",
        "Margin": "Margen",
        "Ingredient": "Ítem",
        "Unit": "Unidad",
        "Suggested Qty": "Cant. sugerida",
        "Est. Cost": "Costo Est.",

        "Register Sale": "Registrar venta",
        "Sale date": "Fecha de la venta",
        "Select...": "Seleccione...",
        "Quantity": "Cantidad",
        "Add Item": "Agregar ítem",
        "Save": "Guardar",

        "Register Product": "Registrar producto",

        "Reset password": "Restablecer contraseña",
        "Reset password subtitle": "Ingresa tu correo y define una nueva contraseña.",
        "New password": "Nueva contraseña",
        "Confirm new password": "Confirmar nueva contraseña",
        "Change password": "Cambiar contraseña",
        "Back to login": "Volver al inicio de sesión",

        "Reports subtitle": "Visión general de ventas, costos y ítems más utilizados.",
        "Total sales": "Total de ventas",
        "Revenue (sold items)": "Ingresos (ítems vendidos)",
        "Total cost": "Costo total",
        "Estimated profit": "Beneficio estimado",
        "Usage last 28 days": "Uso de ítems en los últimos 28 días",
        "Usage subtitle": "Lista de los productos más utilizados, con cantidad total y costo asociado.",
        "Cost": "Costo",
        "No data for reports": "Todavía no hay datos suficientes para generar los informes.",

        "Financial Dashboard": "Panel Financiero",
    }
}

def get_lang():
    try:
        return session.get("lang", "pt")
    except Exception:
        return "pt"

def t(key: str) -> str:
    key = str(key or "").strip()
    lang = get_lang()
    return I18N.get(lang, I18N["pt"]).get(key, key)

def inject_i18n(app):
    @app.context_processor
    def _ctx():
        return {"t": t, "lang": get_lang()}
