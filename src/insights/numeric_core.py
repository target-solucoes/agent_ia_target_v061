"""
Numeric Core - Cálculos Puros de Métricas Derivadas
Separado da formatação para facilitar manutenção e testabilidade

FASE 3: Otimizado com caching para evitar recalcular métricas
"""

import numpy as np
import pandas as pd
from typing import Dict, Any

# Importar sistema de cache (FASE 3)
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
from performance_cache import cached_metrics


@cached_metrics
def calcular_metricas_ranking(df: pd.DataFrame, label_col: str, value_col: str, total_universo: float = None) -> Dict[str, Any]:
    """
    Calcula métricas para rankings (horizontal bar charts).
    
    Métricas incluídas:
    - Top N categorias
    - Concentração (top 3, top 5) - usando total do universo filtrado
    - Gaps entre posições
    - Desvios da média
    - Múltiplos comparativos
    
    Args:
        df: DataFrame com os dados do ranking (pode ser apenas Top N)
        label_col: Nome da coluna de labels
        value_col: Nome da coluna de valores
        total_universo: Total do universo completo filtrado (para cálculo correto de concentração)
    
    Returns:
        Dicionário com métricas calculadas
    """
    # FASE 3: Otimização - evitar cópias desnecessárias
    # Usar inplace=False explícito (pandas otimiza internamente)
    df_sorted = df.sort_values(value_col, ascending=False).reset_index(drop=True)
    
    # CORREÇÃO CRÍTICA: Usar total_universo se disponível, senão usar total do df
    # O total_universo representa a soma de TODOS os elementos com os filtros ativos
    total = total_universo if total_universo is not None else df_sorted[value_col].sum()
    total_topn = df_sorted[value_col].sum()

    metricas = {
        "top_categorias": df_sorted[label_col].head(3).tolist(),
        "valor_max": float(df_sorted[value_col].iloc[0]),
        "valor_min": float(df_sorted[value_col].iloc[-1]),
        "categoria_max": str(df_sorted[label_col].iloc[0]),
        "categoria_min": str(df_sorted[label_col].iloc[-1]),
        "total_topn": float(total_topn),
        "total_universo": float(total)
    }

    # Concentração - calculada sobre o universo completo
    if len(df_sorted) >= 3:
        top3_sum = df_sorted[value_col].head(3).sum()
        metricas["concentracao_top3_pct"] = round((top3_sum / total) * 100, 1)

    if len(df_sorted) >= 5:
        top5_sum = df_sorted[value_col].head(5).sum()
        metricas["concentracao_top5_pct"] = round((top5_sum / total) * 100, 1)

    # Gaps entre posições
    if len(df_sorted) >= 2:
        gap_1_2 = df_sorted[value_col].iloc[0] - df_sorted[value_col].iloc[1]
        metricas["gap_1_2"] = float(gap_1_2)
        metricas["gap_1_2_pct"] = round((gap_1_2 / df_sorted[value_col].iloc[1]) * 100, 1)

    # Diferença max-min
    diferenca = metricas["valor_max"] - metricas["valor_min"]
    metricas["diferenca_max_min"] = float(diferenca)
    metricas["amplitude_relativa"] = round((diferenca / metricas["valor_min"]) * 100, 1) if metricas["valor_min"] > 0 else None

    # Desvio do líder em relação à média
    media = df_sorted[value_col].mean()
    desvio_lider = metricas["valor_max"] - media
    metricas["desvio_lider_media_pct"] = round((desvio_lider / media) * 100, 1)

    # Múltiplo do líder vs segundo
    if len(df_sorted) >= 2 and df_sorted[value_col].iloc[1] > 0:
        metricas["multiplo_1_vs_2"] = round(df_sorted[value_col].iloc[0] / df_sorted[value_col].iloc[1], 2)

    # Contribuição do líder ao total
    metricas["contribuicao_lider_pct"] = round((metricas["valor_max"] / total) * 100, 1)

    return metricas


@cached_metrics
def calcular_metricas_comparacao(df: pd.DataFrame, label_col: str, value_col: str) -> Dict[str, Any]:
    """
    Calcula métricas para comparações diretas (vertical bar charts com 2-5 itens).
    
    Métricas incluídas:
    - Diferenças percentuais entre categorias
    - Categoria dominante
    - Variação relativa
    - Contribuições ao total
    
    Args:
        df: DataFrame com dados de comparação
        label_col: Nome da coluna de labels
        value_col: Nome da coluna de valores
    
    Returns:
        Dicionário com métricas calculadas
    """
    df_sorted = df.sort_values(value_col, ascending=False).reset_index(drop=True)

    metricas = {
        "categoria_maior": str(df_sorted[label_col].iloc[0]),
        "categoria_menor": str(df_sorted[label_col].iloc[-1]),
        "valor_maior": float(df_sorted[value_col].iloc[0]),
        "valor_menor": float(df_sorted[value_col].iloc[-1])
    }

    # Diferença percentual
    if metricas["valor_menor"] > 0:
        diferenca_pct = ((metricas["valor_maior"] - metricas["valor_menor"]) / metricas["valor_menor"]) * 100
        metricas["diferenca_pct"] = round(diferenca_pct, 1)

    # Diferença de pontos percentuais
    total = df_sorted[value_col].sum()
    pct_maior = (metricas["valor_maior"] / total) * 100
    pct_menor = (metricas["valor_menor"] / total) * 100
    metricas["diferenca_pontos_percentuais"] = round(pct_maior - pct_menor, 1)

    # Contribuição ao total
    metricas["contribuicao_maior_pct"] = round(pct_maior, 1)
    metricas["contribuicao_menor_pct"] = round(pct_menor, 1)

    # Se houver 2 itens, calcular proporção
    if len(df_sorted) == 2:
        metricas["proporcao_relativa"] = f"{round(pct_maior, 0)}% vs {round(pct_menor, 0)}%"

    return metricas


@cached_metrics
def calcular_metricas_temporal(df: pd.DataFrame, date_col: str, value_col: str) -> Dict[str, Any]:
    """
    Calcula métricas para séries temporais (line charts).
    
    Métricas incluídas:
    - Tendência (crescente/decrescente/estável)
    - Taxa de crescimento
    - Picos e vales
    - Variação período a período
    - Aceleração/desaceleração
    
    Args:
        df: DataFrame com série temporal
        date_col: Nome da coluna de datas
        value_col: Nome da coluna de valores
    
    Returns:
        Dicionário com métricas calculadas
    """
    df_sorted = df.sort_values(date_col).reset_index(drop=True)

    metricas = {
        "num_periodos": len(df_sorted),
        "valor_inicial": float(df_sorted[value_col].iloc[0]),
        "valor_final": float(df_sorted[value_col].iloc[-1])
    }

    # Tendência
    if metricas["valor_final"] > metricas["valor_inicial"]:
        metricas["tendencia"] = "crescente"
    elif metricas["valor_final"] < metricas["valor_inicial"]:
        metricas["tendencia"] = "decrescente"
    else:
        metricas["tendencia"] = "estável"

    # Taxa de crescimento total
    if metricas["valor_inicial"] > 0:
        taxa_crescimento = ((metricas["valor_final"] - metricas["valor_inicial"]) / metricas["valor_inicial"]) * 100
        metricas["taxa_crescimento_pct"] = round(taxa_crescimento, 1)

    # Picos e vales
    idx_max = df_sorted[value_col].idxmax()
    idx_min = df_sorted[value_col].idxmin()

    metricas["pico_valor"] = float(df_sorted.loc[idx_max, value_col])
    metricas["pico_periodo"] = str(df_sorted.loc[idx_max, date_col])
    metricas["vale_valor"] = float(df_sorted.loc[idx_min, value_col])
    metricas["vale_periodo"] = str(df_sorted.loc[idx_min, date_col])

    # Amplitude
    metricas["amplitude"] = float(metricas["pico_valor"] - metricas["vale_valor"])
    if metricas["vale_valor"] > 0:
        metricas["amplitude_pct"] = round((metricas["amplitude"] / metricas["vale_valor"]) * 100, 1)

    # Variação média período a período
    if len(df_sorted) > 1:
        variacoes = df_sorted[value_col].pct_change().dropna()
        if len(variacoes) > 0:
            metricas["variacao_media_pct"] = round(variacoes.mean() * 100, 1)
            metricas["volatilidade"] = round(variacoes.std() * 100, 1)

    # Detectar aceleração (segunda metade vs primeira metade)
    if len(df_sorted) >= 6:
        metade = len(df_sorted) // 2
        media_primeira_metade = df_sorted[value_col].iloc[:metade].mean()
        media_segunda_metade = df_sorted[value_col].iloc[metade:].mean()

        if media_primeira_metade > 0:
            aceleracao = ((media_segunda_metade - media_primeira_metade) / media_primeira_metade) * 100
            metricas["aceleracao_segunda_metade_pct"] = round(aceleracao, 1)

            if aceleracao > 10:
                metricas["comportamento_temporal"] = "aceleração no segundo período"
            elif aceleracao < -10:
                metricas["comportamento_temporal"] = "desaceleração no segundo período"
            else:
                metricas["comportamento_temporal"] = "ritmo constante"

    return metricas


def gerar_resumo_numerico(df: pd.DataFrame, eixo_x: str, eixo_y: str, tipo_grafico: str, total_universo: float = None) -> Dict[str, Any]:
    """
    Gera resumo numérico estruturado com métricas derivadas.
    
    Esta função orquestra os cálculos específicos por tipo de gráfico.
    
    Args:
        df: DataFrame com os dados do gráfico
        eixo_x: Nome da coluna do eixo X
        eixo_y: Nome da coluna do eixo Y
        tipo_grafico: Tipo do gráfico
        total_universo: Total do universo completo filtrado
    
    Returns:
        Dicionário com métricas estruturadas
    """
    resumo = {
        "tipo_grafico": tipo_grafico,
        "num_categorias": len(df),
        "total_geral": float(df[eixo_y].sum()),
        "media": float(df[eixo_y].mean()),
        "mediana": float(df[eixo_y].median())
    }

    # Métricas específicas por tipo de gráfico
    if tipo_grafico == "horizontal_bar":
        resumo.update(calcular_metricas_ranking(df, eixo_x, eixo_y, total_universo=total_universo))

    elif tipo_grafico == "vertical_bar":
        resumo.update(calcular_metricas_comparacao(df, eixo_x, eixo_y))

    elif tipo_grafico in ["grouped_vertical_bar", "stacked_bar"]:
        resumo.update(calcular_metricas_comparacao(df, eixo_x, eixo_y))

    elif tipo_grafico == "line":
        resumo.update(calcular_metricas_temporal(df, eixo_x, eixo_y))

    return resumo

