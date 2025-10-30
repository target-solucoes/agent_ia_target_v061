"""
Core - Lógica central do sistema de filtros
"""

from .extractor import SQLFilterExtractor, extract_filters_from_sql
from .manager import JSONFilterManager, get_json_filter_manager, processar_filtros_apenas_sql
from .replacer import (
    SmartFilterReplacer,
    apply_smart_filter_replacement,
    validate_filter_consistency,
    auto_resolve_filter_conflicts
)

__all__ = [
    'SQLFilterExtractor',
    'extract_filters_from_sql',
    'JSONFilterManager',
    'get_json_filter_manager',
    'processar_filtros_apenas_sql',
    'SmartFilterReplacer',
    'apply_smart_filter_replacement',
    'validate_filter_consistency',
    'auto_resolve_filter_conflicts',
]
