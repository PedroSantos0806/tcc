from flask import session

I18N = {
    "pt": {
        "Dashboard":"Dashboard","Menu":"Menu","Stock":"Estoque","Shopping List":"Lista de Compras",
        "Reports":"Relatórios","Logout":"Sair","Sign in":"Entrar","Email":"E-mail","Password":"Senha",
        "Remember me":"Lembrar de mim","Forgot password?":"Esqueceu a senha?","Create free account":"Criar conta gratuita",
        "Real demand forecasting":"Previsão de Demanda de verdade",
        "Login subtitle":"Acesse sua conta para gerenciar estoque, vendas e previsões com IA.",
        "Trusted line":"Relatórios, Estoque e Previsão com IA",
        "Sign up":"Criar conta","Name":"Nome","Business Type":"Tipo de estabelecimento",
        "Restaurant":"Restaurante / Lanchonete","Retail":"Varejo (moda, calçados, etc.)","Bakery":"Padaria / Confeitaria",
        "Pharmacy":"Farmácia","Market":"Mercado / Mercearia","Other":"Outro","Preferred Language":"Idioma preferido",
        "Portuguese":"Português (Brasil)","English":"Inglês","Spanish":"Espanhol","Save and continue":"Salvar e continuar",
        "Profile saved":"Preferências salvas!","Have account?":"Já tem conta?","Sign in now":"Entrar agora",
        "Weekly sales":"Vendas desta Semana","Weekly revenue":"Receita da Semana",
        "Low stock items":"Itens com Estoque Baixo","Out of stock items":"Itens em Falta",
        "Welcome to PrevFood!":"Bem-vindo ao PrevFood!","Start setup text":"Comece configurando seu menu e ingredientes para rastrear estoque e gerar predições inteligentes.",
        "Configure Menu":"Configurar Menu","Manage Stock":"Gerenciar Estoque",
        "Next week predictions":"Predições da Próxima Semana","Stock alerts":"Alertas de Estoque",
        "Category":"Categoria","All":"Todas","Products":"Produtos","Items":"Itens","Cost value":"Valor de Custo","Sale value":"Valor de Venda",
        "Status":"Status","Sold %":"% Vendido","In stock":"Em estoque","Unit cost":"Custo Unit","Unit price":"Preço Unit",
        "OK":"OK","Low":"Baixo","Days":"dias",
        "Safety Margin (%)":"Margem de Segurança (%)","Horizon (days)":"Horizonte (dias)","Recalculate":"Recalcular",
        "No suggestions now":"Sem itens sugeridos no momento.","Total Items":"Total de Itens","Estimated Cost":"Custo Estimado","Margin":"Margem",
        "Ingredient":"Ingrediente","Unit":"Unidade","Suggested Qty":"Qtd Sugerida","Est. Cost":"Custo Estimado",
        "Total Sales":"Total de Vendas","Revenue (sold items)":"Receita (itens vendidos)","Total Cost":"Custo Total","Estimated Profit":"Lucro Estimado",
        "Ingredient usage (last 4 weeks)":"Uso de Ingredientes (últimas 4 semanas)","Financial Dashboard":"Dashboard Financeiro",
      },
    "en": {
        "Dashboard":"Dashboard","Menu":"Menu","Stock":"Stock","Shopping List":"Shopping List",
        "Reports":"Reports","Logout":"Logout","Sign in":"Sign in","Email":"Email","Password":"Password",
        "Remember me":"Remember me","Forgot password?":"Forgot password?","Create free account":"Create free account",
        "Real demand forecasting":"Real demand forecasting",
        "Login subtitle":"Access your account to manage inventory, sales and AI forecasts.",
        "Trusted line":"Reports, Inventory and AI Forecasting",
        "Sign up":"Create account","Name":"Name","Business Type":"Business type",
        "Restaurant":"Restaurant / Diner","Retail":"Retail (fashion, shoes, etc.)","Bakery":"Bakery / Pastry",
        "Pharmacy":"Pharmacy","Market":"Grocery / Market","Other":"Other","Preferred Language":"Preferred language",
        "Portuguese":"Portuguese (Brazil)","English":"English","Spanish":"Spanish","Save and continue":"Save and continue",
        "Profile saved":"Preferences saved!","Have account?":"Already have an account?","Sign in now":"Sign in now",
        "Weekly sales":"Sales this Week","Weekly revenue":"Revenue this Week",
        "Low stock items":"Low stock items","Out of stock items":"Out of stock items",
        "Welcome to PrevFood!":"Welcome to PrevFood!","Start setup text":"Start by configuring your menu and ingredients to track stock and get smart predictions.",
        "Configure Menu":"Configure Menu","Manage Stock":"Manage Stock",
        "Next week predictions":"Next week predictions","Stock alerts":"Stock alerts",
        "Category":"Category","All":"All","Products":"Products","Items":"Items","Cost value":"Cost value","Sale value":"Sale value",
        "Status":"Status","Sold %":"Sold %","In stock":"In stock","Unit cost":"Unit cost","Unit price":"Unit price",
        "OK":"OK","Low":"Low","Days":"days",
        "Safety Margin (%)":"Safety Margin (%)","Horizon (days)":"Horizon (days)","Recalculate":"Recalculate",
        "No suggestions now":"No suggestions now.","Total Items":"Total Items","Estimated Cost":"Estimated Cost","Margin":"Margin",
        "Ingredient":"Ingredient","Unit":"Unit","Suggested Qty":"Suggested Qty","Est. Cost":"Est. Cost",
        "Total Sales":"Total Sales","Revenue (sold items)":"Revenue (sold items)","Total Cost":"Total Cost","Estimated Profit":"Estimated Profit",
        "Ingredient usage (last 4 weeks)":"Ingredient usage (last 4 weeks)","Financial Dashboard":"Financial Dashboard",
      },
    "es": {
        "Dashboard":"Panel","Menu":"Menú","Stock":"Inventario","Shopping List":"Lista de Compras",
        "Reports":"Informes","Logout":"Salir","Sign in":"Iniciar sesión","Email":"Correo","Password":"Contraseña",
        "Remember me":"Recordarme","Forgot password?":"¿Olvidó la contraseña?","Create free account":"Crear cuenta gratis",
        "Real demand forecasting":"Pronóstico de demanda real",
        "Login subtitle":"Accede para gestionar inventario, ventas y pronósticos con IA.",
        "Trusted line":"Informes, Inventario y Pronóstico con IA",
        "Sign up":"Crear cuenta","Name":"Nombre","Business Type":"Tipo de negocio",
        "Restaurant":"Restaurante / Cafetería","Retail":"Retail (moda, calzado, etc.)","Bakery":"Panadería / Pastelería",
        "Pharmacy":"Farmacia","Market":"Mercado / Tienda","Other":"Otro","Preferred Language":"Idioma preferido",
        "Portuguese":"Portugués (Brasil)","English":"Inglés","Spanish":"Español","Save and continue":"Guardar y continuar",
        "Profile saved":"¡Preferencias guardadas!","Have account?":"¿Ya tienes cuenta?","Sign in now":"Iniciar ahora",
        "Weekly sales":"Ventas de esta Semana","Weekly revenue":"Ingresos de la Semana",
        "Low stock items":"Artículos con bajo stock","Out of stock items":"Artículos agotados",
        "Welcome to PrevFood!":"¡Bienvenido a PrevFood!","Start setup text":"Empieza configurando tu menú e ingredientes para control y predicciones.",
        "Configure Menu":"Configurar Menú","Manage Stock":"Gestionar Inventario",
        "Next week predictions":"Predicciones de la próxima semana","Stock alerts":"Alertas de inventario",
        "Category":"Categoría","All":"Todas","Products":"Productos","Items":"Ítems","Cost value":"Valor de Costo","Sale value":"Valor de Venta",
        "Status":"Estado","Sold %":"% Vendido","In stock":"En stock","Unit cost":"Costo Unit","Unit price":"Precio Unit",
        "OK":"OK","Low":"Bajo","Days":"días",
        "Safety Margin (%)":"Margen de Seguridad (%)","Horizon (days)":"Horizonte (días)","Recalculate":"Recalcular",
        "No suggestions now":"Sin sugerencias por ahora.","Total Items":"Total de Ítems","Estimated Cost":"Costo Estimado","Margin":"Margen",
        "Ingredient":"Ingrediente","Unit":"Unidad","Suggested Qty":"Cant. sugerida","Est. Cost":"Costo Est.",
        "Total Sales":"Ventas Totales","Revenue (sold items)":"Ingresos (ítems vendidos)","Total Cost":"Costo Total","Estimated Profit":"Beneficio Estimado",
        "Ingredient usage (last 4 weeks)":"Uso de ingredientes (últimas 4 semanas)","Financial Dashboard":"Panel Financiero",
      }
}

def get_lang():
    try:
        return session.get("lang", "pt")
    except Exception:
        return "pt"

def t(key: str) -> str:
    lang = get_lang()
    return I18N.get(lang, I18N["pt"]).get(key, key)

def inject_i18n(app):
    @app.context_processor
    def _ctx():
        return {"t": t, "lang": get_lang}
