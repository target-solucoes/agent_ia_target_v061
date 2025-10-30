"""
Testes para o módulo numeric_analyzer.py
Valida a geração de resumo numérico e prompts de insights
"""

import pandas as pd
import sys
import os

# Adicionar src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from insights.numeric_analyzer import (
    gerar_resumo_numerico,
    gerar_prompt_insights,
    formatar_metricas_para_exibicao
)


class TestResumoNumerico:
    """Testes para a função gerar_resumo_numerico"""

    def test_ranking_horizontal_bar(self):
        """Testa geração de resumo para ranking (horizontal bar)"""
        df = pd.DataFrame({
            'categoria': ['Cliente A', 'Cliente B', 'Cliente C', 'Cliente D', 'Cliente E'],
            'vendas': [100000, 56000, 42000, 28000, 14000]
        })

        resumo = gerar_resumo_numerico(df, 'categoria', 'vendas', 'horizontal_bar')

        # Validações básicas
        assert resumo['tipo_grafico'] == 'horizontal_bar'
        assert resumo['num_categorias'] == 5
        assert resumo['total_geral'] == 240000.0
        assert resumo['media'] == 48000.0

        # Validações de ranking
        assert resumo['categoria_max'] == 'Cliente A'
        assert resumo['categoria_min'] == 'Cliente E'
        assert resumo['valor_max'] == 100000.0
        assert resumo['valor_min'] == 14000.0

        # Validações de concentração
        assert 'concentracao_top3_pct' in resumo
        assert resumo['concentracao_top3_pct'] > 70  # Top 3 devem concentrar > 70%

        # Validações de gaps
        assert 'gap_1_2' in resumo
        assert resumo['gap_1_2'] == 44000.0  # 100000 - 56000

        # Validação de múltiplo
        assert 'multiplo_1_vs_2' in resumo
        assert resumo['multiplo_1_vs_2'] > 1.5

        print("OK: Teste de ranking horizontal bar passou!")
        print(formatar_metricas_para_exibicao(resumo))

    def test_comparacao_vertical_bar(self):
        """Testa geração de resumo para comparação (vertical bar)"""
        df = pd.DataFrame({
            'estado': ['SP', 'RJ', 'MG'],
            'faturamento': [1500000, 980000, 720000]
        })

        resumo = gerar_resumo_numerico(df, 'estado', 'faturamento', 'vertical_bar')

        # Validações básicas
        assert resumo['tipo_grafico'] == 'vertical_bar'
        assert resumo['num_categorias'] == 3

        # Validações de comparação
        assert resumo['categoria_maior'] == 'SP'
        assert resumo['categoria_menor'] == 'MG'
        assert 'diferenca_pct' in resumo
        assert resumo['diferenca_pct'] > 100  # SP é mais do que 2x MG

        # Validação de pontos percentuais
        assert 'diferenca_pontos_percentuais' in resumo
        assert resumo['diferenca_pontos_percentuais'] > 0

        print("OK: Teste de comparacao vertical bar passou!")
        print(formatar_metricas_para_exibicao(resumo))

    def test_serie_temporal_line(self):
        """Testa geração de resumo para série temporal (line chart)"""
        df = pd.DataFrame({
            'mes': ['2024-01', '2024-02', '2024-03', '2024-04', '2024-05', '2024-06'],
            'vendas': [100000, 105000, 98000, 112000, 118000, 125000]
        })

        resumo = gerar_resumo_numerico(df, 'mes', 'vendas', 'line')

        # Validações básicas
        assert resumo['tipo_grafico'] == 'line'
        assert resumo['num_periodos'] == 6

        # Validações temporais
        assert resumo['valor_inicial'] == 100000.0
        assert resumo['valor_final'] == 125000.0
        assert resumo['tendencia'] == 'crescente'
        assert 'taxa_crescimento_pct' in resumo
        assert resumo['taxa_crescimento_pct'] == 25.0  # 25% de crescimento

        # Validações de picos e vales
        assert 'pico_valor' in resumo
        assert resumo['pico_valor'] == 125000.0
        assert 'vale_valor' in resumo
        assert resumo['vale_valor'] == 98000.0

        # Validação de amplitude
        assert 'amplitude' in resumo
        assert resumo['amplitude'] == 27000.0  # 125000 - 98000

        print("OK: Teste de serie temporal line passou!")
        print(formatar_metricas_para_exibicao(resumo))

    def test_serie_temporal_decrescente(self):
        """Testa detecção de tendência decrescente"""
        df = pd.DataFrame({
            'trimestre': ['Q1', 'Q2', 'Q3', 'Q4'],
            'receita': [500000, 480000, 450000, 420000]
        })

        resumo = gerar_resumo_numerico(df, 'trimestre', 'receita', 'line')

        assert resumo['tendencia'] == 'decrescente'
        assert resumo['taxa_crescimento_pct'] == -16.0  # -16% de queda

        print("OK: Teste de tendencia decrescente passou!")

    def test_metricas_basicas_sempre_presentes(self):
        """Verifica que métricas básicas estão sempre presentes"""
        df = pd.DataFrame({
            'item': ['A', 'B'],
            'valor': [100, 200]
        })

        resumo = gerar_resumo_numerico(df, 'item', 'valor', 'horizontal_bar')

        # Métricas obrigatórias
        assert 'tipo_grafico' in resumo
        assert 'num_categorias' in resumo
        assert 'total_geral' in resumo
        assert 'media' in resumo
        assert 'mediana' in resumo

        print("OK: Teste de metricas basicas passou!")


class TestPromptInsights:
    """Testes para a função gerar_prompt_insights"""

    def test_prompt_contém_resumo(self):
        """Verifica que o prompt inclui o resumo numérico"""
        resumo = {
            'tipo_grafico': 'horizontal_bar',
            'num_categorias': 5,
            'concentracao_top3_pct': 71.2
        }

        prompt = gerar_prompt_insights(resumo, 'horizontal_bar', max_insights=5)

        assert '71.2' in prompt  # Resumo numérico deve estar no prompt
        assert 'horizontal_bar' in prompt
        assert 'Principais Insights' in prompt

        print("OK: Teste de conteudo do prompt passou!")

    def test_prompt_tem_regras(self):
        """Verifica que o prompt inclui regras de geração"""
        resumo = {'tipo_grafico': 'line'}
        prompt = gerar_prompt_insights(resumo, 'line')

        # Verificar presença de regras
        assert 'O QUE FAZER' in prompt
        assert 'O QUE NÃO FAZER' in prompt
        assert 'ESTRUTURA OBRIGATÓRIA' in prompt

        print("OK: Teste de regras do prompt passou!")

    def test_prompt_adapta_por_tipo(self):
        """Verifica que o prompt se adapta ao tipo de gráfico"""
        resumo_ranking = {'tipo_grafico': 'horizontal_bar'}
        prompt_ranking = gerar_prompt_insights(resumo_ranking, 'horizontal_bar')

        resumo_temporal = {'tipo_grafico': 'line'}
        prompt_temporal = gerar_prompt_insights(resumo_temporal, 'line')

        # Prompts devem conter instruções específicas
        assert 'RANKINGS' in prompt_ranking
        assert 'TEMPORAIS' in prompt_temporal or 'SÉRIES TEMPORAIS' in prompt_temporal

        print("OK: Teste de adaptacao por tipo passou!")


class TestFormatacaoExibicao:
    """Testes para formatação de métricas"""

    def test_formatar_metricas_legivel(self):
        """Verifica que a formatação é legível"""
        resumo = {
            'tipo_grafico': 'horizontal_bar',
            'num_categorias': 5,
            'total_geral': 1000000,
            'media': 200000,
            'concentracao_top3_pct': 75.5
        }

        formatado = formatar_metricas_para_exibicao(resumo)

        assert 'horizontal_bar' in formatado
        assert '5' in formatado  # número de categorias
        assert '1,000,000' in formatado  # total formatado
        assert '75.5%' in formatado  # concentração

        print("OK: Teste de formatacao passou!")
        print(formatado)


def run_all_tests():
    """Executa todos os testes e exibe resultados"""
    print("=" * 60)
    print("EXECUTANDO TESTES DO NUMERIC_ANALYZER")
    print("=" * 60)

    # Instanciar classes de teste
    test_resumo = TestResumoNumerico()
    test_prompt = TestPromptInsights()
    test_formatacao = TestFormatacaoExibicao()

    try:
        # Testes de resumo numérico
        print("\n## TESTES DE RESUMO NUMÉRICO ##\n")
        test_resumo.test_ranking_horizontal_bar()
        print()
        test_resumo.test_comparacao_vertical_bar()
        print()
        test_resumo.test_serie_temporal_line()
        print()
        test_resumo.test_serie_temporal_decrescente()
        print()
        test_resumo.test_metricas_basicas_sempre_presentes()

        # Testes de prompt
        print("\n## TESTES DE PROMPT DE INSIGHTS ##\n")
        test_prompt.test_prompt_contém_resumo()
        print()
        test_prompt.test_prompt_tem_regras()
        print()
        test_prompt.test_prompt_adapta_por_tipo()

        # Testes de formatação
        print("\n## TESTES DE FORMATAÇÃO ##\n")
        test_formatacao.test_formatar_metricas_legivel()

        print("\n" + "=" * 60)
        print("TODOS OS TESTES PASSARAM COM SUCESSO!")
        print("=" * 60)
        return True

    except AssertionError as e:
        print(f"\nERRO NO TESTE: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\nERRO INESPERADO: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
