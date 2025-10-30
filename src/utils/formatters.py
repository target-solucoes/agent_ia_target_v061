"""
Funções de formatação centralizadas para contexto, SQL e números
"""

import re


def format_context_for_display(context_dict):
    """
    Formata contexto de forma amigável para exibição no sidebar (versão legada para compatibilidade)
    """
    if not context_dict or context_dict.get('sem_filtros') == 'consulta_geral':
        return "🔍 **Consulta Geral**\n\n*Nenhum filtro ativo*"

    display_parts = ["✅ **Filtros Ativos**", ""]

    # Categorizar filtros baseado na hierarquia completa
    temporal_filters = []
    region_filters = []
    client_filters = []
    product_filters = []
    representative_filters = []

    for key, value in context_dict.items():
        # Período
        if key in ['Data', 'Data_>=', 'Data_<', 'periodo', 'mes', 'ano']:
            temporal_filters.append((key, value))
        # Região
        elif key in ['UF_Cliente', 'Municipio_Cliente', 'cidade', 'estado', 'municipio', 'uf']:
            region_filters.append((key, value))
        # Cliente
        elif key in ['Cod_Cliente', 'Cod_Segmento_Cliente']:
            client_filters.append((key, value))
        # Produto
        elif key in ['Cod_Familia_Produto', 'Cod_Grupo_Produto', 'Cod_Linha_Produto', 'Des_Linha_Produto', 'Produto', 'produto', 'linha']:
            product_filters.append((key, value))
        # Representante
        elif key in ['Cod_Vendedor', 'Cod_Regiao_Vendedor']:
            representative_filters.append((key, value))

    # Formatação por categoria com melhor visual
    if temporal_filters:
        display_parts.append("📅 **Período**")

        # Detectar se é um range de datas
        start_date = None
        end_date = None

        for key, value in temporal_filters:
            if 'Data_>=' in key or key == 'inicio':
                start_date = value
            elif 'Data_<' in key or key == 'fim':
                end_date = value

        if start_date and end_date:
            display_parts.append(f"⏰ **Período**: {start_date} até {end_date}")
        else:
            for key, value in temporal_filters:
                if key == 'Data':
                    display_parts.append(f"📆 **Data**: {value}")
                elif 'mes' in key.lower():
                    display_parts.append(f"📅 **Mês**: {value}")
                elif 'ano' in key.lower():
                    display_parts.append(f"🗓️ **Ano**: {value}")
                else:
                    display_name = key.replace("Data_", "").replace(">=", "A partir de").replace("<", "Antes de")
                    display_parts.append(f"📅 **{display_name}**: {value}")
        display_parts.append("")

    if region_filters:
        display_parts.append("📍 **Região**")
        for key, value in region_filters:
            if key in ['Municipio_Cliente', 'cidade', 'municipio']:
                display_parts.append(f"🏙️ Cidade: **{value}**")
            elif key in ['UF_Cliente', 'estado', 'uf']:
                display_parts.append(f"🗺️ Estado: **{value}**")
            else:
                display_parts.append(f"📍 {key}: **{value}**")
        display_parts.append("")

    if client_filters:
        display_parts.append("👥 **Cliente**")
        for key, value in client_filters:
            if key == 'Cod_Cliente':
                display_parts.append(f"🏢 Cliente: **{value}**")
            elif key == 'Cod_Segmento_Cliente':
                display_parts.append(f"📊 Segmento: **{value}**")
            else:
                display_parts.append(f"👥 {key}: **{value}**")
        display_parts.append("")

    if product_filters:
        display_parts.append("🛍️ **Produto**")
        for key, value in product_filters:
            if key == 'Cod_Familia_Produto':
                display_parts.append(f"🏭 Família: **{value}**")
            elif key == 'Cod_Grupo_Produto':
                display_parts.append(f"📋 Grupo: **{value}**")
            elif key == 'Cod_Linha_Produto':
                display_parts.append(f"📦 Cód. Linha: **{value}**")
            elif key in ['Des_Linha_Produto', 'linha']:
                display_parts.append(f"📦 Linha: **{value}**")
            elif key in ['Produto', 'produto']:
                display_parts.append(f"🏷️ Produto: **{value}**")
            else:
                display_parts.append(f"🛍️ {key}: **{value}**")
        display_parts.append("")

    if representative_filters:
        display_parts.append("👨‍💼 **Representante**")
        for key, value in representative_filters:
            if key == 'Cod_Vendedor':
                display_parts.append(f"🤝 Vendedor: **{value}**")
            elif key == 'Cod_Regiao_Vendedor':
                display_parts.append(f"🗺️ Região Vendedor: **{value}**")
            else:
                display_parts.append(f"👨‍💼 {key}: **{value}**")
        display_parts.append("")

    # Adicionar rodapé informativo se houver filtros
    if any([temporal_filters, region_filters, client_filters, product_filters, representative_filters]):
        display_parts.extend(["---", "💡 *Filtros aplicados à consulta atual*"])

    return "\n".join(display_parts).strip()


def format_sql_query(query):
    """
    Formata uma query SQL para melhor legibilidade
    """
    if not query:
        return query

    # Remove ANSI escape sequences
    query = re.sub(r"\x1b\[[0-9;]*m", "", query)

    # Remove caracteres de controle
    query = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", query)

    # Normaliza espaços em branco
    query = " ".join(query.split())

    # Formata as principais palavras-chave SQL
    keywords = [
        "SELECT", "FROM", "WHERE", "JOIN", "LEFT JOIN", "RIGHT JOIN", "INNER JOIN",
        "GROUP BY", "ORDER BY", "HAVING", "UNION", "INSERT", "UPDATE", "DELETE", "AS"
    ]

    formatted_query = query
    for keyword in keywords:
        # Adiciona quebras de linha antes das principais palavras-chave
        if keyword in ["FROM", "WHERE", "GROUP BY", "ORDER BY", "HAVING"]:
            formatted_query = re.sub(
                f" {keyword} ", f"\n{keyword} ", formatted_query, flags=re.IGNORECASE
            )
        elif keyword == "SELECT":
            formatted_query = re.sub(
                f"^{keyword} ", f"{keyword}\n    ", formatted_query, flags=re.IGNORECASE
            )

    # Ajusta indentação
    lines = formatted_query.split("\n")
    formatted_lines = []
    for line in lines:
        line = line.strip()
        if line.upper().startswith(
            ("SELECT", "FROM", "WHERE", "GROUP BY", "ORDER BY", "HAVING")
        ):
            formatted_lines.append(line)
        else:
            formatted_lines.append("    " + line if line else line)

    return "\n".join(formatted_lines)


def format_compact_number(value):
    """
    Formata números grandes em notação compacta (1M, 2.5M, etc.)
    """
    try:
        if value >= 1_000_000_000:
            return f"{value/1_000_000_000:.1f}B"
        elif value >= 1_000_000:
            return f"{value/1_000_000:.1f}M"
        elif value >= 1_000:
            return f"{value/1_000:.1f}K"
        else:
            return f"{value:.0f}"
    except:
        return str(value)


def detect_categorical_id(labels, column_name=None):
    """
    Detecta se valores são IDs categóricos (ex: Cod_Cliente, Cod_Produto).

    Um valor é considerado ID categórico se:
    1. É um número de 3-8 dígitos, OU
    2. O nome da coluna começa com "Cod_"

    Args:
        labels: Lista de valores ou valor único
        column_name: Nome da coluna (opcional, para detecção por nome)

    Returns:
        dict: {
            'is_categorical': bool,
            'column_type': str  # 'cliente', 'produto', 'vendedor', 'segmento', etc.
        }

    Examples:
        >>> detect_categorical_id(['12345', '67890'], 'Cod_Cliente')
        {'is_categorical': True, 'column_type': 'cliente'}

        >>> detect_categorical_id(['SP', 'RJ', 'MG'])
        {'is_categorical': False, 'column_type': None}
    """
    result = {
        'is_categorical': False,
        'column_type': None
    }

    # Detecção por nome da coluna
    if column_name:
        column_lower = column_name.lower()

        # Verificar se começa com "Cod_"
        if column_name.startswith('Cod_') or column_name.startswith('cod_'):
            result['is_categorical'] = True

            # Identificar tipo baseado no nome
            if 'cliente' in column_lower:
                result['column_type'] = 'cliente'
            elif 'produto' in column_lower:
                result['column_type'] = 'produto'
            elif 'vendedor' in column_lower or 'representante' in column_lower:
                result['column_type'] = 'vendedor'
            elif 'segmento' in column_lower:
                result['column_type'] = 'segmento'
            elif 'familia' in column_lower:
                result['column_type'] = 'familia'
            elif 'grupo' in column_lower:
                result['column_type'] = 'grupo'
            elif 'linha' in column_lower:
                result['column_type'] = 'linha'
            elif 'regiao' in column_lower:
                result['column_type'] = 'regiao'
            else:
                result['column_type'] = 'codigo'

            return result

    # Detecção por conteúdo dos valores
    # Converter para lista se for valor único
    if not isinstance(labels, (list, tuple)):
        labels = [labels]

    # Verificar primeiras 3 amostras
    sample = labels[:3]
    for label in sample:
        label_str = str(label)
        # IDs são tipicamente números de 3-8 dígitos
        if label_str.isdigit() and 3 <= len(label_str) <= 8:
            result['is_categorical'] = True
            # Sem nome de coluna, não podemos determinar o tipo exato
            result['column_type'] = 'codigo'
            break

    return result


def format_categorical_id_label(value, column_type, column_name=None):
    """
    Formata label de ID categórico com prefixo apropriado.

    Args:
        value: Valor do ID (string ou número)
        column_type: Tipo da coluna ('cliente', 'produto', 'vendedor', etc.)
        column_name: Nome original da coluna (opcional, para contexto adicional)

    Returns:
        str: Label formatado com prefixo

    Examples:
        >>> format_categorical_id_label('12345', 'cliente')
        'Cliente 12345'

        >>> format_categorical_id_label('98765', 'produto')
        'Produto 98765'
    """
    value_str = str(value)

    # Mapeamento de tipos para prefixos
    type_prefixes = {
        'cliente': 'Cliente',
        'produto': 'Produto',
        'vendedor': 'Vendedor',
        'representante': 'Representante',
        'segmento': 'Segmento',
        'familia': 'Família',
        'grupo': 'Grupo',
        'linha': 'Linha',
        'regiao': 'Região',
        'codigo': 'Código'
    }

    prefix = type_prefixes.get(column_type, 'Código')

    return f"{prefix} {value_str}"


def detect_and_format_categorical_ids(labels, column_name=None):
    """
    Função auxiliar que detecta E formata IDs categóricos em um único passo.

    Args:
        labels: Lista de valores
        column_name: Nome da coluna (opcional)

    Returns:
        dict: {
            'is_categorical': bool,
            'column_type': str,
            'formatted_labels': list  # Labels formatados se categóricos
        }

    Examples:
        >>> detect_and_format_categorical_ids(['12345', '67890'], 'Cod_Cliente')
        {
            'is_categorical': True,
            'column_type': 'cliente',
            'formatted_labels': ['Cliente 12345', 'Cliente 67890']
        }
    """
    detection = detect_categorical_id(labels, column_name)

    result = {
        'is_categorical': detection['is_categorical'],
        'column_type': detection['column_type'],
        'formatted_labels': labels
    }

    # Se for categórico, formatar labels
    if detection['is_categorical'] and detection['column_type']:
        result['formatted_labels'] = [
            format_categorical_id_label(label, detection['column_type'], column_name)
            for label in labels
        ]

    return result


def escape_currency_for_markdown(text: str) -> str:
    """
    Escapa símbolos de moeda para renderização correta no Streamlit markdown.

    O Streamlit interpreta $ como delimitador de expressões LaTeX matemáticas.
    Esta função adiciona backslash de escape para tratar $ como caractere literal.

    Args:
        text: Texto contendo símbolos de moeda (R$)

    Returns:
        Texto com símbolos de moeda escapados (R\\$)

    Examples:
        >>> escape_currency_for_markdown("Total: R$ 4.1M")
        'Total: R\\$ 4.1M'

        >>> escape_currency_for_markdown("Valores: R$ 1.0M vs R$ 2.0M")
        'Valores: R\\$ 1.0M vs R\\$ 2.0M'

        >>> escape_currency_for_markdown("Já escapado: R\\$ 5.0M")
        'Já escapado: R\\$ 5.0M'  # Não duplica o escape
    """
    if not text:
        return text

    # Substituir R$ por R\$ apenas se ainda não estiver escapado
    # Usar regex para não duplicar backslashes
    text = re.sub(r'R\$(?!\\)', r'R\\$', text)

    return text