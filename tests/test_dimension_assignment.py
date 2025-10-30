"""
Testes para o sistema de determinação de eixos em gráficos empilhados

Este módulo testa:
1. QueryIntentAnalyzer - análise de padrões de query
2. VisualizationTools - aplicação de dimension_order
3. Integração completa - comportamento end-to-end
"""

import sys
import os
import pandas as pd
import pytest

# Adicionar src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.query_intent_analyzer import QueryIntentAnalyzer, get_analyzer
from tools.visualization_tools import VisualizationTools


class TestQueryIntentAnalyzer:
    """Testes para o analisador de intenção de query"""

    def setup_method(self):
        """Setup executado antes de cada teste"""
        self.analyzer = QueryIntentAnalyzer()
        self.columns = ['Estado', 'Linha_Produto', 'Total_Vendas', 'UF_Cliente', 'Cod_Produto']

    def test_pattern_for_produtos_para_estados(self):
        """Caso 1: Top 3 linhas de produtos para 5 maiores estados"""
        query = "Qual é o top 3 linhas de produtos para os 5 maiores estados?"

        result = self.analyzer.extract_dimension_order(query, self.columns)

        assert result is not None, "Deveria detectar padrão"
        assert result['x_dimension'] in self.columns, "x_dimension deve estar nas colunas"
        assert result['color_dimension'] in self.columns, "color_dimension deve estar nas colunas"

        # Validar lógica: "para estados" → estados no X
        # A query menciona "linhas de produtos" e depois "estados"
        # Padrão "para [DIM]" indica DIM no eixo X
        print(f"Query: {query}")
        print(f"Resultado: {result}")

        # O padrão esperado é: produtos mencionados primeiro, estados depois
        # "Top N [produtos] para [estados]" → estados no X, produtos nas cores
        assert 'Estado' in result['x_dimension'] or 'UF' in result['x_dimension'], \
            f"Estados deveriam estar no X, mas está: {result['x_dimension']}"

    def test_pattern_for_estados_para_produtos(self):
        """Caso 2: Top 3 estados para 5 maiores linhas de produtos"""
        query = "Qual é o top 3 estados para as 5 maiores linhas de produtos?"

        result = self.analyzer.extract_dimension_order(query, self.columns)

        assert result is not None, "Deveria detectar padrão"
        print(f"Query: {query}")
        print(f"Resultado: {result}")

        # Padrão "para [DIM]" indica DIM no eixo X
        # "Top N [estados] para [produtos]" → produtos no X, estados nas cores
        assert 'Produto' in result['x_dimension'] or 'Linha' in result['x_dimension'], \
            f"Produtos deveriam estar no X, mas está: {result['x_dimension']}"

    def test_pattern_by_estados_por_produto(self):
        """Caso 3: Top N estados por produto"""
        query = "Mostre o top 5 estados por produto"

        result = self.analyzer.extract_dimension_order(query, self.columns)

        assert result is not None, "Deveria detectar padrão"
        print(f"Query: {query}")
        print(f"Resultado: {result}")

        # Padrão "por [DIM]" indica DIM nas cores
        # "Top N [estados] por [produto]" → estados no X, produto nas cores
        assert 'Estado' in result['x_dimension'] or 'UF' in result['x_dimension'], \
            f"Estados deveriam estar no X, mas está: {result['x_dimension']}"

    def test_pattern_in_produtos_nos_estados(self):
        """Caso 4: Produtos nos estados"""
        query = "Mostre os produtos nos estados"

        result = self.analyzer.extract_dimension_order(query, self.columns)

        assert result is not None, "Deveria detectar padrão"
        print(f"Query: {query}")
        print(f"Resultado: {result}")

        # Padrão "nos [DIM]" indica DIM no eixo X
        # "[produtos] nos [estados]" → estados no X, produtos nas cores
        assert 'Estado' in result['x_dimension'] or 'UF' in result['x_dimension'], \
            f"Estados deveriam estar no X, mas está: {result['x_dimension']}"

    def test_first_mentioned_fallback(self):
        """Caso 5: Fallback para primeira dimensão mencionada"""
        query = "Analise a distribuição de estados e produtos"

        result = self.analyzer.extract_dimension_order(query, self.columns)

        # Este caso pode ou não detectar padrão específico
        # Se detectar, deve usar primeira menção
        if result:
            print(f"Query: {query}")
            print(f"Resultado: {result}")
            assert result['confidence'] <= 0.8, "Confiança deve ser menor para fallback"

    def test_no_pattern_detected(self):
        """Caso 6: Query sem padrão claro"""
        query = "Mostre os dados"

        result = self.analyzer.extract_dimension_order(query, ['col1', 'col2'])

        # Pode retornar None ou resultado com baixa confiança
        if result:
            assert result['confidence'] < 0.9, "Confiança deve ser baixa"
        else:
            assert result is None, "Deveria retornar None para queries vagas"

    def test_cache_functionality(self):
        """Caso 7: Validar que cache está funcionando"""
        query = "Top 3 produtos para 5 estados"

        # Primeira chamada
        result1 = self.analyzer.extract_dimension_order(query, self.columns)

        # Segunda chamada (deve vir do cache)
        result2 = self.analyzer.extract_dimension_order(query, self.columns)

        assert result1 == result2, "Cache deve retornar resultado idêntico"

        # Limpar cache e verificar
        self.analyzer.clear_cache()
        result3 = self.analyzer.extract_dimension_order(query, self.columns)

        assert result3 == result1, "Resultado deve ser consistente após limpar cache"


class TestVisualizationToolsDimensionOrder:
    """Testes para VisualizationTools com dimension_order"""

    def setup_method(self):
        """Setup executado antes de cada teste"""
        self.viz_tools = VisualizationTools()

    def test_dimension_order_explicit(self):
        """Caso 8: dimension_order explícito deve ser respeitado"""
        # Criar DataFrame de teste com 5 estados e 3 produtos
        df = pd.DataFrame({
            'Estado': ['SP', 'RJ', 'MG', 'PR', 'SC'] * 3,
            'Produto': ['Produto A'] * 5 + ['Produto B'] * 5 + ['Produto C'] * 5,
            'Vendas': [100, 200, 150, 180, 220, 90, 180, 140, 160, 200, 110, 190, 155, 175, 210]
        })

        # Testar com dimension_order explícito: Estado no X
        dimension_order = {
            'x_dimension': 'Estado',
            'color_dimension': 'Produto'
        }

        result = self.viz_tools._create_stacked_vertical_bar_from_df(
            df=df,
            title="Teste Estados no X",
            value_format="number",
            dimension_order=dimension_order
        )

        # Verificar que não houve erro
        assert "Erro" not in result and "erro" not in result.lower(), \
            f"Não deveria ter erro: {result}"
        assert "preparado" in result.lower() or "criado" in result.lower(), \
            f"Deveria confirmar criação do gráfico. Resultado: {result}"

    def test_dimension_order_reversed(self):
        """Caso 9: dimension_order invertido (Produto no X)"""
        # Criar DataFrame de teste com 5 produtos e 3 estados (15 linhas total)
        df = pd.DataFrame({
            'Estado': ['SP', 'RJ', 'MG'] * 5,
            'Produto': ['Prod A'] * 3 + ['Prod B'] * 3 + ['Prod C'] * 3 + ['Prod D'] * 3 + ['Prod E'] * 3,
            'Vendas': [100, 200, 150, 180, 220, 90, 180, 140, 160, 200, 110, 190, 155, 175, 210]
        })

        # Testar com dimension_order explícito: Produto no X
        dimension_order = {
            'x_dimension': 'Produto',
            'color_dimension': 'Estado'
        }

        result = self.viz_tools._create_stacked_vertical_bar_from_df(
            df=df,
            title="Teste Produtos no X",
            value_format="number",
            dimension_order=dimension_order
        )

        # Verificar que não houve erro
        assert "Erro" not in result and "erro" not in result.lower(), \
            f"Não deveria ter erro: {result}"
        assert "preparado" in result.lower() or "criado" in result.lower(), \
            f"Deveria confirmar criação do gráfico. Resultado: {result}"

    def test_fallback_to_cardinality(self):
        """Caso 10: Sem dimension_order, deve usar cardinalidade"""
        # Criar DataFrame com 5 estados e 3 produtos (estados tem maior cardinalidade)
        df = pd.DataFrame({
            'Estado': ['SP', 'RJ', 'MG', 'PR', 'SC'] * 3,
            'Produto': ['Produto A'] * 5 + ['Produto B'] * 5 + ['Produto C'] * 5,
            'Vendas': [100, 200, 150, 180, 220, 90, 180, 140, 160, 200, 110, 190, 155, 175, 210]
        })

        # Chamar SEM dimension_order (deve usar fallback de cardinalidade)
        result = self.viz_tools._create_stacked_vertical_bar_from_df(
            df=df,
            title="Teste Fallback Cardinalidade",
            value_format="number",
            dimension_order=None  # Explicitamente None
        )

        # Verificar que não houve erro
        assert "❌" not in result, f"Não deveria ter erro: {result}"
        # Com cardinalidade, Estado (5 valores) deve ir para X-axis

    def test_invalid_dimension_order(self):
        """Caso 11: dimension_order inválido deve usar fallback"""
        df = pd.DataFrame({
            'Estado': ['SP', 'RJ', 'MG'] * 3,
            'Produto': ['Prod A'] * 3 + ['Prod B'] * 3 + ['Prod C'] * 3,
            'Vendas': [100, 200, 150, 180, 220, 90, 180, 140, 160]
        })

        # dimension_order com colunas que não existem
        dimension_order = {
            'x_dimension': 'Coluna_Inexistente',
            'color_dimension': 'Outra_Inexistente'
        }

        result = self.viz_tools._create_stacked_vertical_bar_from_df(
            df=df,
            title="Teste Dimension Order Inválido",
            value_format="number",
            dimension_order=dimension_order
        )

        # Deve fazer fallback para cardinalidade e não dar erro
        assert "❌" not in result or "DataFrame precisa de 3 colunas" in result, \
            f"Deveria usar fallback ou dar erro apropriado: {result}"


class TestIntegrationEndToEnd:
    """Testes de integração completa"""

    def setup_method(self):
        """Setup executado antes de cada teste"""
        self.analyzer = get_analyzer()
        self.viz_tools = VisualizationTools()

    def test_complete_flow_produtos_para_estados(self):
        """Caso 12: Fluxo completo - produtos para estados"""
        query = "Top 3 linhas de produtos para os 5 maiores estados"
        columns = ['Estado', 'Linha_Produto', 'Total_Vendas']

        # 1. Analisar query
        dimension_result = self.analyzer.extract_dimension_order(query, columns)

        assert dimension_result is not None, "Analyzer deveria detectar padrão"

        # 2. Criar DataFrame simulado
        df = pd.DataFrame({
            'Estado': ['SP', 'RJ', 'MG', 'PR', 'SC'] * 3,
            'Linha_Produto': ['Premium'] * 5 + ['Standard'] * 5 + ['Economy'] * 5,
            'Total_Vendas': [100, 200, 150, 180, 220, 90, 180, 140, 160, 200, 110, 190, 155, 175, 210]
        })

        # 3. Criar gráfico com dimension_order
        dimension_order = {
            'x_dimension': dimension_result['x_dimension'],
            'color_dimension': dimension_result['color_dimension']
        }

        result = self.viz_tools._create_stacked_vertical_bar_from_df(
            df=df,
            title="Top 3 Linhas por Estado",
            value_format="number",
            dimension_order=dimension_order
        )

        # Verificar sucesso
        assert "Erro" not in result and "erro" not in result.lower(), \
            f"Fluxo completo falhou: {result}"
        print(f"\n[OK] Fluxo completo executado com sucesso!")
        print(f"   Query: {query}")
        print(f"   Dimension Order: {dimension_order}")
        print(f"   Resultado: {result}")


def run_all_tests():
    """Executa todos os testes e mostra resultados"""
    print("\n" + "="*80)
    print("EXECUTANDO TESTES DE DIMENSION ASSIGNMENT")
    print("="*80 + "\n")

    # Executar com pytest
    pytest.main([__file__, "-v", "-s"])


if __name__ == "__main__":
    run_all_tests()
