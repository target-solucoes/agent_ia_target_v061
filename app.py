"""
Aplicação Streamlit Refatorada - Target AI Agent v0.61
Reduzido de 1468 para aproximadamente 300 linhas
"""

import streamlit as st
import pandas as pd
import json
import time
import sys
import re
from typing import Dict, Optional

sys.path.append("src")

# Importar módulos refatorados
from src.utils.data_loaders import load_parquet_data, initialize_agent
from src.utils.formatters import format_context_for_display, format_sql_query, escape_currency_for_markdown
from src.filters.ui.sidebar import (
    filter_user_friendly_context,
    create_enhanced_filter_manager
)
from src.filters.core.manager import get_json_filter_manager
from src.visualization.plotly_charts import render_plotly_visualization

# Page configuration
st.set_page_config(page_title="Agente IA Target v0.61", page_icon="🤖", layout="wide")


def main():
    """Função principal da aplicação"""
    # Initialize CSS and header
    _setup_page_styling()
    _render_header()

    # Load data and initialize agent
    df, data_error = load_parquet_data()
    if data_error:
        st.error(f" {data_error}")
        st.stop()

    agent, df_agent, agent_error = initialize_agent()
    if agent_error:
        st.error(f" {agent_error}")
        st.stop()

    # Main application interface
    _render_main_interface(agent, df)

    # Company footer
    _render_footer()


def _setup_page_styling():
    """Configura CSS personalizado com design moderno e minimalista"""
    st.markdown("""
    <style>
    .main > div {
        padding-top: 1rem;
    }

    /* Header Styling */
    .header-container {
        background: linear-gradient(135deg, #1a2332 0%, #2d3e50 100%);
        padding: 2rem 0;
        margin: -1rem -1rem 2rem -1rem;
        border-radius: 0 0 20px 20px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        text-align: center;
    }

    .app-title {
        color: white !important;
        font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
        font-size: 2.5rem;
        font-weight: 300;
        margin: 0;
        letter-spacing: 2px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }

    .app-subtitle {
        color: white !important;
        font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
        font-size: 1rem;
        font-weight: 300;
        margin: 0.5rem 0 0 0;
        letter-spacing: 1px;
        opacity: 0.95;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
    }

    .app-description {
        color: rgba(255,255,255,0.8);
        font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
        font-size: 0.9rem;
        font-weight: 300;
        margin: 1rem 0 0 0;
        max-width: 600px;
        margin-left: auto;
        margin-right: auto;
        line-height: 1.5;
    }

    .feature-icons {
        display: flex;
        justify-content: center;
        gap: 2rem;
        margin-top: 1.5rem;
        flex-wrap: wrap;
    }

    .feature-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        color: rgba(255,255,255,0.7);
        font-size: 0.8rem;
        font-weight: 300;
    }

    .feature-icon {
        font-size: 1.5rem;
        margin-bottom: 0.5rem;
        opacity: 0.8;
    }

    /* Chat Container Styling */
    .chat-main-container {
        display: flex;
        flex-direction: column;
        margin: 2rem 0;
    }

    .chat-messages-container {
        padding: 1rem;
        margin-bottom: 1rem;
        border-radius: 15px;
        border: 1px solid var(--secondary-background-color);
    }

    .chat-input-container {
        padding: 1.5rem 0;
        margin-top: 1rem;
        border-top: 1px solid var(--secondary-background-color);
    }

    /* Chat Message Styling - Dark mode friendly */
    .stChatMessage {
        border-radius: 15px;
        padding: 1.2rem;
        margin: 0.8rem 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        border: 1px solid var(--secondary-background-color);
    }

    .stChatMessage[data-testid="user-message"] {
        background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%) !important;
        color: white !important;
        margin-left: 2rem;
    }

    .stChatMessage[data-testid="assistant-message"] {
        border-left: 4px solid #e74c3c;
        margin-right: 2rem;
    }

    /* Chat Input Styling - Dark mode friendly */
    .stChatInputContainer {
        border: none !important;
        padding: 0 !important;
        margin: 0 !important;
        background: transparent;
    }

    .stChatInput > div {
        border-radius: 25px !important;
        border: 2px solid #e74c3c !important;
    }

    .stChatInput input {
        border: none !important;
        font-size: 1rem !important;
        padding: 1rem 1.5rem !important;
    }

    /* Welcome message styling - Dark mode friendly */
    .welcome-message {
        text-align: center;
        padding: 3rem 2rem;
        font-style: italic;
        border-radius: 15px;
        margin: 2rem 0;
        border: 2px dashed var(--secondary-background-color);
    }

    .welcome-message h3 {
        color: #e74c3c;
        margin-bottom: 1rem;
    }

    /* Button Styling */
    .stButton > button {
        background: linear-gradient(135deg, #6c757d 0%, #5a6268 100%);
        color: white;
        border: none;
        border-radius: 20px;
        padding: 0.4rem 0.8rem;
        font-weight: 400;
        font-size: 0.85rem;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(108, 117, 125, 0.3);
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, #5a6268 0%, #495057 100%);
        transform: translateY(-1px);
        box-shadow: 0 3px 12px rgba(108, 117, 125, 0.4);
    }

    .stButton > button:active {
        transform: translateY(0px);
    }

    /* Debug mode toggle styling */
    .stToggle > div {
        background-color: transparent !important;
    }

    .stToggle > div > div {
        background-color: #f0f0f0 !important;
        border-radius: 20px !important;
    }

    .stToggle > div > div[data-checked="true"] {
        background-color: #e74c3c !important;
    }

    /* Debug section styling */
    .debug-section {
        background-color: rgba(231, 76, 60, 0.05);
        border: 1px solid rgba(231, 76, 60, 0.2);
        border-radius: 10px;
        padding: 1rem;
        margin-top: 1rem;
    }

    .debug-title {
        color: #e74c3c;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }

    /* Filter Management Styling */
    .filter-checkbox {
        margin-right: 0.5rem !important;
        margin-bottom: 0.5rem !important;
    }

    .filter-item {
        display: flex;
        align-items: center;
        margin-bottom: 0.5rem;
        padding: 0.25rem 0;
    }

    .filter-text {
        flex: 1;
        margin-left: 0.5rem;
    }

    .disabled-filter {
        opacity: 0.6;
        text-decoration: line-through;
        color: var(--text-color-light, #666);
    }

    .enabled-filter {
        opacity: 1;
        text-decoration: none;
    }

    /* Sidebar filter management styling */
    .stSidebar .stCheckbox {
        margin-bottom: 0.25rem !important;
    }

    .stSidebar .stCheckbox > div {
        margin-bottom: 0 !important;
    }

    .filter-category-header {
        font-weight: bold;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
        border-bottom: 1px solid var(--secondary-background-color);
        padding-bottom: 0.25rem;
    }

    .filter-status-info {
        font-size: 0.85rem;
        font-style: italic;
        padding: 0.5rem;
        margin-top: 0.5rem;
        border-radius: 5px;
        background: var(--secondary-background-color);
    }

    .reactivate-button {
        width: 100% !important;
        margin-top: 0.5rem !important;
    }

    /* Modern minimalist enhancements */
    .stApp {
        background-color: var(--background-color);
    }

    /* Enhanced sidebar styling - Light Mode */
    .stSidebar {
        background: #ffffff !important;
        border-right: 1px solid #e0e0e0;
    }

    .stSidebar > div {
        padding-top: 2rem;
    }

    /* Sidebar title styling */
    .stSidebar h2 {
        color: #2c3e50 !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        margin-bottom: 1rem !important;
        padding-bottom: 0.5rem !important;
        border-bottom: 2px solid #e74c3c !important;
    }

    /* Sidebar text styling for better readability */
    .stSidebar p,
    .stSidebar div,
    .stSidebar span {
        color: #2c3e50 !important;
        font-weight: 500 !important;
    }

    .stSidebar strong {
        color: #1a202c !important;
        font-weight: 700 !important;
    }

    .stSidebar .stMarkdown,
    .stSidebar .stMarkdown p,
    .stSidebar .stMarkdown div {
        color: #2c3e50 !important;
    }

    /* Sidebar checkbox and toggle styling */
    .stSidebar .stCheckbox label,
    .stSidebar .stToggle label {
        color: #2c3e50 !important;
        font-weight: 500 !important;
    }

    /* Sidebar expander styling */
    .stSidebar .stExpander summary {
        color: #2c3e50 !important;
        font-weight: 600 !important;
    }

    /* Enhanced expander styling */
    .stExpander {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }

    .stExpander > div > div {
        background-color: #f8f9fa;
        border-radius: 8px;
    }

    /* Code block improvements */
    .stCodeBlock {
        background-color: #f8f9fa;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
    }

    /* Metric improvements */
    .stMetric {
        background-color: rgba(255,255,255,0.8);
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border: 1px solid #e0e0e0;
    }

    /* Success message styling */
    .stSuccess {
        background-color: rgba(46, 204, 113, 0.1);
        border: 1px solid #2ecc71;
        border-radius: 8px;
        color: #27ae60;
    }

    /* Warning message styling */
    .stWarning {
        background-color: rgba(241, 196, 15, 0.1);
        border: 1px solid #f1c40f;
        border-radius: 8px;
        color: #f39c12;
    }

    /* Error message styling */
    .stError {
        background-color: rgba(231, 76, 60, 0.1);
        border: 1px solid #e74c3c;
        border-radius: 8px;
        color: #c0392b;
    }

    /* Modern card styling for containers */
    .card-container {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        border: 1px solid #e0e0e0;
    }

    /* Responsive adjustments */
    @media (max-width: 768px) {
        .app-title {
            font-size: 2rem;
        }
        .feature-icons {
            gap: 1rem;
        }
        .header-container {
            padding: 1.5rem 1rem;
        }
        .stChatMessage[data-testid="user-message"] {
            margin-left: 0.5rem;
        }
        .stChatMessage[data-testid="assistant-message"] {
            margin-right: 0.5rem;
        }
    }

    /* Sidebar separator styling */
    .stSidebar hr {
        border-color: #e0e0e0 !important;
        margin: 1rem 0 !important;
    }

    /* Universal sidebar text color override */
    .stSidebar,
    .stSidebar *,
    .stSidebar div,
    .stSidebar p,
    .stSidebar span,
    .stSidebar label,
    .stSidebar em {
        color: #2c3e50 !important;
    }

    .stSidebar div[data-testid="stMarkdownContainer"],
    .stSidebar div[data-testid="stMarkdownContainer"] *,
    .stSidebar .stMarkdown,
    .stSidebar .stMarkdown * {
        color: #2c3e50 !important;
    }

    /* Dark mode improvements */
    @media (prefers-color-scheme: dark) {
        .stSidebar {
            background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%) !important;
        }

        .stSidebar,
        .stSidebar *,
        .stSidebar div,
        .stSidebar p,
        .stSidebar span,
        .stSidebar label,
        .stSidebar em,
        .stSidebar h2 {
            color: #ecf0f1 !important;
        }

        .stSidebar strong {
            color: #ffffff !important;
        }

        .stSidebar div[data-testid="stMarkdownContainer"],
        .stSidebar div[data-testid="stMarkdownContainer"] *,
        .stSidebar .stMarkdown,
        .stSidebar .stMarkdown * {
            color: #ecf0f1 !important;
        }

        .stSidebar h2 {
            border-bottom: 2px solid #e74c3c !important;
        }

        .card-container {
            background: #34495e;
            border-color: #4a5a70;
        }
    }
    </style>
    """, unsafe_allow_html=True)


def _render_header():
    """Renderiza cabeçalho da aplicação com design profissional"""
    # Import selected_model from config
    try:
        from src.config.model_config import SELECTED_MODEL as selected_model
    except ImportError:
        selected_model = "gpt-5-nano-2025-08-07"  # Fallback

    # Enhanced Professional Header
    st.markdown(
        f"""
        <div class="header-container">
            <h1 class="app-title">🤖 AGENTE IA TARGET v0.61</h1>
            <p class="app-subtitle">INTELIGÊNCIA ARTIFICIAL PARA ANÁLISE DE DADOS</p>
            <p class="app-description">
                Converse naturalmente com seus dados comerciais. Faça perguntas em linguagem natural
                e obtenha insights precisos através de análise inteligente.<br>
                <small style="opacity: 0.7;">Modelo: {selected_model}</small>
            </p>
            <div class="feature-icons">
                <div class="feature-item">
                    <div class="feature-icon">💬</div>
                    <span>Chat Natural</span>
                </div>
                <div class="feature-item">
                    <div class="feature-icon">📊</div>
                    <span>Análise Rápida</span>
                </div>
                <div class="feature-item">
                    <div class="feature-icon">🎯</div>
                    <span>Insights Precisos</span>
                </div>
                <div class="feature-item">
                    <div class="feature-icon">🚀</div>
                    <span>Resultados Instantâneos</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_main_interface(agent, df):
    """Renderiza interface principal com layout otimizado"""
    # Sidebar configuration
    with st.sidebar:
        _render_sidebar(df)

    # Main content area with improved layout
    main_col1, main_col2, main_col3 = st.columns([0.5, 4, 0.5])

    with main_col2:
        # Main chat interface
        _render_chat_interface(agent)


def _render_sidebar(df):
    """Renderiza sidebar com informações e filtros"""
    st.markdown("## 📊 Informações do Dataset")
    st.markdown(f"**Registros totais:** {len(df):,}")
    st.markdown(f"**Período:** {df['Data'].min().strftime('%Y-%m-%d')} a {df['Data'].max().strftime('%Y-%m-%d')}")

    # Debug toggle
    debug_mode = st.toggle(
        "🔧 Modo Debug",
        value=st.session_state.get('debug_mode', False),
        help="Mostra queries SQL e informações técnicas"
    )
    st.session_state.debug_mode = debug_mode

    st.markdown("---")

    # Enhanced Filter management with new JSON system
    if 'last_context' in st.session_state and st.session_state.last_context:
        user_context = filter_user_friendly_context(st.session_state.last_context)
        create_enhanced_filter_manager(user_context, show_suggestions=True, df=df)

        # Removido: exibição da contagem de filtros ativos para simplificar interface
    else:
        create_enhanced_filter_manager({}, show_suggestions=False, df=df)


def _render_chat_interface(agent):
    """Renderiza interface de chat principal"""
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.last_context = {}

        # Add welcome message as first assistant message
        welcome_msg = """👋 Olá! Sou o **Agente IA Target**, seu assistente para análise de dados comerciais.

Estou aqui para ajudá-lo a explorar e entender seus dados através de conversas naturais. Você pode me fazer perguntas como:
- "Quais são os produtos mais vendidos?"
- "Mostre o faturamento por região"
- "Analise as tendências de vendas"

Como posso ajudá-lo hoje?"""
        st.session_state.messages.append(
            {"role": "assistant", "content": welcome_msg}
        )

    # Delete Chat button
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🗑️ Limpar", type="secondary"):
            # Clear all session state related to chat
            st.session_state.messages = []
            if "session_user_id" in st.session_state:
                del st.session_state.session_user_id

            # CORREÇÃO: Limpar cache do agente
            if "cached_agent" in st.session_state:
                del st.session_state.cached_agent
            if "cached_df_agent" in st.session_state:
                del st.session_state.cached_df_agent

            # Clear agent persistent context
            if agent is not None:
                if hasattr(agent, 'clear_persistent_context'):
                    agent.clear_persistent_context()
                elif hasattr(agent, 'persistent_context'):
                    agent.persistent_context = {}
            # Clear disabled filters
            if 'disabled_filters' in st.session_state:
                st.session_state.disabled_filters.clear()
            if 'last_context' in st.session_state:
                del st.session_state.last_context

            # Clear JSON filter manager state
            from src.filters.core.manager import reset_json_filter_manager
            reset_json_filter_manager()
            # Force app rerun to refresh everything
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant":
                _render_assistant_message(message)
            else:
                # CORREÇÃO: Escapar símbolos de moeda antes de renderizar
                st.markdown(escape_currency_for_markdown(message["content"]))

    # Chat input
    if prompt := st.chat_input("💬 Faça sua pergunta sobre os dados comerciais..."):
        _handle_user_input(prompt, agent)


def _render_assistant_message(message):
    """Renderiza mensagem do assistente com visualizações"""
    # SUBSTITUIÇÃO AUTOMÁTICA DE TABELAS (para mensagens históricas)
    content = message["content"]
    has_visualization = "visualization_data" in message and message["visualization_data"]

    if has_visualization:
        content = _extract_and_replace_tables(content, True)

    # INSERIR GRÁFICO NA POSIÇÃO CORRETA: Título → Contexto → Gráfico → Insights
    if has_visualization:
        # Separar título, contexto e insights do conteúdo
        title_part, context_part, insights_part = _split_title_and_content(content)

        # Renderizar: Título → Contexto → Gráfico → Insights/Próximos Passos
        # CORREÇÃO: Escapar símbolos de moeda antes de renderizar
        if title_part:
            st.markdown(escape_currency_for_markdown(title_part))
        if context_part:
            st.markdown(escape_currency_for_markdown(context_part))
        render_plotly_visualization(message["visualization_data"])
        if insights_part:
            st.markdown(escape_currency_for_markdown(insights_part))
    else:
        # Sem visualização: renderizar conteúdo normalmente
        # CORREÇÃO: Escapar símbolos de moeda antes de renderizar
        st.markdown(escape_currency_for_markdown(content))

    # Render debug info if available
    if "debug_info" in message and message["debug_info"] and st.session_state.get('debug_mode', False):
        _render_debug_info(message["debug_info"], message.get("context"))


def _render_debug_info(debug_info, message_context=None):
    """Renderiza informações de debug"""
    with st.expander("🔧 Informações de Debug", expanded=False):

        # SQL Queries
        if "sql_queries" in debug_info and debug_info["sql_queries"]:
            st.markdown("### 📝 Queries SQL Executadas")
            for i, query in enumerate(debug_info["sql_queries"], 1):
                st.markdown(f"**Query {i}:**")
                st.code(format_sql_query(query), language="sql")


        # Show JSON Filter Structure from processed response
        st.markdown("### 🎯 Filtros JSON Detectados")
        if message_context:
            filter_json = _build_intelligent_filter_json(message_context)
            # CORREÇÃO: Sempre exibir JSON, mesmo quando vazio
            if filter_json and any(v for category in filter_json.values() for v in (category.values() if isinstance(category, dict) else []) if v is not None and v != [] and v != ""):
                st.json(filter_json)
            else:
                st.json({"message": "Nenhum filtro detectado no contexto", "context_fields": list(message_context.keys()) if message_context else []})
        else:
            st.json({"message": "Contexto vazio - nenhum filtro ativo"})

        # Response timing
        if "response_time" in debug_info:
            st.markdown(f"### ⏱️ Tempo de Resposta: {debug_info['response_time']:.2f}s")


def _split_title_and_content(response_content: str) -> tuple:
    """
    Separa o título, contexto e insights do conteúdo de forma robusta.

    Args:
        response_content: Conteúdo completo da resposta

    Returns:
        tuple: (title_part, context_part, insights_part) onde:
               - title_part: Título (## Heading)
               - context_part: Contexto (texto após título até "### 💡 Principais Insights")
               - insights_part: Insights e Próximos Passos
    """
    lines = response_content.split('\n')
    title_end_idx = -1
    insights_start_idx = -1

    # PASSO 1: Procurar primeiro heading H2 (##) - TÍTULO
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('## ') and not stripped.startswith('###'):
            title_end_idx = i
            break

    # PASSO 2: Procurar seção de insights (### 💡 Principais Insights ou ### Principais Insights)
    for i, line in enumerate(lines):
        stripped = line.strip()
        # Detectar variações da seção de insights
        if (stripped.startswith('### 💡 Principais Insights') or
            stripped.startswith('### Principais Insights') or
            stripped.startswith('###💡 Principais Insights') or
            (stripped.startswith('### ') and 'Insights' in stripped)):
            insights_start_idx = i
            break

    # PASSO 3: Dividir conteúdo em 3 partes
    if title_end_idx >= 0 and insights_start_idx > title_end_idx:
        # Cenário ideal: tem título E insights
        title_part = '\n'.join(lines[:title_end_idx + 1])
        context_part = '\n'.join(lines[title_end_idx + 1:insights_start_idx])
        insights_part = '\n'.join(lines[insights_start_idx:])

        return title_part.strip(), context_part.strip(), insights_part.strip()

    elif title_end_idx >= 0 and insights_start_idx < 0:
        # Tem título mas não encontrou insights - dividir em 2 partes
        # Assumir que resto do conteúdo é contexto (sem insights)
        title_part = '\n'.join(lines[:title_end_idx + 1])
        context_part = '\n'.join(lines[title_end_idx + 1:])

        return title_part.strip(), context_part.strip(), ''

    elif title_end_idx < 0 and insights_start_idx >= 0:
        # Não tem título mas tem insights - usar primeiras linhas como título/contexto
        title_part = ''
        context_part = '\n'.join(lines[:insights_start_idx])
        insights_part = '\n'.join(lines[insights_start_idx:])

        return title_part.strip(), context_part.strip(), insights_part.strip()

    else:
        # FALLBACK - Não detectou estrutura clara
        # Tentar usar primeira linha como título e resto como contexto
        if lines:
            # Pegar primeiras 2-3 linhas como "título/contexto"
            title_lines_count = min(3, len(lines))

            # Procurar primeira linha vazia para delimitar seção
            for i in range(title_lines_count):
                if not lines[i].strip():
                    title_lines_count = i
                    break

            if title_lines_count > 0:
                title_part = '\n'.join(lines[:title_lines_count])
                context_part = '\n'.join(lines[title_lines_count:])

                return title_part.strip(), context_part.strip(), ''

        # Último fallback - retornar tudo como contexto
        if st.session_state.get('debug_mode', False):
            st.warning(f"Estrutura não detectada: Nenhum heading H2 e nenhuma seção de insights identificável")

        return '', response_content.strip(), ''


def _is_visualization_renderable(visualization_data: dict) -> bool:
    """
    Valida se visualization_data pode ser renderizada com sucesso.

    Esta função realiza validação completa dos metadados de visualização
    antes de remover placeholders, garantindo que o gráfico será renderizado
    com sucesso.

    Args:
        visualization_data: Dicionário com metadados de visualização

    Returns:
        bool: True se a visualização pode ser renderizada, False caso contrário
    """
    if not visualization_data:
        return False

    # Validar tipo de gráfico suportado
    chart_type = visualization_data.get('type')
    supported_types = [
        'bar_chart',
        'line_chart',
        'vertical_bar_chart',
        'grouped_vertical_bar_chart',
        'stacked_vertical_bar_chart'
    ]
    if chart_type not in supported_types:
        if st.session_state.get('debug_mode', False):
            st.warning(f"Tipo de gráfico '{chart_type}' não suportado. Tipos válidos: {supported_types}")
        return False

    # Validar flag has_data
    if not visualization_data.get('has_data', False):
        if st.session_state.get('debug_mode', False):
            st.warning("Flag 'has_data' é False - dados não disponíveis")
        return False

    # Validar DataFrame
    df = visualization_data.get('data')
    if df is None:
        if st.session_state.get('debug_mode', False):
            st.warning("DataFrame é None")
        return False

    if df.empty:
        if st.session_state.get('debug_mode', False):
            st.warning("DataFrame está vazio (0 linhas)")
        return False

    # Validar número mínimo de colunas
    if len(df.columns) < 2:
        if st.session_state.get('debug_mode', False):
            st.warning(f"DataFrame tem apenas {len(df.columns)} coluna(s). Mínimo: 2")
        return False

    # Validar configuração
    config = visualization_data.get('config', {})
    if not config:
        if st.session_state.get('debug_mode', False):
            st.warning("Configuração (config) ausente")
        return False

    # Tudo validado com sucesso
    return True


def _extract_and_replace_tables(response_content: str, has_visualization: bool) -> str:
    """
    Detecta e remove tabelas markdown da resposta quando há visualização disponível.

    Esta função implementa a lógica de substituição automática de tabelas por gráficos,
    garantindo que não haja duplicação de informação quando o sistema gera visualizações.

    Args:
        response_content: Conteúdo da resposta do agente
        has_visualization: True se há dados de visualização disponíveis

    Returns:
        str: Resposta limpa sem tabelas markdown (quando há visualização)
    """
    if not has_visualization:
        return response_content

    import re

    # NOVO: Remover placeholders de gráfico quando há visualização real
    # Padrões para detectar placeholders de gráfico
    graph_placeholder_patterns = [
        r'\[Gráfico automático\]',
        r'\[GRÁFICO AUTOMÁTICO\]',
        r'\[Gráfico será inserido automaticamente aqui\]',
        r'\[GRÁFICO SERÁ INSERIDO AUTOMATICAMENTE AQUI\]',
        r'\[Gráfico inserido automaticamente\]',
        r'\[GRÁFICO INSERIDO AUTOMATICAMENTE\]',
        r'\[Gráfico\]',
        r'\[GRÁFICO\]',
        r'\[Graph\]',
        r'\[GRAPH\]'
    ]

    # Remover todos os placeholders detectados
    for pattern in graph_placeholder_patterns:
        response_content = re.sub(pattern, '', response_content, flags=re.IGNORECASE)

    # Padrões para detectar tabelas markdown
    # Padrão 1: Tabela completa com cabeçalho e linhas
    # Formato: | col1 | col2 |
    #          |------|------|
    #          | val1 | val2 |
    table_pattern = r'\|[^\n]+\|[\s]*\n\|[\s]*[-:]+[\s]*\|[\s]*\n(\|[^\n]+\|[\s]*\n)+'

    # Padrão 2: Linhas individuais que parecem tabela (fallback)
    single_line_table_pattern = r'^\|[^\n]+\|[\s]*$'

    # Remover tabelas completas
    cleaned_content = re.sub(table_pattern, '\n', response_content, flags=re.MULTILINE)

    # Remover linhas individuais que parecem tabela (separadores, linhas órfãs)
    lines = cleaned_content.split('\n')
    filtered_lines = []

    for line in lines:
        # Ignorar linhas que são claramente partes de tabela
        if re.match(single_line_table_pattern, line.strip()):
            continue
        # Ignorar linhas de separador de tabela (|---|---|)
        if re.match(r'^\|[\s]*[-:]+[\s]*\|', line.strip()):
            continue
        filtered_lines.append(line)

    cleaned_content = '\n'.join(filtered_lines)

    # PADRÃO 3: NOVO - Detectar e remover listas de dados redundantes
    # Exemplos: "Cod_Cliente 23700 — Total: 38,531,830"
    #           "Produto A — Vendas: R$ 1.000.000"

    # Regex para detectar linhas de dados:
    # - Começa com palavra-chave (Cod_, Nome_, ID, Cliente, Produto, Estado, UF)
    # - Seguido por identificador (número, texto)
    # - Separador (— – -)
    # - Campo: Valor numérico
    data_list_pattern = r'^(?:Cod_\w+|Nome_\w+|Cliente|Produto|Estado|UF)\s+[\w\s]+\s*[—–-]\s*[^:]+:\s*(?:R\$\s*)?[\d,.\s]+.*$'

    lines = cleaned_content.split('\n')
    filtered_lines = []
    consecutive_data_lines = 0
    data_line_indices = []

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Detectar se linha parece ser item de lista de dados
        is_data_line = bool(re.match(data_list_pattern, stripped))

        if is_data_line:
            consecutive_data_lines += 1
            data_line_indices.append(i)
        else:
            # Se encontramos 2+ linhas consecutivas de dados, são redundantes
            if consecutive_data_lines >= 2:
                # Remover as linhas de dados detectadas
                for idx in data_line_indices:
                    if idx < len(filtered_lines):
                        # Marcar para remoção retroativa
                        pass
            # Reset contador
            consecutive_data_lines = 0
            data_line_indices = []
            filtered_lines.append(line)

    # Se terminou com linhas de dados consecutivas, não adicioná-las
    if consecutive_data_lines >= 2:
        # Não adicionar linhas marcadas
        final_lines = []
        skip_indices = set(data_line_indices)
        for i, line in enumerate(lines):
            if i not in skip_indices:
                final_lines.append(line)
        cleaned_content = '\n'.join(final_lines)
    else:
        cleaned_content = '\n'.join(filtered_lines)

    # PADRÃO 4: NOVO - Detectar e remover listas numeradas com dados
    # Exemplos: "1. Cliente 23700: 38 milhões de unidades"
    #           "2. Produto A: R$ 1.000.000"
    numbered_list_pattern = r'^\d+\.\s+(?:Cod_\w+|Nome_\w+|Cliente|Produto|Estado|UF|Item)\s+[\w\s]+\s*[:\-—–]\s*(?:R\$\s*)?[\d,.\s]+.*$'

    lines = cleaned_content.split('\n')
    filtered_lines = []
    consecutive_numbered = 0

    for line in lines:
        stripped = line.strip()
        is_numbered_data = bool(re.match(numbered_list_pattern, stripped, re.IGNORECASE))

        if is_numbered_data:
            consecutive_numbered += 1
        else:
            # Se encontramos 2+ linhas consecutivas, eram redundantes
            if consecutive_numbered >= 2:
                pass  # Linhas anteriores já foram ignoradas
            else:
                # Se era apenas 1 linha, pode não ser redundante - adicionar as anteriores
                if consecutive_numbered == 1:
                    # Adicionar apenas a última linha numerada (pode ser legítima)
                    pass
            consecutive_numbered = 0
            filtered_lines.append(line)

    cleaned_content = '\n'.join(filtered_lines)

    # PADRÃO 5: NOVO - Detectar e remover bullet points com dados
    # Exemplos: "- Cliente 23700: 38 milhões"
    #           "* Produto A: R$ 1.000.000"
    bullet_list_pattern = r'^[-*•]\s+(?:Cod_\w+|Nome_\w+|Cliente|Produto|Estado|UF|Item)\s+[\w\s]+\s*[:\-—–]\s*(?:R\$\s*)?[\d,.\s]+.*$'

    lines = cleaned_content.split('\n')
    filtered_lines = []
    consecutive_bullets = 0

    for line in lines:
        stripped = line.strip()
        is_bullet_data = bool(re.match(bullet_list_pattern, stripped, re.IGNORECASE))

        if is_bullet_data:
            consecutive_bullets += 1
        else:
            # Se encontramos 2+ linhas consecutivas, eram redundantes
            if consecutive_bullets >= 2:
                pass  # Linhas anteriores já foram ignoradas
            consecutive_bullets = 0
            filtered_lines.append(line)

    cleaned_content = '\n'.join(filtered_lines)

    # PADRÃO 6: NOVO - Remover parágrafos com alta densidade de valores numéricos
    # Detecta parágrafos onde > 40% do conteúdo são números/valores
    lines = cleaned_content.split('\n')
    filtered_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            filtered_lines.append(line)
            continue

        # Contar caracteres numéricos (incluindo separadores)
        num_chars = len(re.findall(r'[\d,.\s]+', stripped))
        total_chars = len(stripped)

        # Se > 40% são números e tem valores monetários ou grandes números, provavelmente é redundante
        if total_chars > 20 and num_chars / total_chars > 0.4:
            # Verificar se contém padrões típicos de dados (R$, milhões, etc.)
            has_data_patterns = bool(re.search(r'R\$|milhões|milhão|mil|total|vendas', stripped, re.IGNORECASE))
            if has_data_patterns:
                continue  # Pular esta linha (provavelmente redundante)

        filtered_lines.append(line)

    cleaned_content = '\n'.join(filtered_lines)

    # Limpar múltiplas linhas em branco consecutivas
    cleaned_content = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned_content)

    # Log para debugging (apenas em modo debug)
    patterns_detected = []
    if st.session_state.get('debug_mode', False):
        if bool(re.search(table_pattern, response_content, flags=re.MULTILINE)):
            patterns_detected.append("Tabela markdown")
        if bool(re.search(data_list_pattern, response_content, flags=re.MULTILINE)):
            patterns_detected.append("Lista de dados")
        if bool(re.search(numbered_list_pattern, response_content, flags=re.MULTILINE | re.IGNORECASE)):
            patterns_detected.append("Lista numerada")
        if bool(re.search(bullet_list_pattern, response_content, flags=re.MULTILINE | re.IGNORECASE)):
            patterns_detected.append("Bullet points")

        if patterns_detected:
            st.info(f"🔄 Padrões removidos automaticamente: {', '.join(patterns_detected)}")

    return cleaned_content.strip()


def _get_filtered_record_count(df, filter_context):
    """
    Conta registros filtrados aplicando os filtros ativos ao DataFrame usando pandas
    Versão simplificada e robusta que evita problemas de tipos SQL

    Args:
        df: DataFrame com todos os dados
        filter_context: Dicionário com filtros ativos do contexto

    Returns:
        int: Contagem de registros filtrados ou None se houver erro
    """
    try:
        # Começar com todos os registros
        filtered_df = df.copy()

        # Aplicar filtros temporais
        if 'Data_>=' in filter_context and filter_context['Data_>=']:
            filtered_df = filtered_df[filtered_df['Data'] >= filter_context['Data_>=']]
        if 'Data_<' in filter_context and filter_context['Data_<']:
            filtered_df = filtered_df[filtered_df['Data'] < filter_context['Data_<']]
        if 'Data' in filter_context and filter_context['Data']:
            filtered_df = filtered_df[filtered_df['Data'] == filter_context['Data']]

        # Aplicar filtros de região
        if 'UF_Cliente' in filter_context and filter_context['UF_Cliente']:
            uf_values = filter_context['UF_Cliente']
            if isinstance(uf_values, list):
                filtered_df = filtered_df[filtered_df['UF_Cliente'].str.upper().isin([str(v).upper() for v in uf_values])]
            else:
                filtered_df = filtered_df[filtered_df['UF_Cliente'].str.upper() == str(uf_values).upper()]

        if 'Municipio_Cliente' in filter_context and filter_context['Municipio_Cliente']:
            mun_values = filter_context['Municipio_Cliente']
            if isinstance(mun_values, list):
                filtered_df = filtered_df[filtered_df['Municipio_Cliente'].str.upper().isin([str(v).upper() for v in mun_values])]
            else:
                filtered_df = filtered_df[filtered_df['Municipio_Cliente'].str.upper() == str(mun_values).upper()]

        # Aplicar filtros de cliente
        if 'Cod_Cliente' in filter_context and filter_context['Cod_Cliente']:
            cod_values = filter_context['Cod_Cliente']
            if isinstance(cod_values, list):
                filtered_df = filtered_df[filtered_df['Cod_Cliente'].isin(cod_values)]
            else:
                filtered_df = filtered_df[filtered_df['Cod_Cliente'] == cod_values]

        if 'Cod_Segmento_Cliente' in filter_context and filter_context['Cod_Segmento_Cliente']:
            seg_values = filter_context['Cod_Segmento_Cliente']
            if isinstance(seg_values, list):
                filtered_df = filtered_df[filtered_df['Cod_Segmento_Cliente'].isin(seg_values)]
            else:
                filtered_df = filtered_df[filtered_df['Cod_Segmento_Cliente'] == seg_values]

        # Aplicar filtros de produto
        if 'Cod_Familia_Produto' in filter_context and filter_context['Cod_Familia_Produto']:
            fam_values = filter_context['Cod_Familia_Produto']
            if isinstance(fam_values, list):
                filtered_df = filtered_df[filtered_df['Cod_Familia_Produto'].isin(fam_values)]
            else:
                filtered_df = filtered_df[filtered_df['Cod_Familia_Produto'] == fam_values]

        if 'Cod_Grupo_Produto' in filter_context and filter_context['Cod_Grupo_Produto']:
            grp_values = filter_context['Cod_Grupo_Produto']
            if isinstance(grp_values, list):
                filtered_df = filtered_df[filtered_df['Cod_Grupo_Produto'].isin(grp_values)]
            else:
                filtered_df = filtered_df[filtered_df['Cod_Grupo_Produto'] == grp_values]

        if 'Cod_Linha_Produto' in filter_context and filter_context['Cod_Linha_Produto']:
            lin_values = filter_context['Cod_Linha_Produto']
            if isinstance(lin_values, list):
                filtered_df = filtered_df[filtered_df['Cod_Linha_Produto'].isin(lin_values)]
            else:
                filtered_df = filtered_df[filtered_df['Cod_Linha_Produto'] == lin_values]

        if 'Des_Linha_Produto' in filter_context and filter_context['Des_Linha_Produto']:
            des_values = filter_context['Des_Linha_Produto']
            if isinstance(des_values, list):
                filtered_df = filtered_df[filtered_df['Des_Linha_Produto'].str.upper().isin([str(v).upper() for v in des_values])]
            else:
                filtered_df = filtered_df[filtered_df['Des_Linha_Produto'].str.upper() == str(des_values).upper()]

        # Aplicar filtros de representante
        if 'Cod_Vendedor' in filter_context and filter_context['Cod_Vendedor']:
            vend_values = filter_context['Cod_Vendedor']
            if isinstance(vend_values, list):
                filtered_df = filtered_df[filtered_df['Cod_Vendedor'].isin(vend_values)]
            else:
                filtered_df = filtered_df[filtered_df['Cod_Vendedor'] == vend_values]

        if 'Cod_Regiao_Vendedor' in filter_context and filter_context['Cod_Regiao_Vendedor']:
            reg_values = filter_context['Cod_Regiao_Vendedor']
            if isinstance(reg_values, list):
                filtered_df = filtered_df[filtered_df['Cod_Regiao_Vendedor'].isin(reg_values)]
            else:
                filtered_df = filtered_df[filtered_df['Cod_Regiao_Vendedor'] == reg_values]

        # Retornar contagem
        return len(filtered_df)

    except Exception as e:
        # Em caso de erro, retornar None silenciosamente
        if st.session_state.get('debug_mode', False):
            st.warning(f"Erro ao contar registros filtrados: {str(e)}")
        return None


def _sincronizar_contexto_agente(agent):
    """
    Sincroniza contexto entre session_state e agent de forma robusta
    """
    # Se há contexto no session_state mas o agente está vazio, restaurar
    if (st.session_state.get('last_context') and
        (not hasattr(agent, 'persistent_context') or not agent.persistent_context)):
        agent.persistent_context = st.session_state.last_context.copy()
        return True
    return False


def _handle_user_input(prompt, agent):
    """Processa entrada do usuário com novo sistema JSON de filtros"""
    # Reset do flag de rerun para permitir nova atualização
    st.session_state.rerun_triggered = False

    # CORREÇÃO: Sincronizar contexto antes de processar
    context_restored = _sincronizar_contexto_agente(agent)
    if context_restored and st.session_state.get('debug_mode', False):
        st.info(f"🔄 Contexto sincronizado antes do processamento: {agent.persistent_context}")

    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Process agent response
    with st.chat_message("assistant"):
        with st.spinner("🤖 Analisando..."):
            start_time = time.time()

            # CORREÇÃO: Pré-processamento desabilitado para evitar falsos positivos
            # O sistema usa extração via SQL (sql_filter_extractor.py) que é mais precisa
            # Problema anterior: regex capturava "VENDAS POR PRODUTO EM JUNHO" como cidade
            # Mantido código comentado para referência futura

            # PRÉ-PROCESSAMENTO INTELIGENTE: Detectar intenções de substituição ANTES da execução
            current_context = getattr(agent, 'persistent_context', {}) if hasattr(agent, 'persistent_context') else {}
            disabled_filters = getattr(st.session_state, 'disabled_filters', set())

            # DESABILITADO: Pré-processar a pergunta para detectar substituições
            # from src.filters.intelligent_query_preprocessor import preprocess_user_query
            # df_dataset = getattr(agent, 'df_normalized', None)
            #
            # if df_dataset is not None:
            #     # Aplicar pré-processamento inteligente
            #     preprocessed_context, preprocessing_changes = preprocess_user_query(
            #         prompt, current_context, df_dataset
            #     )
            #
            #     # Se houve mudanças no pré-processamento, aplicar ao agente
            #     if preprocessing_changes:
            #         agent.persistent_context = preprocessed_context
            #         current_context = preprocessed_context
            #
            #         # Mostrar mudanças apenas em debug mode
            #         if st.session_state.get('debug_mode', False):
            #             substitutions = [c for c in preprocessing_changes if 'Substituindo' in c]
            #             if substitutions:
            #                 st.info(f"🔄 Pré-processamento: {len(substitutions)} substituição(ões) detectada(s)")

            # Aplicar filtros desabilitados (sem pré-processamento)
            if disabled_filters and current_context:
                from src.filters.core.manager import get_json_filter_manager
                df_dataset = getattr(agent, 'df_normalized', None)
                if df_dataset is not None:
                    json_manager = get_json_filter_manager(df_dataset)
                    current_context = json_manager.aplicar_filtros_desabilitados(current_context, disabled_filters)
                    if hasattr(agent, 'persistent_context'):
                        agent.persistent_context = current_context

            try:
                # Clear execution state if needed
                if hasattr(agent, 'clear_execution_state'):
                    agent.clear_execution_state()

                # Get agent response
                response = agent.run(prompt)
                response_time = time.time() - start_time

                # Process response content
                response_content = str(response.content) if hasattr(response, 'content') else str(response)

                # 🔍 DEBUG: Capturar resposta completa do agent
                if st.session_state.get('debug_mode', False):
                    st.warning(f"📊 DEBUG - Resposta do Agent:")
                    st.info(f"• Tamanho da resposta: {len(response_content)} caracteres")
                    st.info(f"• Primeiros 500 chars: {response_content[:500]}")
                    st.info(f"• Últimos 500 chars: {response_content[-500:]}")
                    st.info(f"• Contém 'Principais Insights': {'💡 Principais Insights' in response_content or '### Principais Insights' in response_content}")
                    st.info(f"• Contém 'Próximos Passos': {'🔍 Próximos Passos' in response_content or '### Próximos Passos' in response_content}")
                    st.info(f"• Tipo de response: {type(response)}")
                    st.code(response_content, language="markdown")

                # Extract context and debug info
                context = {}
                debug_info = {"response_time": response_time}
                visualization_data = None

                if hasattr(agent, 'debug_info'):
                    debug_info.update(agent.debug_info)

                    # CORREÇÃO CRÍTICA: Extrair filtros ANTES de limpar debug_info
                    # Processar filtros usando APENAS as queries SQL
                    try:
                        df_dataset = getattr(agent, 'df_normalized', None)
                        # Usar debug_info local que contém as queries (não agent.debug_info)
                        if df_dataset is not None and 'sql_queries' in debug_info:
                            from src.filters.core.manager import processar_filtros_apenas_sql

                            sql_queries = debug_info.get('sql_queries', [])
                            if sql_queries:
                                # Extrair filtros das queries SQL
                                updated_context_temp, filter_changes = processar_filtros_apenas_sql(
                                    sql_queries, {}, df_dataset
                                )
                                # Salvar resultado para uso posterior
                                debug_info['extracted_filters'] = updated_context_temp
                                debug_info['filter_changes'] = filter_changes
                    except Exception as e:
                        debug_info['filter_extraction_error'] = str(e)

                    agent.debug_info.clear()  # Clear for next query

                if hasattr(agent, 'persistent_context'):
                    context = agent.persistent_context.copy()

                    # CORREÇÃO CRÍTICA: Sempre detectar e restaurar contexto (não apenas em debug)
                    if 'last_agent_id' in st.session_state:
                        if st.session_state.last_agent_id != id(agent):
                            # AGENTE FOI RECRIADO - RESTAURAR CONTEXTO AUTOMATICAMENTE
                            if st.session_state.get('last_context'):
                                agent.persistent_context = st.session_state.last_context.copy()
                                context = agent.persistent_context.copy()
                                # Log apenas em debug mode
                                if st.session_state.get('debug_mode', False):
                                    st.warning(f"AGENTE RECRIADO! Contexto restaurado: {context}")
                    st.session_state.last_agent_id = id(agent)

                    # Log contexto inicial apenas em debug mode (simplificado)
                    if st.session_state.get('debug_mode', False):
                        st.info(f"🔍 Contexto atual: {len(context)} filtros ativos")

                # SISTEMA LIMPO: Extrair filtros APENAS das queries SQL
                try:
                    df_dataset = getattr(agent, 'df_normalized', None)
                    if df_dataset is not None:
                        from src.filters.core.manager import processar_filtros_apenas_sql

                        # USAR SISTEMA DE SUBSTITUIÇÃO INTELIGENTE
                        if 'extracted_filters' in debug_info:
                            extracted_context = debug_info['extracted_filters']
                            original_filter_changes = debug_info.get('filter_changes', [])

                            # APLICAR SUBSTITUIÇÃO INTELIGENTE ao invés de merge simples
                            from src.filters.core.replacer import apply_smart_filter_replacement
                            updated_context, filter_changes = apply_smart_filter_replacement(
                                context, extracted_context
                            )
                        else:
                            # Fallback: nenhum filtro foi extraído
                            updated_context = context
                            filter_changes = ["INFO: Nenhum filtro extraído das queries SQL"]

                        # Sempre atualizar contexto após processamento
                        context = updated_context

                        # FALLBACK DE SEGURANÇA: Validar e auto-resolver conflitos lógicos
                        from src.filters.core.replacer import (
                            auto_resolve_filter_conflicts,
                            validate_filter_consistency
                        )
                        is_valid, problems = validate_filter_consistency(context)

                        if not is_valid:
                            # Auto-resolver conflitos detectados
                            corrected_context, corrections = auto_resolve_filter_conflicts(context)
                            context = corrected_context

                            # Log apenas em debug mode
                            if st.session_state.get('debug_mode', False) and corrections:
                                with st.expander("Conflitos Auto-Resolvidos", expanded=False):
                                    st.warning("**Conflitos lógicos detectados e corrigidos automaticamente:**")
                                    for correction in corrections:
                                        st.info(correction)

                        # Sempre atualizar contexto persistente do agente
                        if hasattr(agent, 'update_persistent_context'):
                            agent.update_persistent_context(context)
                        elif hasattr(agent, 'persistent_context'):
                            agent.persistent_context = context

                        # Mostrar apenas substituições importantes (reduzindo verbosidade)
                        if filter_changes:
                            substitutions = [c for c in filter_changes if c.startswith("SUBSTITUIÇÃO:")]
                            if substitutions and st.session_state.get('debug_mode', False):
                                with st.expander("🔄 Filtros Atualizados", expanded=False):
                                    st.markdown("**Substituições aplicadas:**")
                                    for sub in substitutions:
                                        st.info(sub.replace("SUBSTITUIÇÃO: ", ""))

                except Exception as e:
                    # Se houver erro na extração, continuar normalmente sem fallback
                    if st.session_state.get('debug_mode', False):
                        st.error(f" **ERRO** no processamento de filtros SQL:")
                        st.error(f"  - Exceção: {str(e)}")
                        st.error(f"  - Tipo: {type(e).__name__}")
                        st.error(f"  - Debug info disponível: {hasattr(agent, 'debug_info') and bool(agent.debug_info)}")
                        import traceback
                        st.error(f"  - Stack trace: {traceback.format_exc()}")
                    else:
                        st.warning(f"Erro no processamento de filtros SQL: {str(e)}")

                    # Em caso de erro, manter contexto atual (não usar fallback)
                    pass

                # FASE 2: Processar metadados de visualização do agent (tool-based)
                # Priorizar visualization_metadata criado por VisualizationTools
                if hasattr(agent, 'debug_info') and 'visualization_metadata' in agent.debug_info:
                    viz_metadata_list = agent.debug_info['visualization_metadata']

                    if viz_metadata_list:
                        # Usar primeira visualização encontrada
                        # (agent pode ter chamado prepare_chart durante sua execução)
                        visualization_data = viz_metadata_list[0]

                        # Log em modo debug
                        if st.session_state.get('debug_mode', False):
                            st.success(f" Visualização gerada pelo agent durante execução (Fase 2)")
                else:
                    # FALLBACK: Extração automática de dados (lógica antiga - Fase 1)
                    # Mantido para compatibilidade, mas deve ser usado menos frequentemente
                    if hasattr(agent, 'tools'):
                        for tool in agent.tools:
                            if hasattr(tool, 'last_result_df') and tool.last_result_df is not None:
                                df_result = tool.last_result_df
                                if not df_result.empty:
                                    # Verificar se é análise temporal para permitir mais linhas
                                    is_likely_temporal = _is_temporal_analysis(df_result, prompt)
                                    max_rows = 50 if is_likely_temporal else 20

                                    # Debug logging ANTES da verificação de linhas
                                    if st.session_state.get('debug_mode', False):
                                        st.info(f"📊 Tentando gerar visualização: {len(df_result)} linhas (máx: {max_rows})")
                                        st.info(f"   Colunas: {list(df_result.columns)}")
                                        st.info(f"   Temporal: {is_likely_temporal}")

                                    if len(df_result) <= max_rows:
                                        # Passar a query SQL para permitir mapeamento de aliases
                                        last_query = getattr(tool, 'last_query', None)
                                        visualization_data = _prepare_visualization_data(df_result, is_likely_temporal, prompt, last_query=last_query)

                                        if visualization_data:
                                            # Log em modo debug
                                            if st.session_state.get('debug_mode', False):
                                                st.success(" Visualização gerada por fallback automático (Fase 1)")
                                        else:
                                            # Log se prepare_visualization_data retornou None
                                            if st.session_state.get('debug_mode', False):
                                                st.warning("_prepare_visualization_data() retornou None - verifique estrutura dos dados")
                                    else:
                                        # Log se excedeu limite de linhas
                                        if st.session_state.get('debug_mode', False):
                                            st.warning(f"Muitas linhas para visualização: {len(df_result)} > {max_rows}")
                                break

                # SUBSTITUIÇÃO AUTOMÁTICA DE TABELAS POR GRÁFICOS
                # Remove tabelas markdown quando há visualização disponível
                # VALIDAÇÃO COMPLETA antes de remover placeholder
                if visualization_data and _is_visualization_renderable(visualization_data):
                    response_content = _extract_and_replace_tables(response_content, True)

                # INSERIR GRÁFICO NA POSIÇÃO CORRETA: Título → Contexto → Gráfico → Insights
                if visualization_data:
                    # Separar título, contexto e insights do conteúdo
                    title_part, context_part, insights_part = _split_title_and_content(response_content)

                    # Renderizar: Título → Contexto → Gráfico → Insights/Próximos Passos
                    # CORREÇÃO: Escapar símbolos de moeda antes de renderizar
                    if title_part:
                        st.markdown(escape_currency_for_markdown(title_part))
                    if context_part:
                        st.markdown(escape_currency_for_markdown(context_part))

                    # Tentar renderizar gráfico e capturar erro
                    success, error_msg = render_plotly_visualization(visualization_data)
                    if not success:
                        # Se falhou, exibir mensagem em debug mode
                        if st.session_state.get('debug_mode', False):
                            st.error(f"Falha na renderização do gráfico: {error_msg}")
                        # Exibir mensagem amigável ao usuário
                        st.info("📊 Visualização não disponível para este conjunto de dados")

                    if insights_part:
                        st.markdown(escape_currency_for_markdown(insights_part))
                else:
                    # Sem visualização: renderizar conteúdo normalmente
                    # CORREÇÃO: Escapar símbolos de moeda antes de renderizar
                    st.markdown(escape_currency_for_markdown(response_content))

                # Display response time
                st.markdown(f"⏱️ *Tempo de resposta: {response_time:.2f}s*")

                # Store message with all metadata
                assistant_message = {
                    "role": "assistant",
                    "content": response_content,
                    "context": context,
                    "debug_info": debug_info
                }

                if visualization_data:
                    assistant_message["visualization_data"] = visualization_data

                st.session_state.messages.append(assistant_message)

                # ATUALIZAÇÃO IMEDIATA DA SIDEBAR: Detectar se o contexto mudou
                previous_context = st.session_state.get('last_context', {})
                context_changed = context != previous_context

                st.session_state.last_context = context

                # Log estado final apenas em debug mode (simplificado)
                if st.session_state.get('debug_mode', False) and context_changed:
                    st.info(f"🔍 Filtros atualizados: {len(st.session_state.last_context)} filtros ativos")

                # Display debug info if enabled
                if debug_info and st.session_state.get('debug_mode', False):
                    _render_debug_info(debug_info, context)

                # FORÇAR ATUALIZAÇÃO VISUAL IMEDIATA da sidebar se contexto mudou
                if context_changed and context:
                    # Marcar que filtros foram atualizados para trigger rerun
                    st.session_state.filters_just_updated = True
                    # Fazer rerun apenas uma vez para atualizar sidebar
                    if not st.session_state.get('rerun_triggered', False):
                        st.session_state.rerun_triggered = True
                        st.rerun()

            except Exception as e:
                error_msg = f" **Erro:** {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg,
                    "context": {},
                    "debug_info": {"error": str(e), "response_time": time.time() - start_time}
                })



def _is_temporal_analysis(df_result, user_prompt):
    """
    Detecta se a análise é temporal baseado nos dados e na pergunta do usuário.

    Args:
        df_result: DataFrame com resultados da query
        user_prompt: Pergunta do usuário

    Returns:
        bool: True se for análise temporal
    """
    # Palavras-chave que indicam análise temporal na pergunta
    temporal_keywords = [
        'tendencia', 'tendência', 'evolucao', 'evolução', 'linha do tempo',
        'ao longo', 'mês a mês', 'mes a mes', 'mensal', 'anual',
        'trimestral', 'periodo', 'período', 'historico', 'histórico',
        'serie temporal', 'série temporal', 'crescimento', 'variação temporal'
    ]

    prompt_lower = user_prompt.lower()
    has_temporal_keyword = any(keyword in prompt_lower for keyword in temporal_keywords)

    # Verificar estrutura dos dados
    if len(df_result.columns) >= 2:
        # Verificar nomes de colunas
        col_names = ' '.join(df_result.columns).lower()
        has_temporal_column = any(
            keyword in col_names
            for keyword in ['data', 'mes', 'ano', 'periodo', 'date', 'month', 'year', 'trimestre', 'semestre']
        )

        # Verificar se primeira coluna parece ser temporal (por tipo ou conteúdo)
        first_col = df_result.iloc[:, 0]
        is_date_type = pd.api.types.is_datetime64_any_dtype(first_col)

        # Verificar se valores parecem datas/períodos (ex: "2015-01", "Jan/2015", etc.)
        if not is_date_type and first_col.dtype == 'object':
            sample_values = first_col.head(3).astype(str)
            looks_like_dates = any(
                bool(re.search(r'\d{4}[-/]\d{1,2}|\d{1,2}[-/]\d{4}|^\d{4}$|[a-z]{3}[/-]\d{4}', str(val), re.IGNORECASE))
                for val in sample_values
            )
        else:
            looks_like_dates = False

        return has_temporal_keyword or has_temporal_column or is_date_type or looks_like_dates

    return has_temporal_keyword


def _prepare_visualization_data(df_result, is_temporal_hint=False, user_prompt="", last_query=None):
    """
    Prepara dados para visualização automática.
    Suporta séries únicas e múltiplas séries (até 10 categorias).

    Args:
        df_result: DataFrame com resultados
        is_temporal_hint: Dica se a análise é temporal
        user_prompt: Pergunta do usuário para detectar intenção (ranking vs comparação)
        last_query: Query SQL que gerou este DataFrame (para mapeamento de aliases)

    Returns:
        dict: Dados formatados para visualização ou None
    """
    debug_mode = st.session_state.get('debug_mode', False)

    if df_result.empty or len(df_result.columns) < 2:
        if debug_mode:
            st.warning(f" Visualização cancelada: DataFrame vazio ou < 2 colunas (tem {len(df_result.columns)})")
        return None

    # Tentar identificar colunas de valor e rótulo
    numeric_cols = df_result.select_dtypes(include=['number']).columns
    text_cols = df_result.select_dtypes(include=['object', 'string']).columns
    datetime_cols = df_result.select_dtypes(include=['datetime64']).columns

    # Variáveis para armazenar estrutura detectada
    label_col = None
    value_col = None
    category_col = None
    group_col = None  # NOVO: Para comparações grupais
    is_temporal = False
    has_multiple_series = False
    is_grouped_comparison = False  # NOVO: Flag para comparações grupais

    # CASO 1: Múltiplas séries temporais (3+ colunas)
    # Estrutura: data + categoria + valor
    if len(df_result.columns) >= 3 and len(numeric_cols) >= 1:
        value_col = numeric_cols[0]

        # Identificar coluna temporal (datetime ou texto com padrão de data)
        temporal_col = None
        category_candidate = None

        if len(datetime_cols) >= 1:
            temporal_col = datetime_cols[0]
            # Outras colunas de texto são candidatas a categoria
            remaining_text_cols = [col for col in text_cols if col != temporal_col]
            if remaining_text_cols:
                category_candidate = remaining_text_cols[0]
        else:
            # Procurar coluna com nome temporal nos text_cols
            temporal_keywords = ['data', 'mes', 'ano', 'periodo', 'date', 'month', 'year', 'trimestre', 'semestre']

            for col in text_cols:
                col_lower = col.lower()
                if any(keyword in col_lower for keyword in temporal_keywords):
                    temporal_col = col
                    break

            # Se não encontrou por nome, tentar por conteúdo
            if not temporal_col and len(text_cols) >= 2:
                for col in text_cols:
                    sample_values = df_result[col].head(3).astype(str)
                    looks_like_dates = any(
                        bool(re.search(r'\d{4}[-/]\d{1,2}|\d{1,2}[-/]\d{4}|^\d{4}$', str(val), re.IGNORECASE))
                        for val in sample_values
                    )
                    if looks_like_dates:
                        temporal_col = col
                        break

            if temporal_col:
                # Outras colunas de texto são candidatas a categoria
                remaining_text_cols = [col for col in text_cols if col != temporal_col]
                if remaining_text_cols:
                    category_candidate = remaining_text_cols[0]

        # Se encontrou temporal e categoria, verificar se é multi-série OU comparação grupal
        if temporal_col and category_candidate:
            label_col = temporal_col
            category_col = category_candidate
            is_temporal = True

            # Verificar número de períodos e categorias únicas
            n_periods = df_result[temporal_col].nunique()
            n_categories = df_result[category_candidate].nunique()

            # PRIORIDADE: Se n_periods <= 2 E n_categories entre 2-5 E palavras de comparação
            # → Deixar para CASO 1.5 processar como comparação grupal
            prompt_lower = user_prompt.lower()
            comparison_keywords = [
                'comparar', 'comparação', 'comparacao', 'vs', 'versus',
                'diferença', 'diferenca', 'variação', 'variacao',
                'entre', 'comparativo', 'contraste'
            ]
            is_comparison_query = any(keyword in prompt_lower for keyword in comparison_keywords)

            # Verificar se atende critérios de comparação grupal temporal
            is_temporal_comparison = (1 <= n_periods <= 2 and
                                     2 <= n_categories <= 5 and
                                     (is_comparison_query or len(df_result) <= 12))

            if is_temporal_comparison:
                # NÃO ativar has_multiple_series - deixar para CASO 1.5
                # IMPORTANTE: Desativar is_temporal para evitar que seja tratado como line_chart
                is_temporal = False
                # Marcar como candidato a comparação grupal
                if debug_mode:
                    st.info(f"🔄 Estrutura temporal com {n_periods} períodos × {n_categories} categorias → Candidato a comparação grupal")
            elif n_categories <= 10:
                # Análise temporal normal (> 2 períodos)
                has_multiple_series = True
            else:
                # Muitas categorias - retornar None para exibir tabela
                if debug_mode:
                    st.warning(f" Visualização cancelada: Muitas categorias ({n_categories} > 10)")
                return None

    # CASO 1.5: NOVO - Comparações grupais (3 colunas: temporal/texto + categoria + valor)
    # Estrutura: grupo (1-2 únicos) + categoria (2-5 únicos) + valor
    # Exemplo: ["Março 2015", "SC", 1000], ["Março 2015", "PR", 800], ["Abril 2015", "SC", 1200]...
    # MODIFICADO: Aceita tanto estruturas temporais quanto não-temporais
    if not has_multiple_series and len(df_result.columns) >= 3 and len(numeric_cols) >= 1:
        if value_col is None:
            value_col = numeric_cols[0]

        # Procurar estrutura de comparação grupal
        # Prioridade 1: Se já detectou label_col e category_col no CASO 1
        # (pode ser temporal ou não - removido check de is_temporal para suportar temporal_comparison)
        if label_col and category_col:
            # Usar estrutura detectada no CASO 1
            potential_group_col = label_col
            potential_category_col = category_col
        # Prioridade 2: Colunas de texto (estrutura não-temporal)
        elif len(text_cols) >= 2:
            # Tentar primeira coluna como grupo e segunda como categoria
            potential_group_col = text_cols[0]
            potential_category_col = text_cols[1]
        # Prioridade 3: Datetime + texto
        elif len(datetime_cols) >= 1 and len(text_cols) >= 1:
            potential_group_col = datetime_cols[0]
            potential_category_col = text_cols[0]
        else:
            potential_group_col = None
            potential_category_col = None

        # Validar estrutura de comparação grupal
        if potential_group_col and potential_category_col:
            n_groups = df_result[potential_group_col].nunique()
            n_categories = df_result[potential_category_col].nunique()

            # Verificar se atende critérios de comparação grupal:
            # - 1-2 grupos únicos
            # - 2-5 categorias únicas
            if 1 <= n_groups <= 2 and 2 <= n_categories <= 5:
                # Verificar intenção do usuário através de palavras-chave
                prompt_lower = user_prompt.lower()
                comparison_keywords = [
                    'comparar', 'comparação', 'comparacao', 'vs', 'versus',
                    'diferença', 'diferenca', 'variação', 'variacao',
                    'entre', 'comparativo', 'contraste'
                ]
                is_comparison_query = any(keyword in prompt_lower for keyword in comparison_keywords)

                # Ativar comparação grupal se:
                # 1. Estrutura de dados adequada (já validada acima)
                # 2. Pergunta contém palavras de comparação OU número de linhas é pequeno
                if is_comparison_query or len(df_result) <= 12:  # <= 12 linhas = max 2 grupos × 6 categorias (margem de segurança)
                    group_col = potential_group_col
                    category_col = potential_category_col
                    is_grouped_comparison = True

                    if debug_mode:
                        st.info(f"📊 Detectado: Comparação grupal ({n_groups} grupos × {n_categories} categorias)")

    # CASO 2: Série única com datetime
    if not has_multiple_series and not is_grouped_comparison:
        if len(datetime_cols) >= 1 and len(numeric_cols) >= 1:
            label_col = datetime_cols[0]
            value_col = numeric_cols[0]
            is_temporal = True

        # CASO 3: Série única com texto (verificar se é temporal)
        elif len(numeric_cols) >= 1 and len(text_cols) >= 1:
            value_col = numeric_cols[0]
            label_col = text_cols[0]

            # Detectar se é dados temporais com lógica aprimorada
            col_name_temporal = any(
                keyword in label_col.lower()
                for keyword in ['data', 'mes', 'ano', 'periodo', 'date', 'month', 'year', 'trimestre', 'semestre']
            )

            # Verificar conteúdo da coluna para padrões de data
            sample_values = df_result[label_col].head(3).astype(str)
            content_temporal = any(
                bool(re.search(r'\d{4}[-/]\d{1,2}|\d{1,2}[-/]\d{4}|^\d{4}$|[a-z]{3}[/-]\d{4}', str(val), re.IGNORECASE))
                for val in sample_values
            )

            is_temporal = is_temporal_hint or col_name_temporal or content_temporal

        # CASO 4: NOVO - Duas colunas numéricas (ex: Cod_Cliente + Valor)
        # Assumir que primeira coluna é ID/label e segunda é valor
        elif len(numeric_cols) >= 2 and len(text_cols) == 0:
            # Primeira coluna numérica = label (ex: Cod_Cliente, Cod_Produto)
            label_col = numeric_cols[0]
            # Segunda coluna numérica = valor
            value_col = numeric_cols[1] if len(numeric_cols) > 1 else numeric_cols[0]
            is_temporal = False

            if debug_mode:
                st.info(f"📊 Detectado: Rankings com IDs numéricos (label={label_col}, value={value_col})")

        else:
            if debug_mode:
                st.warning(f" Visualização cancelada: Não foi possível identificar estrutura dos dados")
                st.warning(f"   Colunas numéricas: {list(numeric_cols)}, Texto: {list(text_cols)}, Datetime: {list(datetime_cols)}")
            return None

    # Se não conseguiu identificar estrutura, retornar None
    if label_col is None or value_col is None:
        if debug_mode:
            st.warning(f" Visualização cancelada: Não identificou label_col ou value_col (label={label_col}, value={value_col})")
        return None

    # Detectar se é composição empilhada (STACKED)
    # Estrutura: 3 colunas não-temporais com múltiplas categorias em ambas dimensões
    is_stacked_composition = False
    if not has_multiple_series and not is_grouped_comparison and len(df_result.columns) == 3:
        # Verificar se não é temporal
        first_col = df_result.columns[0]
        is_temporal_col = any(keyword in first_col.lower() for keyword in ['date', 'data', 'mes', 'ano', 'period'])

        if not is_temporal_col:
            # Verificar se há múltiplas categorias em ambas dimensões
            n_col1 = df_result.iloc[:, 0].nunique()
            n_col2 = df_result.iloc[:, 1].nunique()

            # Critério: múltiplas categorias em ambas + pelo menos uma > 2
            if n_col1 >= 2 and n_col2 >= 2 and (n_col1 > 2 or n_col2 > 2):
                # Validar que não atende critérios de grouped (1-2 grupos × 2-5 categorias)
                if not (1 <= n_col1 <= 2 and 2 <= n_col2 <= 5):
                    is_stacked_composition = True

    # Determinar tipo de gráfico baseado no contexto E intenção do usuário
    # IMPORTANTE: Verificar is_stacked_composition ANTES de is_grouped_comparison para dar prioridade
    if is_stacked_composition:
        # NOVO: Usar gráfico de barras verticais empilhadas para composições
        chart_type = 'stacked_vertical_bar_chart'
    elif is_grouped_comparison:
        # Usar gráfico de barras verticais agrupadas
        chart_type = 'grouped_vertical_bar_chart'
    elif is_temporal:
        chart_type = 'line_chart'
    else:
        # Detectar intenção da pergunta do usuário
        prompt_lower = user_prompt.lower()

        # Palavras-chave de RANKING (sempre usar barras horizontais)
        ranking_keywords = [
            'top', 'maiores', 'menores', 'melhores', 'piores',
            'ranking', 'principais', 'lideres', 'líderes',
            'mais vendidos', 'menos vendidos', 'maior', 'menor'
        ]
        is_ranking_query = any(keyword in prompt_lower for keyword in ranking_keywords)

        # Palavras-chave de COMPARAÇÃO (usar barras verticais se 2-5 itens)
        comparison_keywords = [
            'comparar', 'comparação', 'comparacao', 'vs', 'versus',
            'diferença', 'diferenca', 'variação', 'variacao',
            'entre', 'comparativo', 'contraste'
        ]
        is_comparison_query = any(keyword in prompt_lower for keyword in comparison_keywords)

        # Lógica de decisão:
        if is_ranking_query:
            # Sempre usar barras horizontais para rankings, independente do número de itens
            chart_type = 'bar_chart'
        elif is_comparison_query and not has_multiple_series and 2 <= len(df_result) <= 5:
            # Usar barras verticais apenas para comparações explícitas com 2-5 itens
            chart_type = 'vertical_bar_chart'
        elif not has_multiple_series and len(df_result) > 5:
            # Muitos itens sem palavra-chave explícita: provavelmente é ranking
            chart_type = 'bar_chart'
        else:
            # Fallback: usar barras horizontais para casos ambíguos
            chart_type = 'bar_chart'

    # Preparar dados no formato esperado
    if is_stacked_composition:
        # NOVO: Composição empilhada - formato com main_category, sub_category, value
        col1, col2 = df_result.columns[0], df_result.columns[1]

        # DECISÃO: Qual coluna é main (eixo X) e qual é sub (empilhado)?
        # REGRA DO USUÁRIO: "Sempre o maior conjunto no eixo X"
        n_col1 = df_result[col1].nunique()
        n_col2 = df_result[col2].nunique()

        if n_col1 >= n_col2:
            main_col, sub_col = col1, col2
        else:
            main_col, sub_col = col2, col1

        chart_data = df_result[[main_col, sub_col, value_col]].copy()
        chart_data.columns = ['main_category', 'sub_category', 'value']

        # Ordenar por total da main_category
        main_totals = chart_data.groupby('main_category')['value'].sum().sort_values(ascending=False)
        chart_data['main_category'] = pd.Categorical(
            chart_data['main_category'],
            categories=main_totals.index,
            ordered=True
        )
        chart_data = chart_data.sort_values(['main_category', 'value'], ascending=[True, False])

        n_main = chart_data['main_category'].nunique()
        n_sub = chart_data['sub_category'].nunique()
        title = f'Composição: {n_main} categorias × {n_sub} subcategorias'
    elif is_grouped_comparison:
        # Comparação grupal - formato especial com group, category, value
        chart_data = df_result[[group_col, category_col, value_col]].copy()
        chart_data.columns = ['group', 'category', 'value']

        # Ordenar por grupo e categoria para visualização consistente
        chart_data = chart_data.sort_values(['group', 'category'])

        n_groups = chart_data['group'].nunique()
        n_categories = chart_data['category'].nunique()
        title = f'Comparação entre {n_groups} {"períodos" if n_groups > 1 else "período"} - {n_categories} categorias'
    elif has_multiple_series:
        # Múltiplas séries: incluir coluna de categoria
        chart_data = df_result[[label_col, category_col, value_col]].copy()
        chart_data.columns = ['date', 'category', 'value']

        # Garantir ordenação por data e categoria para visualização correta
        try:
            chart_data['date'] = pd.to_datetime(chart_data['date'])
            chart_data = chart_data.sort_values(['date', 'category'])
        except:
            chart_data = chart_data.sort_values(['date', 'category'])

        n_series = chart_data['category'].nunique()
        n_periods = chart_data['date'].nunique()
        title = f'Evolução Temporal - {n_series} Categorias ({n_periods} períodos)'
    else:
        # Série única
        chart_data = df_result[[label_col, value_col]].copy()
        chart_data.columns = ['label' if not is_temporal else 'date', 'value']

        # CORREÇÃO: Converter IDs numéricos para string para exibição correta
        if not is_temporal:
            chart_data['label'] = chart_data['label'].astype(str)

        title = f'{"Evolução Temporal" if is_temporal else "Top Resultados"} ({len(chart_data)} {"períodos" if is_temporal else "itens"})'

    # Mapear alias SQL de volta para nome original da coluna
    original_value_column = value_col
    if last_query and value_col:
        try:
            from src.utils.sql_column_mapper import extract_original_column_from_alias
            mapped_col = extract_original_column_from_alias(last_query, value_col)
            if mapped_col:
                original_value_column = mapped_col
        except Exception:
            pass  # Em caso de erro, usar value_col original

    # Preparar config com y_label para gráficos multi-série e grupais
    config = {
        'title': title,
        'value_format': 'currency' if 'valor' in value_col.lower() else 'number',
        'is_categorical_id': not is_temporal and not has_multiple_series and not is_grouped_comparison,
        'original_value_column': original_value_column
    }

    # Para gráficos multi-série, adicionar y_label que é usado pelo plotly_charts
    if has_multiple_series:
        config['y_label'] = original_value_column

    # Para gráficos de comparação grupal, adicionar x_label e y_label
    if is_grouped_comparison:
        config['x_label'] = group_col if group_col else 'Período/Item'
        config['y_label'] = original_value_column

    # Para gráficos de composição empilhada, adicionar x_label, y_label e sub_label
    if is_stacked_composition:
        config['x_label'] = main_col if 'main_col' in locals() else 'Categoria'
        config['y_label'] = original_value_column
        config['sub_label'] = sub_col if 'sub_col' in locals() else 'Subcategoria'

    return {
        'type': chart_type,
        'data': chart_data,
        'has_data': True,
        'has_multiple_series': has_multiple_series,
        'config': config
    }





def _render_footer():
    """Renderiza footer com logotipo da empresa"""
    # Footer Target Data Experience
    st.markdown("---")
    st.markdown("<br>", unsafe_allow_html=True)

    # Create footer with logo
    footer_col1, footer_col2, footer_col3 = st.columns([1, 2, 1])

    with footer_col2:
        # Company footer with modern styling
        st.markdown(
            """
            <div style="text-align: center; background: linear-gradient(135deg, #1a2332 0%, #2d3e50 100%);
                        padding: 30px; border-radius: 15px; margin: 20px 0; display: flex;
                        flex-direction: column; align-items: center; justify-content: center;">
                <div style="color: white; font-family: 'Arial', sans-serif; font-weight: 300;
                           letter-spacing: 6px; margin: 0; font-size: 24px;">T A R G E T</div>
                <div style="color: #e74c3c; font-family: 'Arial', sans-serif; font-weight: 300;
                          letter-spacing: 3px; margin: 8px 0 0 0; font-size: 12px;">D A T A &nbsp; E X P E R I E N C E</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)


def _build_intelligent_filter_json(message_context: Dict) -> Dict:
    """
    Constrói JSON de filtros de forma inteligente preservando granularidade temporal.

    Args:
        message_context: Contexto da mensagem processada

    Returns:
        Dict com estrutura JSON preservando granularidade de mês/ano
    """
    filter_json = {
        "periodo": {},
        "regiao": {
            "UF_Cliente": message_context.get("UF_Cliente"),
            "Municipio_Cliente": message_context.get("Municipio_Cliente")
        },
        "cliente": {
            "Cod_Cliente": message_context.get("Cod_Cliente"),
            "Cod_Segmento_Cliente": message_context.get("Cod_Segmento_Cliente")
        },
        "produto": {
            "Cod_Familia_Produto": message_context.get("Cod_Familia_Produto"),
            "Cod_Grupo_Produto": message_context.get("Cod_Grupo_Produto"),
            "Cod_Linha_Produto": message_context.get("Cod_Linha_Produto"),
            "Des_Linha_Produto": message_context.get("Des_Linha_Produto")
        },
        "representante": {
            "Cod_Vendedor": message_context.get("Cod_Vendedor"),
            "Cod_Regiao_Vendedor": message_context.get("Cod_Regiao_Vendedor")
        }
    }

    # LÓGICA INTELIGENTE PARA PERÍODO - PRESERVAR GRANULARIDADE
    try:
        from src.text_normalizer import normalizer

        # CORREÇÃO CRÍTICA: Verificar se há estrutura inicio/fim (novo formato)
        if message_context.get("inicio") and message_context.get("fim"):
            # Novo formato estruturado já está correto
            filter_json["periodo"] = {
                "inicio": message_context["inicio"],
                "fim": message_context["fim"]
            }

        # Verificar se há ranges de data no contexto (formato antigo)
        elif message_context.get("Data_>=") and message_context.get("Data_<"):
            data_inicio = message_context["Data_>="]
            data_fim = message_context["Data_<"]

            # NOVO: Converter ranges para estrutura mês/ano se possível
            structured_data = _convert_range_to_structured(data_inicio, data_fim)
            if structured_data:
                filter_json["periodo"] = structured_data
            else:
                # Fallback para ranges originais
                filter_json["periodo"] = {
                    "Data_>=": data_inicio,
                    "Data_<": data_fim
                }

        # Se há apenas Data simples, tentar preservar como estava
        elif message_context.get("Data"):
            filter_json["periodo"]["Data"] = message_context["Data"]

        # CORREÇÃO: Verificar se há campos de mês/ano diretos
        elif message_context.get("mes") and message_context.get("ano"):
            filter_json["periodo"] = {
                "mes": message_context["mes"],
                "ano": message_context["ano"]
            }

        # Se não há info temporal, deixar vazio
        else:
            # Período vazio será removido pelo _clean_empty_fields
            pass

    except Exception as e:
        # Fallback para formato antigo se algo der errado
        filter_json["periodo"] = {
            "error": f"Erro ao processar período: {str(e)}",
            "Data": message_context.get("Data"),
            "Data_>=": message_context.get("Data_>="),
            "Data_<": message_context.get("Data_<"),
            "inicio": message_context.get("inicio"),
            "fim": message_context.get("fim")
        }

    # Limpar campos vazios
    filter_json = _clean_empty_fields(filter_json)

    return filter_json


def _convert_range_to_structured(data_inicio: str, data_fim: str) -> Optional[Dict]:
    """
    Converte ranges de data para estrutura mês/ano se aplicável.

    Args:
        data_inicio: Data início (YYYY-MM-DD)
        data_fim: Data fim (YYYY-MM-DD)

    Returns:
        Dict com estrutura mês/ano ou None se não aplicável
    """
    try:
        from datetime import datetime, timedelta

        start = datetime.strptime(data_inicio, '%Y-%m-%d')
        end = datetime.strptime(data_fim, '%Y-%m-%d')

        # Verificar se é um mês específico
        if (start.day == 1 and
            end.day == 1 and
            start.year == end.year and
            end.month == start.month + 1):

            return {
                "mes": f"{start.month:02d}",
                "ano": str(start.year)
            }

        # Verificar se é intervalo de meses no mesmo ano
        elif (start.day == 1 and
              end.day == 1 and
              start.year == end.year and
              end.month > start.month):

            return {
                "inicio": {
                    "mes": f"{start.month:02d}",
                    "ano": str(start.year)
                },
                "fim": {
                    "mes": f"{end.month - 1:02d}",  # end é exclusivo
                    "ano": str(start.year)
                }
            }

        # Verificar se é ano completo
        elif (start.month == 1 and start.day == 1 and
              end.month == 1 and end.day == 1 and
              end.year == start.year + 1):

            return {"ano": str(start.year)}

    except Exception:
        pass

    return None


def _clean_empty_fields(data: Dict) -> Dict:
    """
    Remove campos None ou vazios do dicionário recursivamente.

    Args:
        data: Dicionário para limpar

    Returns:
        Dicionário limpo
    """
    if isinstance(data, dict):
        cleaned = {}
        for key, value in data.items():
            if isinstance(value, dict):
                cleaned_value = _clean_empty_fields(value)
                if cleaned_value:  # Só adicionar se dict não estiver vazio
                    cleaned[key] = cleaned_value
            elif value is not None and value != [] and value != "":
                cleaned[key] = value
        return cleaned
    else:
        return data


if __name__ == "__main__":
    main()