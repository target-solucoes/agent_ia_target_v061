"""
Ferramenta DuckDB Otimizada com normalização automática de strings e captura de contexto
"""

from agno.tools.duckdb import DuckDbTools
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
# from parsers.sql_context_parser import extract_where_clause_context  # Removido - agora usando sistema JSON
import pandas as pd
import re


class DebugDuckDbTools(DuckDbTools):
    """
    Classe customizada de DuckDbTools que aplica normalização automática
    de strings e captura contexto das queries SQL com cache inteligente
    """

    def __init__(self, debug_info_ref=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.debug_info_ref = debug_info_ref
        self.last_result_df = None  # Armazenar último DataFrame resultado
        self.last_query = None  # Armazenar última query SQL executada (para mapeamento de aliases)

        # Cache inteligente de metadados para evitar queries redundantes
        self.metadata_cache = {
            'tables_exist': set(),  # Tabelas que sabemos que existem
            'table_schemas': {},    # Schema de tabelas já consultadas
            'basic_stats': {},      # Estatísticas básicas já calculadas
            'initialization_done': False,  # Se a inicialização foi concluída
            'recent_queries': {},   # Cache de queries recentes para evitar duplicação
            'last_query_hash': None  # Hash da última query executada
        }

    def _normalize_query_strings(self, query: str) -> str:
        """Aplica normalização LOWER() automaticamente a todas as comparações de strings na query"""

        # Pattern para detectar comparações de strings: coluna = 'valor', coluna LIKE 'valor', etc.
        # Captura: operador de comparação, nome da coluna, operador, valor entre aspas
        patterns = [
            # Igualdade: WHERE coluna = 'valor'
            (r"(\w+)\s*(=)\s*'([^']*)'", r"LOWER(\1) \2 '\3'"),
            # LIKE: WHERE coluna LIKE 'valor'
            (r"(\w+)\s+(LIKE)\s+'([^']*)'", r"LOWER(\1) \2 '\3'"),
            # Igualdade com aspas duplas: WHERE coluna = "valor"
            (r"(\w+)\s*(=)\s*\"([^\"]*)\"", r"LOWER(\1) \2 '\3'"),
            # LIKE com aspas duplas: WHERE coluna LIKE "valor"
            (r"(\w+)\s+(LIKE)\s+\"([^\"]*)\"", r"LOWER(\1) \2 '\3'"),
        ]

        normalized_query = query
        applied_normalizations = []

        for pattern, replacement in patterns:
            # Encontrar todas as correspondências
            matches = re.finditer(pattern, normalized_query, re.IGNORECASE)

            for match in matches:
                column = match.group(1)
                operator = match.group(2)
                value = match.group(3)

                # Converter o valor para lowercase também
                normalized_value = value.lower()

                # Aplicar a substituição com LOWER() na coluna e valor normalizado
                old_text = match.group(0)
                new_text = f"LOWER({column}) {operator} '{normalized_value}'"

                normalized_query = normalized_query.replace(old_text, new_text)
                applied_normalizations.append({
                    "column": column,
                    "operator": operator,
                    "original_value": value,
                    "normalized_value": normalized_value
                })

        # Log das normalizações aplicadas para debug
        if applied_normalizations and self.debug_info_ref and hasattr(self.debug_info_ref, "debug_info"):
            if "string_normalizations" not in self.debug_info_ref.debug_info:
                self.debug_info_ref.debug_info["string_normalizations"] = []
            self.debug_info_ref.debug_info["string_normalizations"].extend(applied_normalizations)

        return normalized_query

    def _is_redundant_metadata_query(self, query: str) -> tuple[bool, str]:
        """
        Detecta se a query é redundante baseada no cache de metadados

        Returns:
            tuple: (is_redundant, cached_result)
        """
        query_lower = query.strip().lower()

        # Detectar queries de metadados básicos
        if query_lower in ['show tables', 'show tables;']:
            if self.metadata_cache['initialization_done'] or 'dados_comerciais' in self.metadata_cache['tables_exist']:
                return True, "┌─────────────────┐\n│      name       │\n├─────────────────┤\n│ dados_comerciais │\n└─────────────────┘"

        elif query_lower.startswith('describe dados_comerciais') or query_lower.startswith('desc dados_comerciais'):
            if 'dados_comerciais' in self.metadata_cache['table_schemas']:
                return True, self.metadata_cache['table_schemas']['dados_comerciais']
            elif self.metadata_cache['initialization_done']:
                # Retornar schema básico se não temos cached mas sabemos que a tabela existe
                return True, "┌─────────────────┬──────────────┬─────────┬─────────┬─────────┬─────────┐\n│   column_name   │ column_type  │  null   │   key   │ default │  extra  │\n├─────────────────┼──────────────┼─────────┼─────────┼─────────┼─────────┤\n│ Table schema available in database │      │         │         │         │\n└─────────────────┴──────────────┴─────────┴─────────┴─────────┴─────────┘"

        elif (query_lower.startswith('select count(*) as total_filas from dados_comerciais') or
              query_lower.startswith('select count(*) from dados_comerciais')):
            if 'dados_comerciais_count' in self.metadata_cache['basic_stats']:
                return True, self.metadata_cache['basic_stats']['dados_comerciais_count']

        # Detectar criação de tabela já existente - incluir variações
        # IMPORTANTE: Apenas bloquear se a tabela foi verificada como funcional
        elif (('create table dados_comerciais' in query_lower or
               'create or replace table dados_comerciais' in query_lower)
              and self.metadata_cache.get('table_verified', False)):
            return True, "Table dados_comerciais already exists and is ready for use."

        return False, ""

    def _cache_query_result(self, query: str, result: str):
        """Cache do resultado da query se for de metadados"""
        query_lower = query.strip().lower()

        if query_lower in ['show tables', 'show tables;'] and 'dados_comerciais' in result.lower():
            self.metadata_cache['tables_exist'].add('dados_comerciais')
            self.metadata_cache['initialization_done'] = True

        elif (query_lower.startswith('describe dados_comerciais') or
              query_lower.startswith('desc dados_comerciais')):
            self.metadata_cache['table_schemas']['dados_comerciais'] = result
            self.metadata_cache['tables_exist'].add('dados_comerciais')
            self.metadata_cache['initialization_done'] = True

        elif (query_lower.startswith('select count(*) as total_filas from dados_comerciais') or
              query_lower.startswith('select count(*) from dados_comerciais')):
            self.metadata_cache['basic_stats']['dados_comerciais_count'] = result
            self.metadata_cache['tables_exist'].add('dados_comerciais')
            self.metadata_cache['initialization_done'] = True

        elif ('create table dados_comerciais' in query_lower or
              'create or replace table dados_comerciais' in query_lower):
            self.metadata_cache['tables_exist'].add('dados_comerciais')
            self.metadata_cache['initialization_done'] = True

    def run_query(self, query: str) -> str:
        """Override do método run_query com normalização automática de strings e captura de contexto"""

        # VERIFICAR CACHE PRIMEIRO para evitar queries redundantes
        is_redundant, cached_result = self._is_redundant_metadata_query(query)
        if is_redundant:
            # Log da otimização
            if self.debug_info_ref and hasattr(self.debug_info_ref, "debug_info"):
                if "cached_queries" not in self.debug_info_ref.debug_info:
                    self.debug_info_ref.debug_info["cached_queries"] = []
                self.debug_info_ref.debug_info["cached_queries"].append({
                    "query": query.strip(),
                    "cache_hit": True,
                    "optimization": "Metadata cache hit - query avoided"
                })
            return cached_result

        # VERIFICAR QUERY DUPLICADA recentemente
        query_hash = hash(query.strip().lower())
        if query_hash == self.metadata_cache['last_query_hash']:
            # Query idêntica executada recentemente
            if query_hash in self.metadata_cache['recent_queries']:
                if self.debug_info_ref and hasattr(self.debug_info_ref, "debug_info"):
                    if "duplicate_queries_avoided" not in self.debug_info_ref.debug_info:
                        self.debug_info_ref.debug_info["duplicate_queries_avoided"] = []
                    self.debug_info_ref.debug_info["duplicate_queries_avoided"].append(query.strip())
                return self.metadata_cache['recent_queries'][query_hash]

        # APLICAR NORMALIZAÇÃO AUTOMÁTICA de todas as strings na query
        normalized_query = self._normalize_query_strings(query)

        # Executar a query normalizada
        result = super().run_query(normalized_query)

        # CACHE o resultado se for metadados
        self._cache_query_result(query, result)

        # CACHE da query recente para evitar duplicação
        self.metadata_cache['recent_queries'][query_hash] = result
        self.metadata_cache['last_query_hash'] = query_hash

        # Limitar cache de queries recentes para evitar vazamento de memória
        if len(self.metadata_cache['recent_queries']) > 10:
            # Remover a query mais antiga
            oldest_hash = min(self.metadata_cache['recent_queries'].keys())
            del self.metadata_cache['recent_queries'][oldest_hash]

        # CAPTURAR DADOS DO RESULTADO para visualização
        try:
            # Tentar executar novamente a query para capturar DataFrame
            if hasattr(self, 'connection') and self.connection:
                df_result = self.connection.execute(normalized_query).df()
                if not df_result.empty:
                    self.last_result_df = df_result
                    # Salvar query que gerou este DataFrame (para mapeamento de aliases)
                    self.last_query = normalized_query
        except Exception as e:
            # Se falhar, tentar extrair dados do resultado textual
            self.last_result_df = self._parse_result_to_dataframe(result)
            # Ainda assim salvar a query
            if self.last_result_df is not None:
                self.last_query = normalized_query

        # Debug info e context extraction
        if self.debug_info_ref is not None and hasattr(
            self.debug_info_ref, "debug_info"
        ):
            if "sql_queries" not in self.debug_info_ref.debug_info:
                self.debug_info_ref.debug_info["sql_queries"] = []
            if "query_contexts" not in self.debug_info_ref.debug_info:
                self.debug_info_ref.debug_info["query_contexts"] = []

            # Usar a query normalizada final
            clean_query = normalized_query.strip()
            if (
                clean_query
                and clean_query not in self.debug_info_ref.debug_info["sql_queries"]
            ):
                self.debug_info_ref.debug_info["sql_queries"].append(clean_query)

                # SEMPRE extrair contexto, mesmo que vazio
                # context = extract_where_clause_context(clean_query)  # Removido - agora usando sistema JSON
                context = {}  # Placeholder - filtros agora extraídos via JSON response
                # Adicionar contexto mesmo se vazio (para garantir que sempre apareça)
                self.debug_info_ref.debug_info["query_contexts"].append(context if context else {})

        return result

    def _parse_result_to_dataframe(self, result_text):
        """Converte resultado textual em DataFrame quando possível"""
        try:
            # Procurar por padrões de tabela no resultado
            lines = result_text.split('\n')
            data_rows = []

            # Procurar por linhas que parecem dados tabulares
            for line in lines:
                line = line.strip()
                if '|' in line or '\t' in line:
                    # Possível linha de dados
                    if '|' in line:
                        cells = [cell.strip() for cell in line.split('|') if cell.strip()]
                    else:
                        cells = [cell.strip() for cell in line.split('\t') if cell.strip()]

                    if len(cells) >= 2:
                        # Tentar converter última célula para número
                        try:
                            value = float(cells[-1].replace(',', '').replace('$', ''))
                            data_rows.append({
                                'label': cells[0],
                                'value': value
                            })
                        except:
                            continue

            return pd.DataFrame(data_rows) if data_rows else None
        except:
            return None