"""
Numeric Analyzer - Camada de Análise Numérica para Insights Inteligentes

FASE 2 IMPLEMENTADA:
- Refatorado para separar responsabilidades (cálculos vs formatação)
- numeric_core.py: Cálculos matemáticos puros
- numeric_formatter.py: Formatação para LLM
- Este módulo: Interface pública (mantém compatibilidade)
"""

import pandas as pd
from typing import Dict, Any

# Importar funções dos módulos refatorados
from insights.numeric_core import (
    gerar_resumo_numerico,
    calcular_metricas_ranking,
    calcular_metricas_comparacao,
    calcular_metricas_temporal
)

from insights.numeric_formatter import (
    gerar_prompt_insights,
    formatar_metricas_para_exibicao
)

# Re-exportar funções para manter compatibilidade com código existente
__all__ = [
    'gerar_resumo_numerico',
    'gerar_prompt_insights',
    'formatar_metricas_para_exibicao',
    'calcular_metricas_ranking',
    'calcular_metricas_comparacao',
    'calcular_metricas_temporal'
]
