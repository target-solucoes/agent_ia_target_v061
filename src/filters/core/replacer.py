"""
Sistema de Substituição Inteligente de Filtros
Implementa lógica de negócio para detectar quando filtros devem ser substituídos
ao invés de adicionados, baseado na natureza mutuamente exclusiva dos campos.

Versão Refatorada: Carrega configuração de agent_config.py (zero hardcoding)
"""

from typing import Dict, List, Set, Optional, Tuple
import copy
import sys
import os

# Importar configuração centralizada
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from config.agent_config import FILTER_BEHAVIOR_CONFIG


class SmartFilterReplacer:
    """
    Classe responsável por aplicar lógica inteligente de substituição de filtros
    baseada em regras de negócio configuráveis (zero hardcoding).
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Inicializa o sistema de substituição com configuração flexível

        Args:
            config: Configuração de comportamento de filtros (opcional)
                   Se não fornecida, usa FILTER_BEHAVIOR_CONFIG de agent_config.py
        """
        # Carregar configuração centralizada
        filter_config = config or FILTER_BEHAVIOR_CONFIG

        # Campos que são mutuamente exclusivos (apenas um valor por vez)
        self.exclusive_fields = filter_config.get("exclusive_fields", {})

        # Campos que podem ter múltiplos valores simultaneamente
        self.multi_value_fields = filter_config.get("multi_value_fields", set())

        # Grupos de campos relacionados que se sobrepõem
        self.field_groups = filter_config.get("field_groups", {})

    def should_replace_filter(self, field: str, new_value, existing_context: Dict) -> bool:
        """
        Determina se um filtro deve substituir valores existentes

        Args:
            field: Nome do campo
            new_value: Novo valor sendo adicionado
            existing_context: Contexto atual de filtros

        Returns:
            True se deve substituir, False se deve adicionar
        """
        # Verificar se é campo exclusivo
        if field in self.exclusive_fields:
            # Se já existe valor para este campo, substituir
            if field in existing_context and existing_context[field] is not None:
                return True

        # Verificar grupos de campos relacionados
        return self._check_group_conflicts(field, new_value, existing_context)

    def _check_group_conflicts(self, field: str, new_value, existing_context: Dict) -> bool:
        """
        Verifica conflitos dentro de grupos de campos relacionados

        Args:
            field: Nome do campo
            new_value: Novo valor
            existing_context: Contexto existente

        Returns:
            True se há conflito que requer substituição
        """
        # Conflitos temporais
        if field == 'Municipio_Cliente':
            # Nova cidade sempre substitui cidade anterior
            for existing_field in existing_context:
                if existing_field == 'Municipio_Cliente' and existing_context[existing_field]:
                    return True

        elif field in ['Data_>=', 'Data_<']:
            # Novos ranges temporais substituem ranges anteriores
            if 'Data_>=' in existing_context and 'Data_<' in existing_context:
                return True

        elif field == 'Data':
            # Data específica substitui ranges e outras datas específicas
            temporal_fields = ['Data', 'Data_>=', 'Data_<', 'Data_<=', 'Data_>']
            if any(f in existing_context and existing_context[f] for f in temporal_fields):
                return True

        return False

    def _preserve_critical_fields(self, existing_context: Dict, new_filters: Dict,
                                  changes: List[str]) -> Dict:
        """
        FALLBACK DE SEGURANÇA: Preserva campos críticos do contexto existente
        que não foram mencionados nos novos filtros.

        Esta é uma camada de proteção adicional para quando o modelo GPT não
        incluir campos críticos nas queries SQL geradas, apesar das instruções
        explícitas no prompt.

        Campos críticos (configurados em FILTER_BEHAVIOR_CONFIG):
        - Cod_Cliente: código específico do cliente
        - Municipio_Cliente: cidade específica
        - UF_Cliente: estado
        - Cod_Segmento_Cliente: segmento do cliente

        Args:
            existing_context: Contexto atual com possíveis campos críticos
            new_filters: Novos filtros detectados (podem não conter campos críticos)
            changes: Lista para registrar mudanças de preservação

        Returns:
            Dict com campos críticos que devem ser preservados
        """
        # Carregar lista de campos críticos da configuração centralizada
        critical_fields = self.field_groups.get('critical_preservation_fields', [])
        if not critical_fields:
            # Fallback: usar configuração direta se não estiver em field_groups
            import sys, os
            sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
            from config.agent_config import FILTER_BEHAVIOR_CONFIG
            critical_fields = FILTER_BEHAVIOR_CONFIG.get("critical_preservation_fields", [])

        preserved_context = {}

        for field in critical_fields:
            # Se campo crítico existe no contexto mas NÃO foi mencionado nos novos filtros
            if field in existing_context and field not in new_filters:
                existing_value = existing_context[field]

                # Validar que o valor não é vazio/nulo
                if existing_value is not None and existing_value != [] and existing_value != "":
                    preserved_context[field] = existing_value
                    changes.append(f"PRESERVAÇÃO: {field} = '{existing_value}' (campo crítico mantido automaticamente)")

        return preserved_context

    def handle_explicit_removals(self, existing_context: Dict, fields_to_remove: List[str],
                                 clear_all: bool = False) -> Tuple[Dict, List[str]]:
        """
        Manipula remoções explícitas de filtros solicitadas pelo usuário

        Args:
            existing_context: Contexto atual
            fields_to_remove: Lista de campos a remover
            clear_all: Se True, limpa todos os filtros

        Returns:
            Tuple[Dict, List[str]]: (contexto_atualizado, lista_de_mudanças)
        """
        changes = []

        # Limpeza total
        if clear_all:
            removed_count = len([v for v in existing_context.values()
                               if v is not None and v != [] and v != ""])
            changes.append(f"LIMPEZA TOTAL: {removed_count} filtros removidos pelo usuário")
            return {}, changes

        # Remoção específica
        updated_context = existing_context.copy()

        for field in fields_to_remove:
            if field in updated_context:
                old_value = updated_context[field]
                del updated_context[field]
                changes.append(f"REMOÇÃO EXPLÍCITA: {field} = '{old_value}' (solicitado pelo usuário)")

        if not changes:
            changes.append("INFO: Nenhum filtro correspondente encontrado para remover")

        return updated_context, changes

    def apply_intelligent_merge(self, existing_context: Dict, new_filters: Dict) -> Tuple[Dict, List[str]]:
        """
        Aplica merge inteligente com substituição baseada em regras de negócio

        NOVO: Inclui preservação automática de campos críticos como fallback de segurança
        para casos onde o modelo GPT não inclui esses campos nas queries SQL.

        Args:
            existing_context: Contexto atual
            new_filters: Novos filtros detectados

        Returns:
            Tuple[Dict, List[str]]: (contexto_atualizado, lista_de_mudanças)
        """
        result_context = existing_context.copy()
        changes = []

        # NOVO: Preservar campos críticos ANTES de processar novos filtros
        # Esta é uma camada de proteção adicional para quando o modelo GPT falha
        # em incluir campos críticos nas queries SQL, apesar das instruções do prompt
        critical_preserved = self._preserve_critical_fields(
            existing_context, new_filters, changes
        )

        for field, new_value in new_filters.items():
            if new_value is None or new_value == [] or new_value == "":
                continue

            # Verificar se deve substituir
            should_replace = self.should_replace_filter(field, new_value, result_context)

            if should_replace:
                # Se é substituição explícita de campo crítico, remover da preservação automática
                if field in critical_preserved:
                    del critical_preserved[field]
                    # Remover mensagem de preservação da lista de changes
                    changes = [c for c in changes if not c.startswith(f"PRESERVAÇÃO: {field}")]

                old_value = result_context.get(field)
                result_context[field] = new_value

                if old_value != new_value:
                    changes.append(f"SUBSTITUIÇÃO: {field} '{old_value}' -> '{new_value}'")

                    # Verificar se precisa limpar campos relacionados
                    self._clean_related_fields(field, result_context, changes)
            else:
                # Adicionar normalmente (para campos multi-valor)
                if field in result_context and isinstance(result_context[field], list):
                    # Adicionar à lista existente se não duplicado
                    if isinstance(new_value, list):
                        for item in new_value:
                            if item not in result_context[field]:
                                result_context[field].append(item)
                                changes.append(f"ADIÇÃO: {field} += '{item}'")
                    else:
                        if new_value not in result_context[field]:
                            result_context[field].append(new_value)
                            changes.append(f"ADIÇÃO: {field} += '{new_value}'")
                else:
                    # Definir novo valor
                    result_context[field] = new_value
                    changes.append(f"NOVO: {field} = '{new_value}'")

        # NOVO: Mesclar campos críticos preservados no resultado final
        # Apenas adicionar campos que ainda não foram processados/substituídos
        for field, value in critical_preserved.items():
            if field not in result_context or result_context[field] is None:
                result_context[field] = value

        return result_context, changes

    def _clean_related_fields(self, field: str, context: Dict, changes: List[str]):
        """
        Limpa campos relacionados quando um campo principal é substituído

        Args:
            field: Campo que foi substituído
            context: Contexto a ser limpo
            changes: Lista para registrar mudanças
        """
        if field == 'Municipio_Cliente':
            # Nova cidade pode implicar em limpar estado se conflitante
            # (Mantém estado se compatível, limpa se conflitante)
            pass  # Por enquanto, manter UF_Cliente intacto

        elif field == 'Data':
            # Data específica limpa ranges temporais
            range_fields = ['Data_>=', 'Data_<', 'Data_<=', 'Data_>']
            for rf in range_fields:
                if rf in context:
                    del context[rf]
                    changes.append(f"LIMPEZA: Removido {rf} devido à data específica")

        elif field in ['Data_>=', 'Data_<']:
            # Novo range temporal limpa data específica
            if 'Data' in context:
                del context['Data']
                changes.append(f"LIMPEZA: Removida data específica devido ao range temporal")

    def get_conflict_summary(self, existing_context: Dict, new_filters: Dict) -> str:
        """
        Gera resumo dos conflitos que serão resolvidos

        Args:
            existing_context: Contexto atual
            new_filters: Novos filtros

        Returns:
            String com resumo dos conflitos
        """
        conflicts = []

        for field, new_value in new_filters.items():
            if new_value is None or new_value == "":
                continue

            if self.should_replace_filter(field, new_value, existing_context):
                old_value = existing_context.get(field)
                if old_value and old_value != new_value:
                    conflicts.append(f"{field}: {old_value} -> {new_value}")

        if conflicts:
            return f"Substituições detectadas: {', '.join(conflicts)}"
        else:
            return "Nenhum conflito detectado - apenas adições"

    def validate_context_consistency(self, context: Dict) -> Tuple[bool, List[str]]:
        """
        Valida se o contexto atual é consistente (sem conflitos lógicos)

        Args:
            context: Contexto para validar

        Returns:
            Tuple[bool, List[str]]: (é_válido, lista_de_problemas)
        """
        problems = []

        # Verificar múltiplas cidades
        if 'Municipio_Cliente' in context:
            municipio = context['Municipio_Cliente']
            if isinstance(municipio, list) and len(municipio) > 1:
                problems.append(f"Múltiplas cidades detectadas: {municipio}")

        # Verificar conflitos temporais
        has_specific_date = 'Data' in context and context['Data']
        has_date_range = ('Data_>=' in context and context['Data_>=']) or ('Data_<' in context and context['Data_<'])

        if has_specific_date and has_date_range:
            problems.append("Conflito temporal: data específica + range de datas")

        # Verificar múltiplos clientes específicos
        if 'Cod_Cliente' in context:
            cliente = context['Cod_Cliente']
            if isinstance(cliente, list) and len(cliente) > 1:
                problems.append(f"Múltiplos clientes específicos: {cliente}")

        is_valid = len(problems) == 0
        return is_valid, problems

    def auto_resolve_conflicts(self, context: Dict) -> Tuple[Dict, List[str]]:
        """
        Detecta e resolve automaticamente conflitos lógicos no contexto

        Args:
            context: Contexto com possíveis conflitos

        Returns:
            Tuple[Dict, List[str]]: (contexto_corrigido, lista_de_correções)
        """
        corrected_context = context.copy()
        corrections = []

        # CONFLITO 1: Município com múltiplos valores string (não-lista)
        # Exemplo: Municipio_Cliente aparece múltiplas vezes no SQL
        if 'Municipio_Cliente' in corrected_context:
            municipio = corrected_context['Municipio_Cliente']

            # Se for string única, verificar se não é resultado de merge errado
            if isinstance(municipio, str):
                # Detectar padrões de AND impossíveis que podem ter sido capturados
                if ' AND ' in municipio.upper() or ', ' in municipio:
                    # Pegar apenas o último valor mencionado (mais recente)
                    parts = municipio.replace(' AND ', ',').split(',')
                    latest_city = parts[-1].strip().upper()
                    corrected_context['Municipio_Cliente'] = latest_city
                    corrections.append(f"CORREÇÃO: Múltiplas cidades detectadas → mantida apenas '{latest_city}' (mais recente)")

            # Se for lista com apenas um elemento, converter para string
            elif isinstance(municipio, list) and len(municipio) == 1:
                corrected_context['Municipio_Cliente'] = municipio[0]
                corrections.append(f"CORREÇÃO: Lista com um elemento convertida para string")

        # CONFLITO 2: Cliente específico com múltiplos valores
        if 'Cod_Cliente' in corrected_context:
            cliente = corrected_context['Cod_Cliente']

            # Similar ao município, manter apenas o mais recente se não for lista explícita
            if isinstance(cliente, str) and (' AND ' in cliente.upper() or ', ' in cliente):
                parts = cliente.replace(' AND ', ',').split(',')
                latest_client = parts[-1].strip()
                corrected_context['Cod_Cliente'] = latest_client
                corrections.append(f"CORREÇÃO: Múltiplos clientes detectados → mantido apenas '{latest_client}' (mais recente)")

        # CONFLITO 3: Data específica + range temporal simultaneamente
        has_specific_date = 'Data' in corrected_context and corrected_context['Data']
        has_date_range = ('Data_>=' in corrected_context and corrected_context['Data_>=']) or \
                        ('Data_<' in corrected_context and corrected_context['Data_<'])

        if has_specific_date and has_date_range:
            # Priorizar range temporal (mais comum em análises)
            del corrected_context['Data']
            corrections.append("CORREÇÃO: Conflito temporal → mantido range, removida data específica")

        return corrected_context, corrections


def apply_smart_filter_replacement(existing_context: Dict, new_filters: Dict) -> Tuple[Dict, List[str]]:
    """
    Função de conveniência para aplicar substituição inteligente de filtros

    Args:
        existing_context: Contexto atual de filtros
        new_filters: Novos filtros detectados

    Returns:
        Tuple[Dict, List[str]]: (contexto_atualizado, lista_de_mudanças)
    """
    replacer = SmartFilterReplacer()
    return replacer.apply_intelligent_merge(existing_context, new_filters)


def validate_filter_consistency(context: Dict) -> Tuple[bool, List[str]]:
    """
    Função de conveniência para validar consistência de filtros

    Args:
        context: Contexto para validar

    Returns:
        Tuple[bool, List[str]]: (é_válido, lista_de_problemas)
    """
    replacer = SmartFilterReplacer()
    return replacer.validate_context_consistency(context)


def auto_resolve_filter_conflicts(context: Dict) -> Tuple[Dict, List[str]]:
    """
    Função de conveniência para auto-resolver conflitos lógicos

    Args:
        context: Contexto com possíveis conflitos

    Returns:
        Tuple[Dict, List[str]]: (contexto_corrigido, lista_de_correções)
    """
    replacer = SmartFilterReplacer()
    return replacer.auto_resolve_conflicts(context)


def handle_filter_removals(existing_context: Dict, fields_to_remove: List[str],
                           clear_all: bool = False) -> Tuple[Dict, List[str]]:
    """
    Função de conveniência para manipular remoções explícitas de filtros

    Args:
        existing_context: Contexto atual
        fields_to_remove: Lista de campos a remover
        clear_all: Se True, limpa todos os filtros

    Returns:
        Tuple[Dict, List[str]]: (contexto_atualizado, lista_de_mudanças)
    """
    replacer = SmartFilterReplacer()
    return replacer.handle_explicit_removals(existing_context, fields_to_remove, clear_all)