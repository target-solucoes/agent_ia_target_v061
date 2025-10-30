"""
Sistema de Filtros - v0.6
Módulo responsável por toda a lógica de gerenciamento de filtros do aplicativo.
"""

__version__ = "0.6.0"

# Exports principais
from .core.extractor import SQLFilterExtractor, extract_filters_from_sql
from .core.manager import JSONFilterManager, get_json_filter_manager
from .core.replacer import (
    SmartFilterReplacer,
    apply_smart_filter_replacement,
    validate_filter_consistency,
    auto_resolve_filter_conflicts
)
from .ui.sidebar import (
    filter_user_friendly_context,
    create_enhanced_filter_manager,
    apply_disabled_filters_to_context
)

__all__ = [
    # Extração
    'SQLFilterExtractor',
    'extract_filters_from_sql',
    # Gerenciamento
    'JSONFilterManager',
    'get_json_filter_manager',
    # Substituição Inteligente
    'SmartFilterReplacer',
    'apply_smart_filter_replacement',
    'validate_filter_consistency',
    'auto_resolve_filter_conflicts',
    # UI
    'filter_user_friendly_context',
    'create_enhanced_filter_manager',
    'apply_disabled_filters_to_context',
]
