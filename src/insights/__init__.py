"""
Módulo de Insights Inteligentes
Sistema híbrido de geração de insights com análise numérica + LLM
"""

from .numeric_analyzer import gerar_resumo_numerico, gerar_prompt_insights

__all__ = ['gerar_resumo_numerico', 'gerar_prompt_insights']
