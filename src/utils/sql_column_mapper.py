"""
Utilitário para mapear aliases SQL de volta para nomes originais de colunas.

Este módulo resolve o problema de aliases SQL aparecendo nos gráficos.
Quando uma query usa `SUM(Valor_Vendido) AS total_vendas`, o DataFrame
resultante tem a coluna "total_vendas", mas queremos exibir "Valor_Vendido"
nos eixos dos gráficos.
"""

import re
from typing import Optional


def extract_original_column_from_alias(query: str, alias: str) -> Optional[str]:
    """
    Extrai o nome original da coluna a partir de um alias SQL.

    Esta função analisa a query SQL para encontrar a expressão que gera
    o alias fornecido, e extrai o nome da coluna original.

    Padrões suportados:
    - SUM(Valor_Vendido) AS total_vendas → "Valor_Vendido"
    - COUNT(Cod_Cliente) AS total_clientes → "Cod_Cliente"
    - AVG(Qtd_Vendida) AS media → "Qtd_Vendida"
    - MAX(Data) AS data_max → "Data"
    - MIN(Preco) AS preco_min → "Preco"
    - COALESCE(coluna, 0) AS alias → "coluna"
    - coluna AS alias → "coluna"
    - coluna (sem AS) → "coluna"

    Args:
        query: Query SQL completa
        alias: Nome do alias a mapear (ex: "total_vendas")

    Returns:
        Nome original da coluna ou None se não encontrar mapeamento

    Examples:
        >>> query = "SELECT UF_Cliente, SUM(Valor_Vendido) AS total_vendas FROM dados"
        >>> extract_original_column_from_alias(query, "total_vendas")
        "Valor_Vendido"

        >>> query = "SELECT produto, COUNT(cod_cliente) AS total FROM dados"
        >>> extract_original_column_from_alias(query, "total")
        "cod_cliente"
    """
    if not query or not alias:
        return None

    # Normalizar query para facilitar parsing
    query_normalized = ' '.join(query.split())  # Remover múltiplos espaços

    # PADRÃO 1: Funções agregadas com AS
    # Regex: FUNÇÃO(...) AS alias
    # Captura: nome da função, conteúdo dentro dos parênteses, alias
    aggregate_pattern = rf'\b(SUM|COUNT|AVG|MAX|MIN|COALESCE)\s*\(\s*([^)]+)\s*\)\s+AS\s+{re.escape(alias)}\b'
    match = re.search(aggregate_pattern, query_normalized, re.IGNORECASE)

    if match:
        column_expr = match.group(2).strip()
        # Extrair nome da coluna (primeiro identificador)
        # Remove DISTINCT, números, espaços, etc.
        column_name = re.sub(r'\bDISTINCT\b', '', column_expr, flags=re.IGNORECASE).strip()

        # Se há vírgulas (múltiplas colunas, como em COALESCE), pegar primeira
        if ',' in column_name:
            column_name = column_name.split(',')[0].strip()

        # Remover caracteres especiais e validar
        column_name = re.sub(r'[^\w]', '', column_name)

        return column_name if column_name else None

    # PADRÃO 2: Alias simples com AS
    # Regex: coluna AS alias (sem função)
    simple_as_pattern = rf'\b(\w+)\s+AS\s+{re.escape(alias)}\b'
    match = re.search(simple_as_pattern, query_normalized, re.IGNORECASE)

    if match:
        return match.group(1)

    # PADRÃO 3: Coluna sem AS (alias implícito após SELECT)
    # Ex: SELECT Valor_Vendido, Cod_Cliente FROM ...
    # Neste caso, o alias seria o próprio nome da coluna
    # Apenas retornar o alias se ele aparecer como nome de coluna no SELECT
    select_pattern = rf'\bSELECT\s+.*?\b{re.escape(alias)}\b'
    if re.search(select_pattern, query_normalized, re.IGNORECASE):
        # Se o alias aparece diretamente no SELECT sem transformação, é o nome original
        # Verificar se não é precedido por AS (seria outra coisa AS alias)
        not_after_as = rf'(?<!AS\s)\b{re.escape(alias)}\b'
        if re.search(not_after_as, query_normalized, re.IGNORECASE):
            return alias

    # PADRÃO 4: Funções agregadas sem AS (DuckDB permite)
    # Ex: SELECT SUM(Valor_Vendido) FROM ...
    # Neste caso o alias seria algo como "sum(valor_vendido)" ou gerado automaticamente
    # Tentar encontrar função agregada que contenha o alias parcialmente
    no_as_aggregate_pattern = r'\b(SUM|COUNT|AVG|MAX|MIN|COALESCE)\s*\(\s*([^)]+)\s*\)'
    for match in re.finditer(no_as_aggregate_pattern, query_normalized, re.IGNORECASE):
        func_name = match.group(1).lower()
        column_expr = match.group(2).strip()

        # Verificar se o alias se parece com a função aplicada
        # Ex: alias="sum" e func="SUM" ou alias contém parte do nome da coluna
        column_name = re.sub(r'\bDISTINCT\b', '', column_expr, flags=re.IGNORECASE).strip()
        if ',' in column_name:
            column_name = column_name.split(',')[0].strip()
        column_name = re.sub(r'[^\w]', '', column_name)

        # Se alias contém parte do nome da coluna ou função, provavelmente é este
        if column_name.lower() in alias.lower() or func_name in alias.lower():
            return column_name if column_name else None

    # Não conseguiu mapear - retornar None
    return None


def extract_all_column_mappings(query: str) -> dict:
    """
    Extrai todos os mapeamentos de aliases para colunas originais de uma query.

    Args:
        query: Query SQL completa

    Returns:
        Dicionário {alias: coluna_original}

    Examples:
        >>> query = "SELECT UF_Cliente, SUM(Valor_Vendido) AS total, COUNT(*) AS qtd FROM dados"
        >>> extract_all_column_mappings(query)
        {'total': 'Valor_Vendido', 'qtd': None, 'UF_Cliente': 'UF_Cliente'}
    """
    if not query:
        return {}

    mappings = {}
    query_normalized = ' '.join(query.split())

    # Extrair parte do SELECT (antes do FROM)
    select_match = re.search(r'\bSELECT\s+(.*?)\s+FROM\b', query_normalized, re.IGNORECASE | re.DOTALL)
    if not select_match:
        return mappings

    select_clause = select_match.group(1)

    # Dividir por vírgulas (cuidado com funções que têm vírgulas internas)
    # Usar regex para split inteligente
    columns = re.split(r',(?![^()]*\))', select_clause)

    for col_expr in columns:
        col_expr = col_expr.strip()

        # Tentar extrair alias (parte depois de AS)
        as_match = re.search(r'\s+AS\s+(\w+)\s*$', col_expr, re.IGNORECASE)
        if as_match:
            alias = as_match.group(1)
            # Usar extract_original_column_from_alias para mapear
            original = extract_original_column_from_alias(query, alias)
            mappings[alias] = original
        else:
            # Sem AS - assumir que o alias é o próprio nome da coluna
            # Extrair último identificador
            col_name = re.findall(r'\b(\w+)\b', col_expr)
            if col_name:
                alias = col_name[-1]
                mappings[alias] = alias

    return mappings


# Função auxiliar para testes
def _test_sql_column_mapper():
    """Testes unitários para validar o mapeamento"""
    test_cases = [
        # (query, alias, expected_result)
        (
            "SELECT UF_Cliente, SUM(Valor_Vendido) AS total_vendas FROM dados_comerciais GROUP BY UF_Cliente",
            "total_vendas",
            "Valor_Vendido"
        ),
        (
            "SELECT Cod_Cliente, COUNT(DISTINCT Cod_Produto) AS total_produtos FROM dados GROUP BY Cod_Cliente",
            "total_produtos",
            "Cod_Produto"
        ),
        (
            "SELECT estado, AVG(Qtd_Vendida) AS media_qtd FROM vendas GROUP BY estado",
            "media_qtd",
            "Qtd_Vendida"
        ),
        (
            "SELECT MAX(Data) AS data_maxima, MIN(Data) AS data_minima FROM dados",
            "data_maxima",
            "Data"
        ),
        (
            "SELECT produto AS nome_produto, valor FROM dados",
            "nome_produto",
            "produto"
        ),
        (
            "SELECT Cod_Cliente, Valor_Vendido FROM dados WHERE UF_Cliente = 'SP'",
            "Valor_Vendido",
            "Valor_Vendido"  # Sem alias, retorna o próprio nome
        ),
    ]

    print("Testando sql_column_mapper.py...")
    passed = 0
    failed = 0

    for query, alias, expected in test_cases:
        result = extract_original_column_from_alias(query, alias)
        if result == expected:
            print(f"[PASS] '{alias}' -> '{result}'")
            passed += 1
        else:
            print(f"[FAIL] '{alias}' -> '{result}' (esperado: '{expected}')")
            failed += 1

    print(f"\n{passed} testes passaram, {failed} falharam")
    return failed == 0


if __name__ == "__main__":
    # Executar testes se rodado diretamente
    _test_sql_column_mapper()
