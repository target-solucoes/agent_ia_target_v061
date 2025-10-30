"""
Sistema de Detecção Inteligente de Remoção de Filtros
Detecta quando o usuário solicita explicitamente a remoção de filtros específicos
e mapeia para os campos correspondentes no sistema de filtros persistentes.

Versão configurável via agent_config.py (zero hardcoding)
"""

import re
from typing import Dict, List, Set, Tuple, Optional
import sys
import os

# Importar configuração centralizada
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config.agent_config import FILTER_REMOVAL_CONFIG


class FilterRemovalDetector:
    """
    Detector de intenções de remoção de filtros baseado em padrões configuráveis.

    Funcionalidades:
    - Detecta comandos de remoção na pergunta do usuário
    - Mapeia termos genéricos para campos específicos
    - Suporta remoção por campo individual ou categoria completa
    - Configurável via FILTER_REMOVAL_CONFIG
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Inicializa o detector com configuração flexível

        Args:
            config: Configuração de remoção (opcional)
                   Se não fornecida, usa FILTER_REMOVAL_CONFIG de agent_config.py
        """
        # Carregar configuração centralizada
        removal_config = config or FILTER_REMOVAL_CONFIG

        # Padrões para detectar intenção de remoção
        self.removal_patterns = removal_config.get("removal_patterns", [])

        # Mapeamento de termos para campos
        self.field_mapping = removal_config.get("field_mapping", {})

        # Mapeamento de categorias para campos
        self.category_mapping = removal_config.get("category_mapping", {})

        # Comandos de limpeza total
        self.clear_all_patterns = removal_config.get("clear_all_patterns", [])

    def detect_removal_intent(self, user_query: str, current_context: Dict) -> Tuple[bool, List[str], bool]:
        """
        Detecta se o usuário quer remover filtros

        Args:
            user_query: Pergunta do usuário
            current_context: Contexto atual de filtros

        Returns:
            Tuple[bool, List[str], bool]:
                (tem_remocao, lista_de_campos_a_remover, limpar_tudo)
        """
        query_lower = user_query.lower().strip()

        # 1. Verificar comando de limpeza total
        if self._is_clear_all_command(query_lower):
            return True, [], True

        # 2. Detectar remoções específicas
        fields_to_remove = self._detect_specific_removals(query_lower, current_context)

        if fields_to_remove:
            return True, fields_to_remove, False

        return False, [], False

    def _is_clear_all_command(self, query_lower: str) -> bool:
        """
        Verifica se é comando de limpeza total de filtros

        Args:
            query_lower: Query em lowercase

        Returns:
            True se é comando de limpeza total
        """
        for pattern in self.clear_all_patterns:
            if re.search(pattern, query_lower):
                return True
        return False

    def _detect_specific_removals(self, query_lower: str, current_context: Dict) -> List[str]:
        """
        Detecta remoções específicas de campos ou categorias

        Args:
            query_lower: Query em lowercase
            current_context: Contexto atual

        Returns:
            Lista de campos a remover
        """
        fields_to_remove = set()

        # Verificar cada padrão de remoção
        for pattern in self.removal_patterns:
            matches = re.finditer(pattern, query_lower)

            for match in matches:
                # Extrair termo mencionado (última captura do regex)
                groups = match.groups()
                if not groups:
                    continue

                mentioned_term = groups[-1].strip()

                # Mapear termo para campos
                mapped_fields = self._map_term_to_fields(mentioned_term, current_context)
                fields_to_remove.update(mapped_fields)

        return list(fields_to_remove)

    def _map_term_to_fields(self, term: str, current_context: Dict) -> Set[str]:
        """
        Mapeia termo genérico para campos específicos

        Args:
            term: Termo mencionado pelo usuário (ex: "cidade", "cliente")
            current_context: Contexto atual de filtros

        Returns:
            Set de campos específicos a remover
        """
        fields = set()

        # 1. Verificar mapeamento direto de campo individual
        if term in self.field_mapping:
            field_candidates = self.field_mapping[term]
            # Adicionar apenas campos que existem no contexto atual
            for field in field_candidates:
                if field in current_context:
                    fields.add(field)

        # 2. Verificar mapeamento de categoria (remove múltiplos campos)
        if term in self.category_mapping:
            category_fields = self.category_mapping[term]
            for field in category_fields:
                if field in current_context:
                    fields.add(field)

        return fields

    def apply_removals(self, current_context: Dict, fields_to_remove: List[str],
                      clear_all: bool = False) -> Tuple[Dict, List[str]]:
        """
        Aplica remoções ao contexto atual

        Args:
            current_context: Contexto atual de filtros
            fields_to_remove: Lista de campos a remover
            clear_all: Se True, limpa todos os filtros

        Returns:
            Tuple[Dict, List[str]]: (contexto_atualizado, lista_de_mudanças)
        """
        changes = []

        # Limpeza total
        if clear_all:
            removed_count = len([v for v in current_context.values()
                               if v is not None and v != [] and v != ""])
            changes.append(f"LIMPEZA TOTAL: {removed_count} filtros removidos")
            return {}, changes

        # Remoção específica
        updated_context = current_context.copy()

        for field in fields_to_remove:
            if field in updated_context:
                old_value = updated_context[field]
                del updated_context[field]
                changes.append(f"REMOÇÃO: {field} = '{old_value}' foi removido")

        if not changes:
            changes.append("INFO: Nenhum filtro correspondente encontrado para remover")

        return updated_context, changes

    def get_removal_summary(self, fields_removed: List[str], clear_all: bool = False) -> str:
        """
        Gera resumo das remoções realizadas

        Args:
            fields_removed: Lista de campos removidos
            clear_all: Se foi limpeza total

        Returns:
            String com resumo
        """
        if clear_all:
            return "Todos os filtros foram removidos"

        if not fields_removed:
            return "Nenhum filtro foi removido"

        count = len(fields_removed)
        if count == 1:
            return f"1 filtro removido: {fields_removed[0]}"
        else:
            return f"{count} filtros removidos: {', '.join(fields_removed)}"


def detect_and_apply_filter_removal(user_query: str, current_context: Dict) -> Tuple[Dict, List[str], bool]:
    """
    Função de conveniência para detectar e aplicar remoção de filtros

    Args:
        user_query: Pergunta do usuário
        current_context: Contexto atual de filtros

    Returns:
        Tuple[Dict, List[str], bool]:
            (contexto_atualizado, lista_de_mudanças, houve_remocao)
    """
    detector = FilterRemovalDetector()

    # Detectar intenção
    has_removal, fields_to_remove, clear_all = detector.detect_removal_intent(
        user_query, current_context
    )

    if not has_removal:
        return current_context, [], False

    # Aplicar remoções
    updated_context, changes = detector.apply_removals(
        current_context, fields_to_remove, clear_all
    )

    return updated_context, changes, True


def preview_removal_impact(user_query: str, current_context: Dict) -> Dict:
    """
    Visualiza impacto da remoção sem aplicar

    Args:
        user_query: Pergunta do usuário
        current_context: Contexto atual

    Returns:
        Dict com informações sobre o impacto
    """
    detector = FilterRemovalDetector()

    has_removal, fields_to_remove, clear_all = detector.detect_removal_intent(
        user_query, current_context
    )

    if not has_removal:
        return {
            "will_remove": False,
            "fields_affected": [],
            "clear_all": False,
            "summary": "Nenhuma remoção detectada"
        }

    summary = detector.get_removal_summary(fields_to_remove, clear_all)

    return {
        "will_remove": True,
        "fields_affected": fields_to_remove,
        "clear_all": clear_all,
        "summary": summary,
        "current_filter_count": len([v for v in current_context.values()
                                    if v is not None and v != [] and v != ""]),
        "remaining_filter_count": 0 if clear_all else len([
            v for k, v in current_context.items()
            if k not in fields_to_remove and v is not None and v != [] and v != ""
        ])
    }
