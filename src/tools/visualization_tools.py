"""
VisualizationTools - Ferramenta para preparação de metadados de visualização
Permite que o agent crie gráficos DURANTE sua execução, não após.

FASE 3: Otimizado com lazy loading para reduzir tempo de inicialização
"""

from agno.tools import Toolkit
import pandas as pd
import json
from typing import Dict, List, Optional, Any
import sys
import os

# Importar funções de detecção de IDs categóricos
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.formatters import detect_categorical_id, format_categorical_id_label

# FASE 3: Lazy import - carregar apenas quando necessário
_numeric_analyzer_loaded = False
_gerar_resumo_numerico = None
_gerar_prompt_insights = None

def _ensure_numeric_analyzer_loaded():
    """Carrega numeric_analyzer apenas quando necessário (lazy loading)"""
    global _numeric_analyzer_loaded, _gerar_resumo_numerico, _gerar_prompt_insights
    
    if not _numeric_analyzer_loaded:
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        from insights.numeric_analyzer import gerar_resumo_numerico, gerar_prompt_insights
        _gerar_resumo_numerico = gerar_resumo_numerico
        _gerar_prompt_insights = gerar_prompt_insights
        _numeric_analyzer_loaded = True


class VisualizationTools(Toolkit):
    """
    Tool que permite ao agent preparar metadados de visualização durante sua execução.

    O agent pode chamar `prepare_chart()` para criar gráficos de forma integrada
    com sua resposta textual, em vez de depender de post-processing.
    """

    def __init__(self, debug_info_ref=None):
        """
        Inicializa VisualizationTools.

        Args:
            debug_info_ref: Referência ao agent para salvar metadados em debug_info
        """
        super().__init__(name="visualization_tools")
        self.debug_info_ref = debug_info_ref
        self.duckdb_tool_ref = None  # Referência para DuckDbTools
        self.register(self.create_chart_from_last_query)
        self.register(self.prepare_bar_chart)
        self.register(self.prepare_vertical_bar_chart)
        self.register(self.prepare_grouped_vertical_bar_chart)
        self.register(self.prepare_stacked_vertical_bar_chart)
        self.register(self.prepare_line_chart)
        self.register(self.prepare_multi_series_chart)

    def create_chart_from_last_query(
        self,
        title: str,
        chart_type: str = "auto",
        value_format: str = "number",
        x_dimension: Optional[str] = None,
        color_dimension: Optional[str] = None
    ) -> str:
        """
        MÉTODO SIMPLIFICADO - Cria gráfico automaticamente a partir da última query SQL executada.

        Este método acessa automaticamente o resultado da última query DuckDB e cria
        o gráfico apropriado, sem necessidade de extrair dados manualmente.

        Args:
            title: Título do gráfico
            chart_type: Tipo do gráfico ("auto", "bar", "line", "multi_series")
            value_format: Formato dos valores ("number" ou "currency")
            x_dimension: (Opcional) Para gráficos empilhados: nome da coluna para eixo X
            color_dimension: (Opcional) Para gráficos empilhados: nome da coluna para cores

        Returns:
            Mensagem de confirmação

        Examples:
            >>> # Após executar: SELECT Cod_Cliente, SUM(Qtd_Vendida) ...
            >>> create_chart_from_last_query(
            ...     title="Top 5 Clientes por Quantidade",
            ...     chart_type="bar",
            ...     value_format="number"
            ... )
            "✅ Gráfico criado automaticamente: 'Top 5 Clientes' com 5 itens"

            >>> # Com controle explícito de dimensões para gráfico empilhado
            >>> create_chart_from_last_query(
            ...     title="Produtos por Estado",
            ...     chart_type="stacked_vertical_bar",
            ...     x_dimension="Estado",
            ...     color_dimension="Linha_Produto"
            ... )
        """
        # Encontrar DuckDbTools para acessar last_result_df
        if self.duckdb_tool_ref is None:
            if self.debug_info_ref and hasattr(self.debug_info_ref, 'tools'):
                for tool in self.debug_info_ref.tools:
                    if hasattr(tool, 'last_result_df'):
                        self.duckdb_tool_ref = tool
                        break

        if self.duckdb_tool_ref is None:
            return "❌ Erro: Não foi possível acessar resultados SQL"

        if self.duckdb_tool_ref.last_result_df is None or self.duckdb_tool_ref.last_result_df.empty:
            return "❌ Erro: Nenhum resultado SQL disponível para visualização"

        df = self.duckdb_tool_ref.last_result_df

        # Detectar tipo de gráfico automaticamente se necessário
        if chart_type == "auto":
            chart_type = self._detect_chart_type(df)

        # Preparar dimension_order se fornecido
        dimension_order = None
        if x_dimension and color_dimension:
            dimension_order = {
                'x_dimension': x_dimension,
                'color_dimension': color_dimension
            }

        # Criar gráfico baseado no tipo
        if chart_type == "bar":
            return self._create_bar_from_df(df, title, value_format)
        elif chart_type == "vertical_bar":
            return self._create_vertical_bar_from_df(df, title, value_format)
        elif chart_type == "grouped_vertical_bar":
            return self._create_grouped_vertical_bar_from_df(df, title, value_format)
        elif chart_type == "stacked_vertical_bar":
            return self._create_stacked_vertical_bar_from_df(df, title, value_format, dimension_order)
        elif chart_type == "line":
            return self._create_line_from_df(df, title, value_format)
        elif chart_type == "multi_series":
            return self._create_multi_series_from_df(df, title, value_format)
        else:
            return f"❌ Erro: Tipo de gráfico '{chart_type}' não reconhecido"

    def _detect_chart_type(self, df: pd.DataFrame) -> str:
        """Detecta automaticamente o tipo de gráfico baseado na estrutura do DataFrame"""
        if len(df.columns) == 2:
            # 2 colunas: pode ser ranking, comparação ou série temporal
            col1, col2 = df.columns

            # Verificar se primeira coluna parece temporal
            if any(temporal_word in col1.lower() for temporal_word in ['date', 'data', 'mes', 'ano', 'period']):
                return "line"

            # Verificar se é comparação (2-5 itens)
            # Comparações são adequadas para barras verticais
            num_items = len(df)
            if 2 <= num_items <= 5:
                return "vertical_bar"

            # Caso contrário, é ranking (barras horizontais)
            return "bar"
        elif len(df.columns) == 3:
            # 3 colunas: pode ser multi-série temporal, comparação agrupada OU composição empilhada
            col1, col2, col3 = df.columns

            # Verificar se é série temporal (date, category, value)
            is_temporal = any(temporal_word in col1.lower() for temporal_word in ['date', 'data', 'mes', 'ano', 'period'])

            if is_temporal:
                # Gráfico de linha com múltiplas séries
                return "multi_series"
            else:
                # Verificar estrutura das dimensões
                unique_col1 = df[col1].nunique()
                unique_col2 = df[col2].nunique()

                # PRIORIDADE 1: Comparação agrupada temporal (grouped)
                # Critério: primeira coluna com 1-2 valores únicos + segunda coluna com 2-5 únicos
                # Usado para comparações temporais (ex: "SC e PR em março vs abril")
                if 1 <= unique_col1 <= 2 and 2 <= unique_col2 <= 5:
                    # Padrão de comparação agrupada detectado
                    return "grouped_vertical_bar"

                # PRIORIDADE 2: Composição empilhada (stacked)
                # Critério: múltiplas categorias em ambas dimensões
                # Usado para composições (ex: "Top 3 produtos nos 5 clientes")
                # Pelo menos uma dimensão deve ter > 2 valores únicos
                elif unique_col1 >= 2 and unique_col2 >= 2 and (unique_col1 > 2 or unique_col2 > 2):
                    # Estrutura de composição detectada
                    return "stacked_vertical_bar"
                else:
                    # Fallback para multi-série
                    return "multi_series"
        elif len(df.columns) == 4:
            # 4 colunas: pode ser ano + mes + categoria + valor (comparação grupal temporal)
            col1, col2, col3, col4 = df.columns

            # Verificar se primeiras duas colunas são temporais (ano, mes)
            is_temporal_split = (any(word in col1.lower() for word in ['ano', 'year']) and
                                any(word in col2.lower() for word in ['mes', 'month']))

            if is_temporal_split:
                # Consolidar ano+mes e tratar como comparação grupal
                # Critério: poucos períodos + poucas categorias
                # Criar coluna temporária para contar períodos únicos
                df_temp = df.copy()
                df_temp['periodo'] = df_temp[col1].astype(str) + '-' + df_temp[col2].astype(str).str.zfill(2)

                n_periods = df_temp['periodo'].nunique()
                n_categories = df[col3].nunique()

                if 1 <= n_periods <= 2 and 2 <= n_categories <= 5:
                    # Comparação grupal temporal
                    return "grouped_vertical_bar"
                else:
                    # Muitos períodos: série temporal
                    return "multi_series"
            else:
                # Estrutura não reconhecida
                return "bar"
        else:
            # Padrão: gráfico de barras
            return "bar"

    def _consolidate_temporal_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Consolida colunas separadas de ano e mês em uma única coluna de período.

        Detecta estruturas de 4 colunas (ano, mes, categoria, valor) e transforma
        em 3 colunas (periodo, categoria, valor) no formato YYYY-MM.

        Args:
            df: DataFrame com 4 colunas (ano, mes, categoria, valor)

        Returns:
            DataFrame com 3 colunas (periodo, categoria, valor)
        """
        if len(df.columns) != 4:
            return df

        col1, col2, col3, col4 = df.columns

        # Verificar se primeiras duas colunas são temporais
        is_temporal_split = (any(word in col1.lower() for word in ['ano', 'year']) and
                            any(word in col2.lower() for word in ['mes', 'month']))

        if not is_temporal_split:
            return df

        # Criar nova coluna de período consolidada
        df_consolidated = df.copy()

        # Formatar periodo como YYYY-MM (garantir mês com 2 dígitos)
        df_consolidated['periodo'] = (
            df_consolidated[col1].astype(str) + '-' +
            df_consolidated[col2].astype(str).str.zfill(2)
        )

        # Retornar apenas 3 colunas: periodo, categoria, valor
        return df_consolidated[['periodo', col3, col4]]

    def _create_bar_from_df(self, df: pd.DataFrame, title: str, value_format: str) -> str:
        """Cria gráfico de barras a partir do DataFrame"""
        if len(df.columns) < 2:
            return "❌ Erro: DataFrame precisa de pelo menos 2 colunas"

        # Assumir: primeira coluna = labels, segunda coluna = values
        labels = df.iloc[:, 0].astype(str).tolist()
        values = df.iloc[:, 1].astype(float).tolist()

        # Capturar nome da coluna original para exibir no gráfico
        original_col = df.columns[1]

        # Tentar mapear de volta para coluna original se houver query disponível
        if self.duckdb_tool_ref and hasattr(self.duckdb_tool_ref, 'last_query') and self.duckdb_tool_ref.last_query:
            from src.utils.sql_column_mapper import extract_original_column_from_alias
            mapped_col = extract_original_column_from_alias(
                self.duckdb_tool_ref.last_query, original_col
            )
            original_value_column = mapped_col if mapped_col else original_col
        else:
            original_value_column = original_col

        return self.prepare_bar_chart(labels, values, title, value_format, original_value_column=original_value_column)

    def _create_vertical_bar_from_df(self, df: pd.DataFrame, title: str, value_format: str) -> str:
        """Cria gráfico de barras verticais a partir do DataFrame"""
        if len(df.columns) < 2:
            return "❌ Erro: DataFrame precisa de pelo menos 2 colunas"

        # Assumir: primeira coluna = labels, segunda coluna = values
        labels = df.iloc[:, 0].astype(str).tolist()
        values = df.iloc[:, 1].astype(float).tolist()

        # Capturar nome da coluna original para exibir no gráfico
        original_col = df.columns[1]

        # Tentar mapear de volta para coluna original se houver query disponível
        if self.duckdb_tool_ref and hasattr(self.duckdb_tool_ref, 'last_query') and self.duckdb_tool_ref.last_query:
            from src.utils.sql_column_mapper import extract_original_column_from_alias
            mapped_col = extract_original_column_from_alias(
                self.duckdb_tool_ref.last_query, original_col
            )
            original_value_column = mapped_col if mapped_col else original_col
        else:
            original_value_column = original_col

        return self.prepare_vertical_bar_chart(labels, values, title, value_format, original_value_column=original_value_column)

    def _create_grouped_vertical_bar_from_df(self, df: pd.DataFrame, title: str, value_format: str) -> str:
        """Cria gráfico de barras verticais agrupadas a partir do DataFrame"""

        # SUPORTE PARA 4 COLUNAS: consolidar ano+mes antes de processar
        if len(df.columns) == 4:
            df = self._consolidate_temporal_columns(df)

        if len(df.columns) < 3:
            return "❌ Erro: DataFrame precisa de 3 colunas (grupo, categoria, valor)"

        # Assumir: primeira coluna = grupos, segunda coluna = categorias, terceira coluna = values
        groups = df.iloc[:, 0].astype(str).tolist()
        categories = df.iloc[:, 1].astype(str).tolist()
        values = df.iloc[:, 2].astype(float).tolist()

        # Capturar nome da coluna original para exibir no gráfico
        original_col = df.columns[2]  # Terceira coluna = valores

        # Tentar mapear de volta para coluna original se houver query disponível
        if self.duckdb_tool_ref and hasattr(self.duckdb_tool_ref, 'last_query') and self.duckdb_tool_ref.last_query:
            from src.utils.sql_column_mapper import extract_original_column_from_alias
            mapped_col = extract_original_column_from_alias(
                self.duckdb_tool_ref.last_query, original_col
            )
            original_value_column = mapped_col if mapped_col else original_col
        else:
            original_value_column = original_col

        # Nomes das colunas para labels
        x_label = df.columns[0]
        y_label = original_value_column

        return self.prepare_grouped_vertical_bar_chart(
            groups, categories, values, title, value_format,
            original_value_column=original_value_column,
            x_label=x_label,
            y_label=y_label
        )

    def _create_stacked_vertical_bar_from_df(
        self,
        df: pd.DataFrame,
        title: str,
        value_format: str,
        dimension_order: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Cria gráfico de barras verticais empilhadas a partir do DataFrame

        Args:
            df: DataFrame com 3 colunas (2 dimensões categóricas + 1 valor numérico)
            title: Título do gráfico
            value_format: Formato dos valores ("number", "currency", "percentage")
            dimension_order: Opcional. Dicionário com:
                - 'x_dimension': nome da coluna que deve ir no eixo X
                - 'color_dimension': nome da coluna que deve ir nas cores da legenda
                Se fornecido, essa ordem será respeitada. Se None, usa heurística de cardinalidade.

        Returns:
            String com comando preparado para renderização do gráfico
        """
        if len(df.columns) < 3:
            return "❌ Erro: DataFrame precisa de 3 colunas (main_category, sub_category, value)"

        # NOVO: Detecção inteligente de coluna de valores (independente da ordem)
        # Identificar qual coluna é numérica (valores) e quais são categóricas (dimensões)
        numeric_cols = []
        categorical_cols = []

        for col in df.columns[:3]:
            col_lower = col.lower()

            # PRIORIDADE 1: Verificar por NOME da coluna
            # Colunas de valores têm nomes específicos
            is_value_column = any(kw in col_lower for kw in [
                'valor', 'total', 'quantidade', 'qtd', 'preco', 'sum', 'avg', 'count',
                'vendido', 'faturamento', 'receita', 'custo', 'lucro'
            ])

            # Colunas com prefixo "Cod_" são IDs categóricos
            is_id_column = col.startswith('Cod_') or col.startswith('cod_')

            if is_value_column:
                # É coluna de valores (por nome)
                numeric_cols.append(col)
            elif is_id_column:
                # É coluna de ID categórico (por nome)
                categorical_cols.append(col)
            else:
                # PRIORIDADE 2: Verificar por CONTEÚDO
                # Detectar IDs categóricos por padrão numérico
                detection = detect_categorical_id(df[col].head().tolist(), col)

                if detection['is_categorical']:
                    # É um ID categórico (por conteúdo)
                    categorical_cols.append(col)
                elif pd.api.types.is_numeric_dtype(df[col]):
                    # É numérico E não é ID categórico - é valor numérico real
                    numeric_cols.append(col)
                else:
                    # Tentar converter para numérico e verificar se tem valores válidos
                    try:
                        numeric_values = pd.to_numeric(df[col], errors='coerce')
                        # Se >50% dos valores são numéricos, considerar numérica
                        if numeric_values.notna().sum() / len(df) > 0.5:
                            numeric_cols.append(col)
                        else:
                            categorical_cols.append(col)
                    except:
                        categorical_cols.append(col)

        # Validar estrutura: deve ter exatamente 1 coluna numérica e 2 categóricas
        if len(numeric_cols) != 1 or len(categorical_cols) != 2:
            # Fallback: assumir ordem tradicional (col1, col2, col3)
            col1, col2, col3 = df.columns[:3]
            value_col = col3
            dim_col1 = col1
            dim_col2 = col2
        else:
            # Usar detecção inteligente
            value_col = numeric_cols[0]
            dim_col1 = categorical_cols[0]
            dim_col2 = categorical_cols[1]

        # DECISÃO: Qual dimensão usar como main_category (eixo X)?

        # PRIORIDADE 1: Se dimension_order foi fornecido, usar essa ordem explícita
        if dimension_order and 'x_dimension' in dimension_order and 'color_dimension' in dimension_order:
            x_dim = dimension_order['x_dimension']
            color_dim = dimension_order['color_dimension']

            # Validar que as dimensões especificadas existem no DataFrame
            if x_dim in [dim_col1, dim_col2] and color_dim in [dim_col1, dim_col2] and x_dim != color_dim:
                main_col = x_dim
                sub_col = color_dim
                main_label = x_dim
                sub_label = color_dim
            else:
                # Dimensões inválidas, usar fallback
                dimension_order = None

        # PRIORIDADE 2 (Fallback): Usar heurística de cardinalidade
        if not dimension_order:
            # REGRA: "Sempre o maior conjunto no eixo X"
            # Ou seja, a dimensão com MAIS valores únicos vai para o eixo X
            n_dim1 = df[dim_col1].nunique()
            n_dim2 = df[dim_col2].nunique()

            # Determinar qual é main e qual é sub
            if n_dim1 >= n_dim2:
                # dim1 tem mais ou igual valores únicos → dim1 = main (eixo X)
                main_col = dim_col1
                sub_col = dim_col2
                main_label = dim_col1
                sub_label = dim_col2
            else:
                # dim2 tem mais valores únicos → dim2 = main (eixo X)
                main_col = dim_col2
                sub_col = dim_col1
                main_label = dim_col2
                sub_label = dim_col1

        # Extrair listas
        main_categories = df[main_col].astype(str).tolist()
        sub_categories = df[sub_col].astype(str).tolist()
        values = df[value_col].astype(float).tolist()

        # Capturar nome da coluna original para exibir no gráfico
        original_col = value_col  # CORRIGIDO: usar value_col detectado automaticamente

        # Tentar mapear de volta para coluna original se houver query disponível
        if self.duckdb_tool_ref and hasattr(self.duckdb_tool_ref, 'last_query') and self.duckdb_tool_ref.last_query:
            from src.utils.sql_column_mapper import extract_original_column_from_alias
            mapped_col = extract_original_column_from_alias(
                self.duckdb_tool_ref.last_query, original_col
            )
            original_value_column = mapped_col if mapped_col else original_col
        else:
            original_value_column = original_col

        return self.prepare_stacked_vertical_bar_chart(
            main_categories, sub_categories, values, title, value_format,
            original_value_column=original_value_column,
            main_label=main_label,
            sub_label=sub_label
        )

    def _create_line_from_df(self, df: pd.DataFrame, title: str, value_format: str) -> str:
        """Cria gráfico de linha a partir do DataFrame"""
        if len(df.columns) < 2:
            return "❌ Erro: DataFrame precisa de pelo menos 2 colunas"

        # Assumir: primeira coluna = dates, segunda coluna = values
        dates = df.iloc[:, 0].astype(str).tolist()
        values = df.iloc[:, 1].astype(float).tolist()

        # Capturar nome da coluna original para exibir no gráfico
        original_col = df.columns[1]

        # Tentar mapear de volta para coluna original se houver query disponível
        if self.duckdb_tool_ref and hasattr(self.duckdb_tool_ref, 'last_query') and self.duckdb_tool_ref.last_query:
            from src.utils.sql_column_mapper import extract_original_column_from_alias
            mapped_col = extract_original_column_from_alias(
                self.duckdb_tool_ref.last_query, original_col
            )
            original_value_column = mapped_col if mapped_col else original_col
        else:
            original_value_column = original_col

        return self.prepare_line_chart(dates, values, title, y_label=original_value_column, value_format=value_format)

    def _create_multi_series_from_df(self, df: pd.DataFrame, title: str, value_format: str) -> str:
        """Cria gráfico multi-série a partir do DataFrame"""

        # SUPORTE PARA 4 COLUNAS: consolidar ano+mes antes de processar
        if len(df.columns) == 4:
            df = self._consolidate_temporal_columns(df)

        if len(df.columns) < 3:
            return "❌ Erro: DataFrame precisa de 3 colunas para multi-série"

        # Validar que não há valores None/null nas primeiras 3 colunas
        if df.iloc[:, :3].isnull().any().any():
            return "❌ Erro: DataFrame contém valores None/null nas primeiras 3 colunas"

        # Assumir: primeira coluna = dates, segunda = categories, terceira = values
        try:
            dates = df.iloc[:, 0].astype(str).tolist()
            categories = df.iloc[:, 1].astype(str).tolist()
            values = df.iloc[:, 2].astype(float).tolist()
        except (ValueError, TypeError) as e:
            return f"❌ Erro ao converter dados: {str(e)}"

        # Capturar nome da coluna original para exibir no gráfico
        original_col = df.columns[2]  # Terceira coluna = valores

        # Tentar mapear de volta para coluna original se houver query disponível
        if self.duckdb_tool_ref and hasattr(self.duckdb_tool_ref, 'last_query') and self.duckdb_tool_ref.last_query:
            from src.utils.sql_column_mapper import extract_original_column_from_alias
            mapped_col = extract_original_column_from_alias(
                self.duckdb_tool_ref.last_query, original_col
            )
            original_value_column = mapped_col if mapped_col else original_col
        else:
            original_value_column = original_col

        return self.prepare_multi_series_chart(dates, categories, values, title, y_label=original_value_column, value_format=value_format)

    def prepare_bar_chart(
        self,
        labels: List[str],
        values: List[float],
        title: str,
        value_format: str = "number",
        original_value_column: str = None
    ) -> str:
        """
        Prepara gráfico de barras horizontal para rankings ou top N.

        Args:
            labels: Lista de rótulos (nomes de produtos, clientes, etc.)
            values: Lista de valores numéricos correspondentes
            title: Título do gráfico
            value_format: Formato dos valores ("number" ou "currency")
            original_value_column: Nome original da coluna de valores para exibir no eixo

        Returns:
            Mensagem de confirmação

        Examples:
            >>> prepare_bar_chart(
            ...     labels=["Produto A", "Produto B", "Produto C"],
            ...     values=[1000000, 800000, 600000],
            ...     title="Top 3 Produtos Mais Vendidos",
            ...     value_format="currency"
            ... )
            "✅ Gráfico de barras preparado com 3 itens"
        """
        if len(labels) != len(values):
            return "❌ Erro: número de labels e values deve ser igual"

        if not labels or not values:
            return "❌ Erro: labels e values não podem estar vazios"

        # Criar DataFrame no formato esperado por plotly_charts
        df = pd.DataFrame({
            'label': labels,
            'value': values
        })

        # VALIDAÇÃO CRÍTICA: Verificar se DataFrame tem dados válidos
        if df.empty:
            return "⚠️ Aviso: DataFrame criado está vazio - visualização não será exibida"

        if len(df) == 0:
            return "⚠️ Aviso: DataFrame não tem linhas - visualização não será exibida"

        # Preparar metadados de visualização
        viz_metadata = {
            'type': 'bar_chart',
            'data': df,
            'has_data': not df.empty and len(df) > 0,  # Validação real do DataFrame
            'config': {
                'title': title,
                'value_format': value_format,
                'is_categorical_id': self._detect_categorical_ids(labels),
                'original_value_column': original_value_column
            }
        }

        # Salvar em debug_info para captura por app.py
        self._save_visualization_metadata(viz_metadata)

        # NOVO: Verificar se numeric_summary foi gerado e incluir prompt de insights
        insights_prompt = viz_metadata.get('insights_prompt', '')

        base_msg = f"✅ Gráfico de barras preparado: '{title}' com {len(labels)} itens"

        if insights_prompt:
            # Incluir prompt estruturado para geração de insights
            return f"{base_msg}\n\n{insights_prompt}"
        else:
            return base_msg

    def prepare_vertical_bar_chart(
        self,
        labels: List[str],
        values: List[float],
        title: str,
        value_format: str = "number",
        original_value_column: str = None
    ) -> str:
        """
        Prepara gráfico de barras verticais para comparações diretas.

        Args:
            labels: Lista de rótulos (nomes de estados, produtos, clientes, períodos)
            values: Lista de valores numéricos correspondentes
            title: Título do gráfico
            value_format: Formato dos valores ("number" ou "currency")
            original_value_column: Nome original da coluna de valores para exibir no eixo

        Returns:
            Mensagem de confirmação

        Examples:
            >>> prepare_vertical_bar_chart(
            ...     labels=["São Paulo", "Rio de Janeiro", "Minas Gerais"],
            ...     values=[5000000, 3500000, 2800000],
            ...     title="Comparação de Vendas por Estado",
            ...     value_format="currency"
            ... )
            "✅ Gráfico de barras verticais preparado com 3 itens"
        """
        if len(labels) != len(values):
            return "❌ Erro: número de labels e values deve ser igual"

        if not labels or not values:
            return "❌ Erro: labels e values não podem estar vazios"

        # Validar se é apropriado para comparação (2-5 itens idealmente)
        if len(labels) > 10:
            return f"⚠️ Aviso: {len(labels)} itens podem não ser ideais para comparação direta. Considere usar prepare_bar_chart para rankings."

        # Criar DataFrame no formato esperado por plotly_charts
        df = pd.DataFrame({
            'label': labels,
            'value': values
        })

        # VALIDAÇÃO CRÍTICA: Verificar se DataFrame tem dados válidos
        if df.empty or len(df) == 0:
            return "⚠️ Aviso: DataFrame criado está vazio - visualização não será exibida"

        # Preparar metadados de visualização
        viz_metadata = {
            'type': 'vertical_bar_chart',
            'data': df,
            'has_data': not df.empty and len(df) > 0,  # Validação real do DataFrame
            'config': {
                'title': title,
                'value_format': value_format,
                'is_categorical_id': self._detect_categorical_ids(labels),
                'original_value_column': original_value_column
            }
        }

        # Salvar em debug_info para captura por app.py
        self._save_visualization_metadata(viz_metadata)

        # NOVO: Verificar se numeric_summary foi gerado e incluir prompt de insights
        insights_prompt = viz_metadata.get('insights_prompt', '')

        base_msg = f"✅ Gráfico de barras verticais preparado: '{title}' com {len(labels)} itens"

        if insights_prompt:
            return f"{base_msg}\n\n{insights_prompt}"
        else:
            return base_msg

    def prepare_grouped_vertical_bar_chart(
        self,
        groups: List[str],
        categories: List[str],
        values: List[float],
        title: str,
        value_format: str = "number",
        original_value_column: str = None,
        x_label: str = "Período/Item",
        y_label: str = "Valor"
    ) -> str:
        """
        Prepara gráfico de barras verticais agrupadas para comparações diretas entre poucos itens/períodos.

        Este método é ideal para comparações visuais claras entre 1-2 grupos (períodos ou itens)
        com 2-5 categorias cada, usando cores distintas para cada categoria.

        Args:
            groups: Lista de grupos/períodos (ex: ["Março 2015", "Abril 2015"])
            categories: Lista de categorias correspondentes (ex: ["SC", "PR", "RS", "SC", "PR", "RS"])
            values: Lista de valores numéricos correspondentes
            title: Título do gráfico
            value_format: Formato dos valores ("number" ou "currency")
            original_value_column: Nome original da coluna de valores para exibir no eixo
            x_label: Rótulo do eixo X
            y_label: Rótulo do eixo Y

        Returns:
            Mensagem de confirmação

        Examples:
            >>> # Comparação entre março e abril para SC, PR e RS
            >>> prepare_grouped_vertical_bar_chart(
            ...     groups=["Março 2015", "Março 2015", "Março 2015", "Abril 2015", "Abril 2015", "Abril 2015"],
            ...     categories=["SC", "PR", "RS", "SC", "PR", "RS"],
            ...     values=[1000, 800, 900, 1200, 950, 1100],
            ...     title="Vendas por Estado - Março vs Abril 2015",
            ...     value_format="number"
            ... )
            "✅ Gráfico de barras agrupadas preparado: 2 grupos × 3 categorias"
        """
        # Validação básica
        if not (len(groups) == len(categories) == len(values)):
            return "❌ Erro: groups, categories e values devem ter mesmo tamanho"

        if not groups or not categories or not values:
            return "❌ Erro: entradas não podem estar vazias"

        # Validar número de grupos únicos (1-2)
        unique_groups = list(set(groups))
        if len(unique_groups) > 2:
            return f"❌ Erro: máximo de 2 grupos permitidos (recebido: {len(unique_groups)}). Use outro tipo de gráfico."

        if len(unique_groups) < 1:
            return "❌ Erro: mínimo de 1 grupo necessário"

        # Validar número de categorias únicas (2-5)
        unique_categories = list(set(categories))
        if len(unique_categories) > 5:
            return f"❌ Erro: máximo de 5 categorias permitidas (recebido: {len(unique_categories)}). Use outro tipo de gráfico."

        if len(unique_categories) < 2:
            return f"⚠️ Aviso: mínimo de 2 categorias recomendado (recebido: {len(unique_categories)}). Considere usar prepare_vertical_bar_chart."

        # Criar DataFrame no formato esperado por plotly_charts
        df = pd.DataFrame({
            'group': groups,
            'category': categories,
            'value': values
        })

        # VALIDAÇÃO CRÍTICA: Verificar se DataFrame tem dados válidos
        if df.empty or len(df) == 0:
            return "⚠️ Aviso: DataFrame criado está vazio - visualização não será exibida"

        # Ordenar por grupo e categoria para garantir consistência visual
        df = df.sort_values(['group', 'category'])

        # Preparar metadados de visualização
        viz_metadata = {
            'type': 'grouped_vertical_bar_chart',
            'data': df,
            'has_data': not df.empty and len(df) > 0,  # Validação real do DataFrame
            'config': {
                'title': title,
                'value_format': value_format,
                'original_value_column': original_value_column or y_label,
                'x_label': x_label,
                'y_label': y_label
            }
        }

        # Salvar em debug_info para captura por app.py
        self._save_visualization_metadata(viz_metadata)

        # NOVO: Verificar se numeric_summary foi gerado e incluir prompt de insights
        insights_prompt = viz_metadata.get('insights_prompt', '')

        base_msg = f"✅ Gráfico de barras agrupadas preparado: '{title}' ({len(unique_groups)} grupos × {len(unique_categories)} categorias)"

        if insights_prompt:
            return f"{base_msg}\n\n{insights_prompt}"
        else:
            return base_msg

    def prepare_stacked_vertical_bar_chart(
        self,
        main_categories: List[str],
        sub_categories: List[str],
        values: List[float],
        title: str,
        value_format: str = "number",
        original_value_column: str = None,
        main_label: str = "Categoria",
        sub_label: str = "Subcategoria"
    ) -> str:
        """
        Prepara gráfico de barras verticais empilhadas para composições.

        Este método é ideal para visualizar CONTRIBUIÇÃO de subcategorias DENTRO de categorias principais.
        Exemplo: "Top 3 linhas de produto nos 5 maiores clientes" mostra como cada linha contribui para cada cliente.

        Args:
            main_categories: Lista de categorias principais (ex: clientes, produtos)
            sub_categories: Lista de subcategorias correspondentes (ex: linhas de produto)
            values: Lista de valores numéricos correspondentes
            title: Título do gráfico
            value_format: Formato dos valores ("number" ou "currency")
            original_value_column: Nome original da coluna de valores para exibir no eixo
            main_label: Rótulo da categoria principal (eixo X)
            sub_label: Rótulo da subcategoria (empilhamento)

        Returns:
            Mensagem de confirmação

        Examples:
            >>> # "Top 3 linhas de produto nos 5 maiores clientes"
            >>> prepare_stacked_vertical_bar_chart(
            ...     main_categories=["Cliente_23700", "Cliente_19114", "Cliente_22910", ...],
            ...     sub_categories=["Linha_A", "Linha_B", "Linha_C", "Linha_A", ...],
            ...     values=[1200000, 800000, 600000, 1500000, ...],
            ...     title="Top 3 Linhas de Produto nos 5 Maiores Clientes",
            ...     value_format="currency",
            ...     main_label="Cliente",
            ...     sub_label="Linha de Produto"
            ... )
            "✅ Gráfico de barras empilhadas preparado: '...' (5 categorias × 3 subcategorias)"
        """
        # Validação básica
        if not (len(main_categories) == len(sub_categories) == len(values)):
            return "❌ Erro: main_categories, sub_categories e values devem ter mesmo tamanho"

        if not main_categories or not sub_categories or not values:
            return "❌ Erro: entradas não podem estar vazias"

        # Validar número de categorias principais (mínimo 2)
        unique_main = list(set(main_categories))
        if len(unique_main) < 2:
            return f"⚠️ Aviso: mínimo de 2 categorias principais necessário (recebido: {len(unique_main)}). Considere usar outro tipo de gráfico."

        # Validar número de subcategorias (mínimo 2)
        unique_sub = list(set(sub_categories))
        if len(unique_sub) < 2:
            return f"⚠️ Aviso: mínimo de 2 subcategorias necessário (recebido: {len(unique_sub)}). Use prepare_vertical_bar_chart para série única."

        # IMPORTANTE: Sistema limitará automaticamente a 5 subcategorias no render
        # (agregando demais em "Outros")

        # NOVO: Detectar se main_categories e sub_categories são IDs categóricos
        main_detection = detect_categorical_id(unique_main, main_label)
        sub_detection = detect_categorical_id(unique_sub, sub_label)

        # Criar DataFrame no formato esperado por plotly_charts
        df = pd.DataFrame({
            'main_category': main_categories,
            'sub_category': sub_categories,
            'value': values
        })

        # VALIDAÇÃO CRÍTICA: Verificar se DataFrame tem dados válidos
        if df.empty or len(df) == 0:
            return "⚠️ Aviso: DataFrame criado está vazio - visualização não será exibida"

        # Ordenar por main_category (por total) e sub_category (por valor dentro de cada main)
        # Isso será refinado no render, mas já organizamos aqui
        main_totals = df.groupby('main_category')['value'].sum().sort_values(ascending=False)
        df['main_category'] = pd.Categorical(
            df['main_category'],
            categories=main_totals.index,
            ordered=True
        )
        df = df.sort_values(['main_category', 'value'], ascending=[True, False])

        # Preparar metadados de visualização
        viz_metadata = {
            'type': 'stacked_vertical_bar_chart',
            'data': df,
            'has_data': not df.empty and len(df) > 0,  # Validação real do DataFrame
            'config': {
                'title': title,
                'value_format': value_format,
                'original_value_column': original_value_column,
                'x_label': main_label,
                'y_label': original_value_column or 'Valor',
                'sub_label': sub_label,
                # NOVO: Adicionar informações de detecção de IDs categóricos
                'is_categorical_id_main': main_detection['is_categorical'],
                'column_type_main': main_detection['column_type'],
                'original_label_column_main': main_label,
                'is_categorical_id_sub': sub_detection['is_categorical'],
                'column_type_sub': sub_detection['column_type'],
                'original_label_column_sub': sub_label
            }
        }

        # Salvar em debug_info para captura por app.py
        self._save_visualization_metadata(viz_metadata)

        # Verificar se numeric_summary foi gerado e incluir prompt de insights
        insights_prompt = viz_metadata.get('insights_prompt', '')

        base_msg = f"Grafico de barras empilhadas preparado: '{title}' ({len(unique_main)} categorias x {len(unique_sub)} subcategorias)"

        if insights_prompt:
            return f"{base_msg}\n\n{insights_prompt}"
        else:
            return base_msg

    def prepare_line_chart(
        self,
        dates: List[str],
        values: List[float],
        title: str,
        x_label: str = "Data",
        y_label: str = "Valor",
        value_format: str = "number"
    ) -> str:
        """
        Prepara gráfico de linha para séries temporais.

        Args:
            dates: Lista de datas (formato: YYYY-MM-DD, YYYY-MM, etc.)
            values: Lista de valores numéricos correspondentes
            title: Título do gráfico
            x_label: Rótulo do eixo X
            y_label: Rótulo do eixo Y
            value_format: Formato dos valores ("number" ou "currency")

        Returns:
            Mensagem de confirmação

        Examples:
            >>> prepare_line_chart(
            ...     dates=["2015-01", "2015-02", "2015-03"],
            ...     values=[1000000, 1200000, 1100000],
            ...     title="Evolução Mensal de Vendas",
            ...     value_format="currency"
            ... )
            "✅ Gráfico de linha preparado com 3 períodos"
        """
        if len(dates) != len(values):
            return "❌ Erro: número de dates e values deve ser igual"

        if not dates or not values:
            return "❌ Erro: dates e values não podem estar vazios"

        # Criar DataFrame no formato esperado por plotly_charts
        df = pd.DataFrame({
            'date': pd.to_datetime(dates),
            'value': values
        })

        # VALIDAÇÃO CRÍTICA: Verificar se DataFrame tem dados válidos
        if df.empty or len(df) == 0:
            return "⚠️ Aviso: DataFrame criado está vazio - visualização não será exibida"

        # Ordenar por data
        df = df.sort_values('date')

        # Preparar metadados de visualização
        viz_metadata = {
            'type': 'line_chart',
            'data': df,
            'has_data': not df.empty and len(df) > 0,  # Validação real do DataFrame
            'config': {
                'title': title,
                'x_label': x_label,
                'y_label': y_label,
                'value_format': value_format
            }
        }

        # Salvar em debug_info para captura por app.py
        self._save_visualization_metadata(viz_metadata)

        # NOVO: Verificar se numeric_summary foi gerado e incluir prompt de insights
        insights_prompt = viz_metadata.get('insights_prompt', '')

        base_msg = f"✅ Gráfico de linha preparado: '{title}' com {len(dates)} períodos"

        if insights_prompt:
            return f"{base_msg}\n\n{insights_prompt}"
        else:
            return base_msg

    def prepare_multi_series_chart(
        self,
        dates: List[str],
        categories: List[str],
        values: List[float],
        title: str,
        x_label: str = "Data",
        y_label: str = "Valor",
        value_format: str = "number"
    ) -> str:
        """
        Prepara gráfico de múltiplas séries para comparações temporais.

        Args:
            dates: Lista de datas (repetidas para cada categoria)
            categories: Lista de categorias (ex: estados, produtos)
            values: Lista de valores correspondentes
            title: Título do gráfico
            x_label: Rótulo do eixo X
            y_label: Rótulo do eixo Y
            value_format: Formato dos valores ("number" ou "currency")

        Returns:
            Mensagem de confirmação

        Examples:
            >>> prepare_multi_series_chart(
            ...     dates=["2015-01", "2015-01", "2015-02", "2015-02"],
            ...     categories=["SP", "RJ", "SP", "RJ"],
            ...     values=[1000000, 800000, 1200000, 900000],
            ...     title="Vendas por Estado",
            ...     value_format="currency"
            ... )
            "✅ Gráfico multi-série preparado com 2 categorias"
        """
        if not (len(dates) == len(categories) == len(values)):
            return "❌ Erro: dates, categories e values devem ter mesmo tamanho"

        if not dates or not categories or not values:
            return "❌ Erro: entradas não podem estar vazias"

        # Validar que não há valores None em dates, categories ou values
        if None in dates or 'None' in dates or any(d is None or str(d).lower() == 'none' for d in dates):
            return "❌ Erro: dates contém valores None"
        if None in categories or 'None' in categories:
            return "❌ Erro: categories contém valores None"
        if None in values:
            return "❌ Erro: values contém valores None"

        # Verificar número de categorias únicas
        unique_categories = list(set(categories))
        if len(unique_categories) > 10:
            return f"❌ Erro: máximo de 10 categorias permitidas (recebido: {len(unique_categories)})"

        # Criar DataFrame no formato esperado por plotly_charts
        try:
            df = pd.DataFrame({
                'date': pd.to_datetime(dates),
                'category': categories,
                'value': values
            })
        except (ValueError, TypeError) as e:
            return f"❌ Erro ao criar DataFrame: {str(e)}"

        # VALIDAÇÃO CRÍTICA: Verificar se DataFrame tem dados válidos
        if df.empty or len(df) == 0:
            return "⚠️ Aviso: DataFrame criado está vazio - visualização não será exibida"

        # Ordenar por data e categoria
        df = df.sort_values(['date', 'category'])

        # Preparar metadados de visualização
        viz_metadata = {
            'type': 'line_chart',
            'data': df,
            'has_data': not df.empty and len(df) > 0,  # Validação real do DataFrame
            'has_multiple_series': True,
            'config': {
                'title': title,
                'x_label': x_label,
                'y_label': y_label,
                'value_format': value_format
            }
        }

        # Salvar em debug_info para captura por app.py
        self._save_visualization_metadata(viz_metadata)

        # NOVO: Verificar se numeric_summary foi gerado e incluir prompt de insights
        insights_prompt = viz_metadata.get('insights_prompt', '')

        n_periods = len(set(dates))
        base_msg = f"✅ Gráfico multi-série preparado: '{title}' com {len(unique_categories)} categorias e {n_periods} períodos"

        if insights_prompt:
            return f"{base_msg}\n\n{insights_prompt}"
        else:
            return base_msg

    def _calcular_total_universo(self) -> Optional[float]:
        """
        Calcula o total do universo completo filtrado para queries Top N.
        
        Detecta se a última query tinha LIMIT (Top N) e executa uma query
        auxiliar SEM o LIMIT para calcular o total correto do universo.
        
        Returns:
            Total do universo completo ou None se não for aplicável
        """
        if self.duckdb_tool_ref is None or not hasattr(self.duckdb_tool_ref, 'last_query'):
            return None
            
        last_query = self.duckdb_tool_ref.last_query
        if not last_query:
            return None
            
        # Detectar se é uma query Top N (tem LIMIT)
        query_upper = last_query.upper()
        if 'LIMIT' not in query_upper:
            return None  # Não é Top N, não precisa de correção
            
        try:
            # Extrair a coluna de valor que está sendo agregada
            # Padrão típico: SELECT col1, SUM(col2) as alias FROM ... WHERE ... ORDER BY ... LIMIT N
            
            # 1. Remover LIMIT e ORDER BY
            query_sem_limit = self._remover_limit_orderby(last_query)
            
            # 2. Extrair a coluna agregada (SUM, COUNT, AVG, etc.)
            coluna_agregada = self._extrair_coluna_agregada(last_query)
            
            if not coluna_agregada:
                return None
                
            # 3. Construir query auxiliar para calcular total do universo
            # Manter WHERE, mas remover GROUP BY, ORDER BY e LIMIT
            query_total = self._construir_query_total(query_sem_limit, coluna_agregada)
            
            if not query_total:
                return None
                
            # 4. Executar query auxiliar
            result_df = self.duckdb_tool_ref.connection.execute(query_total).df()
            
            if result_df.empty or len(result_df.columns) == 0:
                return None
                
            # Pegar o primeiro valor (total)
            total = float(result_df.iloc[0, 0])
            
            return total
            
        except Exception as e:
            # Em caso de erro, retornar None (usará comportamento legado)
            if self.debug_info_ref and hasattr(self.debug_info_ref, 'debug_info'):
                if 'total_universo_errors' not in self.debug_info_ref.debug_info:
                    self.debug_info_ref.debug_info['total_universo_errors'] = []
                self.debug_info_ref.debug_info['total_universo_errors'].append({
                    'error': str(e),
                    'query': last_query
                })
            return None
    
    def _remover_limit_orderby(self, query: str) -> str:
        """Remove LIMIT e ORDER BY da query"""
        import re
        
        # Remover ORDER BY ... LIMIT N (case insensitive)
        query_limpo = re.sub(r'\s+ORDER\s+BY\s+[^;]+LIMIT\s+\d+', '', query, flags=re.IGNORECASE)
        
        # Se ainda houver LIMIT sozinho, remover
        query_limpo = re.sub(r'\s+LIMIT\s+\d+', '', query_limpo, flags=re.IGNORECASE)
        
        # Se ainda houver ORDER BY sozinho, remover
        query_limpo = re.sub(r'\s+ORDER\s+BY\s+[^;]+', '', query_limpo, flags=re.IGNORECASE)
        
        return query_limpo
    
    def _extrair_coluna_agregada(self, query: str) -> Optional[str]:
        """Extrai a coluna que está sendo agregada (SUM, COUNT, etc.)"""
        import re
        
        # Procurar por padrões de agregação
        patterns = [
            r'SUM\s*\(\s*([^\)]+)\s*\)',
            r'COUNT\s*\(\s*([^\)]+)\s*\)',
            r'AVG\s*\(\s*([^\)]+)\s*\)',
            r'MAX\s*\(\s*([^\)]+)\s*\)',
            r'MIN\s*\(\s*([^\)]+)\s*\)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                coluna = match.group(1).strip()
                # Retornar a função agregada completa
                funcao_match = re.search(r'(SUM|COUNT|AVG|MAX|MIN)\s*\([^\)]+\)', query, re.IGNORECASE)
                if funcao_match:
                    return funcao_match.group(0)
        
        return None
    
    def _construir_query_total(self, query_base: str, coluna_agregada: str) -> Optional[str]:
        """Constrói query para calcular total do universo"""
        import re
        
        # Extrair FROM ... WHERE ... (sem GROUP BY)
        # Padrão: SELECT ... FROM table WHERE conditions GROUP BY ...
        
        # 1. Encontrar FROM
        match_from = re.search(r'\bFROM\b', query_base, re.IGNORECASE)
        if not match_from:
            return None
            
        inicio_from = match_from.start()
        
        # 2. Encontrar GROUP BY (se existir)
        match_group = re.search(r'\bGROUP\s+BY\b', query_base, re.IGNORECASE)
        
        if match_group:
            # Pegar até o GROUP BY
            from_where_clause = query_base[inicio_from:match_group.start()].strip()
        else:
            # Pegar até o final
            from_where_clause = query_base[inicio_from:].strip()
        
        # 3. Construir query final
        query_total = f"SELECT {coluna_agregada} as total {from_where_clause}"
        
        return query_total.strip()

    def _detect_categorical_ids(self, labels: List[str]) -> bool:
        """
        Detecta se labels são IDs categóricos (ex: códigos de cliente).

        Args:
            labels: Lista de rótulos

        Returns:
            True se parecem ser IDs categóricos
        """
        if not labels:
            return False

        # Verificar primeiras 3 labels
        sample = labels[:3]
        for label in sample:
            label_str = str(label)
            # IDs são tipicamente números de 3-8 dígitos
            if label_str.isdigit() and 3 <= len(label_str) <= 8:
                return True

        return False

    def _save_visualization_metadata(self, viz_metadata: Dict[str, Any]):
        """
        Salva metadados de visualização em debug_info do agent.

        NOVO: Gera resumo numérico automaticamente para insights inteligentes.
        CORREÇÃO: Detecta Top N e calcula total do universo filtrado corretamente.

        Args:
            viz_metadata: Dicionário com metadados do gráfico
        """
        if self.debug_info_ref is None:
            return

        if not hasattr(self.debug_info_ref, 'debug_info'):
            return

        # NOVA FUNCIONALIDADE: Gerar resumo numérico para insights
        try:
            df = viz_metadata.get('data')
            chart_type = viz_metadata.get('type')

            if df is not None and not df.empty and chart_type:
                # Mapear tipo de gráfico para formato esperado pelo analyzer
                tipo_grafico_map = {
                    'bar_chart': 'horizontal_bar',
                    'vertical_bar_chart': 'vertical_bar',
                    'grouped_vertical_bar_chart': 'grouped_vertical_bar',
                    'line_chart': 'line'
                }

                tipo_grafico = tipo_grafico_map.get(chart_type, 'horizontal_bar')

                # Identificar colunas de eixo X e Y baseado no tipo
                if chart_type == 'grouped_vertical_bar_chart':
                    # Estrutura: group, category, value
                    eixo_x = 'group'
                    eixo_y = 'value'
                elif chart_type == 'line_chart' and 'category' in df.columns:
                    # Multi-série: date, category, value
                    eixo_x = 'date'
                    eixo_y = 'value'
                elif chart_type == 'line_chart':
                    # Série única: date, value
                    eixo_x = 'date'
                    eixo_y = 'value'
                else:
                    # Padrão: label, value
                    eixo_x = 'label'
                    eixo_y = 'value'

                # NOVA FUNCIONALIDADE: Detectar Top N e calcular total do universo
                total_universo = None
                if chart_type == 'bar_chart' and tipo_grafico == 'horizontal_bar':
                    total_universo = self._calcular_total_universo()

                # FASE 3: Lazy loading - carregar numeric_analyzer apenas quando necessário
                _ensure_numeric_analyzer_loaded()
                
                # Gerar resumo numérico com total do universo correto
                resumo_numerico = _gerar_resumo_numerico(df, eixo_x, eixo_y, tipo_grafico, total_universo=total_universo)

                # Gerar prompt de insights para a LLM
                prompt_insights = _gerar_prompt_insights(resumo_numerico, tipo_grafico, max_insights=5)

                # Adicionar ao viz_metadata
                viz_metadata['numeric_summary'] = resumo_numerico
                viz_metadata['insights_prompt'] = prompt_insights

        except Exception as e:
            # Em caso de erro, continuar sem resumo numérico
            # (não bloquear a visualização)
            viz_metadata['numeric_summary_error'] = str(e)

        # Criar lista se não existir
        if 'visualization_metadata' not in self.debug_info_ref.debug_info:
            self.debug_info_ref.debug_info['visualization_metadata'] = []

        # Adicionar metadados (agora com numeric_summary)
        self.debug_info_ref.debug_info['visualization_metadata'].append(viz_metadata)


# Função helper para conversão de resultados SQL para listas
def sql_result_to_lists(result_string: str) -> tuple:
    """
    Converte resultado de query SQL em listas para uso com VisualizationTools.

    Args:
        result_string: String com resultado da query (formato tabular)

    Returns:
        Tupla (labels, values) ou (dates, values) dependendo do conteúdo

    Examples:
        >>> result = "| Produto | Vendas |\\n|---------|--------|\\n| A | 1000 |"
        >>> labels, values = sql_result_to_lists(result)
        >>> print(labels)
        ['A']
        >>> print(values)
        [1000.0]
    """
    lines = result_string.strip().split('\n')
    labels = []
    values = []

    for line in lines:
        line = line.strip()
        # Pular linhas vazias, separadores e cabeçalhos
        if not line or line.startswith('|---') or line.startswith('+-'):
            continue

        # Extrair dados de linha com pipes
        if '|' in line:
            cells = [cell.strip() for cell in line.split('|') if cell.strip()]
            if len(cells) >= 2:
                # Tentar converter segunda célula para número
                try:
                    value = float(cells[-1].replace(',', '').replace('R$', '').strip())
                    labels.append(cells[0])
                    values.append(value)
                except ValueError:
                    continue

    return labels, values
