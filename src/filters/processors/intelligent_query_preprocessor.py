"""
Pré-processador Inteligente de Queries - DESABILITADO

⚠️ AVISO: Este módulo está DESABILITADO no app.py (linhas 761-780)

MOTIVO DA DESABILITAÇÃO:
- Os padrões regex (especialmente linha 30) capturam frases inteiras como cidades
- Exemplo de bug: "qual o total de vendas por produto em junho/2016"
  → Capturava: Municipio_Cliente = "VENDAS POR PRODUTO EM JUNHO"
- O regex `r'\b(vendas (?:de|em))\s+([A-ZÀ-Ü][a-zà-ü]+(?:\s+[A-ZÀ-Ü][a-zà-ü]+)*)'`
  captura múltiplas palavras sem limite, causando falsos positivos

SOLUÇÃO IMPLEMENTADA:
- Extração de filtros via SQL (sql_filter_extractor.py) que é mais precisa
- Analisa cláusulas WHERE das queries executadas pelo agente
- Não depende de regex na pergunta do usuário

Este código foi mantido para referência futura caso seja necessário
implementar pré-processamento com validação mais rigorosa.
"""

import re
from typing import Dict, List, Tuple, Optional
import pandas as pd


class IntelligentQueryPreprocessor:
    """
    Pré-processador que analisa a pergunta do usuário para detectar
    intenções de substituição de filtros antes da execução do agente.
    """

    def __init__(self, df_dataset: Optional[pd.DataFrame] = None):
        """
        Inicializa o pré-processador

        Args:
            df_dataset: Dataset para validação de valores
        """
        self.df_dataset = df_dataset

        # Padrões para detectar menções geográficas
        self.geographic_patterns = {
            'municipio': [
                r'\b(em|de|para|client[es]* (?:de|em)|vendas (?:de|em)|top.*(?:de|em))\s+([A-ZÀ-Ü][a-zà-ü]+(?:\s+[A-ZÀ-Ü][a-zà-ü]+)*)',
                r'\b([A-ZÀ-Ü][a-zà-ü]+(?:\s+[A-ZÀ-Ü][a-zà-ü]+)*)\b(?=\s*\?|$|,)',  # Final da pergunta
                r'\bcidade[s]* (?:de|em) ([A-ZÀ-Ü][a-zà-ü]+(?:\s+[A-ZÀ-Ü][a-zà-ü]+)*)',
                r'\bmunicipio[s]* (?:de|em) ([A-ZÀ-Ü][a-zà-ü]+(?:\s+[A-ZÀ-Ü][a-zà-ü]+)*)'
            ]
        }

        # Padrões temporais
        self.temporal_patterns = {
            'ano': r'\b(\d{4})\b',
            'mes_ano': r'\b(\w+) de (\d{4})\b',
            'periodo': r'\b(ultimo[s]* \d+ (?:mes|meses|ano[s]*)|periodo|trimestre)',
        }

        # Lista de cidades conhecidas (pode ser expandida)
        self.known_cities = self._get_known_cities() if df_dataset is not None else []

    def _get_known_cities(self) -> List[str]:
        """Extrai cidades conhecidas do dataset"""
        if 'Municipio_Cliente' in self.df_dataset.columns:
            cities = self.df_dataset['Municipio_Cliente'].dropna().unique().tolist()
            return [city.strip().upper() for city in cities if isinstance(city, str)]
        return []

    def preprocess_query(self, user_query: str, current_context: Dict) -> Tuple[Dict, List[str]]:
        """
        Pré-processa a query do usuário para detectar intenções de substituição

        Args:
            user_query: Pergunta do usuário
            current_context: Contexto atual de filtros

        Returns:
            Tuple[Dict, List[str]]: (contexto_atualizado, lista_de_mudanças)
        """
        changes = []
        updated_context = current_context.copy()

        # Detectar novas menções geográficas
        detected_cities = self._detect_geographic_mentions(user_query)

        if detected_cities:
            # Se há cidade no contexto atual e nova cidade detectada
            current_city = current_context.get('Municipio_Cliente')
            new_city = detected_cities[0].upper()  # Usar primeira cidade detectada

            if current_city and current_city != new_city:
                # SUBSTITUIÇÃO INTELIGENTE: nova cidade substitui anterior
                updated_context['Municipio_Cliente'] = new_city
                changes.append(f"PRÉ-PROCESSAMENTO: Substituindo cidade '{current_city}' -> '{new_city}'")

                # Log da detecção
                changes.append(f"DETECÇÃO: Nova cidade '{new_city}' identificada na pergunta")

            elif not current_city:
                # ADIÇÃO: primeira cidade mencionada
                updated_context['Municipio_Cliente'] = new_city
                changes.append(f"PRÉ-PROCESSAMENTO: Adicionando cidade '{new_city}'")

        # Detectar menções temporais (ano, período, etc.)
        detected_temporal = self._detect_temporal_mentions(user_query)
        if detected_temporal:
            for temporal_field, temporal_value in detected_temporal.items():
                updated_context[temporal_field] = temporal_value
                changes.append(f"PRÉ-PROCESSAMENTO: Detectado {temporal_field} = '{temporal_value}'")

        return updated_context, changes

    def _detect_geographic_mentions(self, query: str) -> List[str]:
        """
        Detecta menções geográficas na query

        Args:
            query: Query do usuário

        Returns:
            Lista de cidades detectadas
        """
        detected_cities = []
        query_upper = query.upper()

        # Primeiro, verificar cidades conhecidas do dataset
        for city in self.known_cities:
            if city in query_upper:
                # Verificar se é uma menção real (não parte de outra palavra)
                city_pattern = r'\b' + re.escape(city) + r'\b'
                if re.search(city_pattern, query_upper):
                    detected_cities.append(city)

        # Se não encontrou cidades conhecidas, usar padrões regex
        if not detected_cities:
            for pattern in self.geographic_patterns['municipio']:
                matches = re.finditer(pattern, query, re.IGNORECASE)
                for match in matches:
                    # Pegar o grupo que contém a cidade (última captura)
                    groups = match.groups()
                    potential_city = groups[-1] if groups else None

                    if potential_city and len(potential_city.strip()) > 2:
                        # Validar se parece com nome de cidade
                        city_candidate = potential_city.strip().upper()
                        if self._is_likely_city_name(city_candidate):
                            detected_cities.append(city_candidate)

        return list(set(detected_cities))  # Remover duplicatas

    def _detect_temporal_mentions(self, query: str) -> Dict[str, str]:
        """
        Detecta menções temporais na query

        Args:
            query: Query do usuário

        Returns:
            Dict com campos temporais detectados
        """
        temporal_fields = {}

        # Detectar anos (YYYY)
        year_matches = re.findall(self.temporal_patterns['ano'], query)
        if year_matches:
            temporal_fields['ano'] = year_matches[0]

        # Detectar mês e ano (ex: "julho de 2015")
        month_year_matches = re.findall(self.temporal_patterns['mes_ano'], query, re.IGNORECASE)
        if month_year_matches:
            month_name, year = month_year_matches[0]
            # Converter nome do mês para número se necessário
            month_number = self._convert_month_name_to_number(month_name)
            if month_number:
                temporal_fields['mes'] = f"{month_number:02d}"
                temporal_fields['ano'] = year

        return temporal_fields

    def _is_likely_city_name(self, candidate: str) -> bool:
        """
        Verifica se o candidato parece com nome de cidade

        Args:
            candidate: Candidato a nome de cidade

        Returns:
            True se parece com nome de cidade
        """
        # Regras básicas para validar nomes de cidade
        if len(candidate) < 3:
            return False

        # Deve começar com letra maiúscula (já está em uppercase)
        if not candidate[0].isalpha():
            return False

        # Não deve conter números
        if any(char.isdigit() for char in candidate):
            return False

        # Palavras que provavelmente não são cidades
        non_city_words = {
            'CLIENTE', 'CLIENTES', 'VENDAS', 'PRODUTO', 'PRODUTOS',
            'VENDEDOR', 'REPRESENTANTE', 'TOTAL', 'VALOR', 'QUANTIDADE',
            'PERIODO', 'MES', 'ANO', 'DIA', 'SEMANA', 'TRIMESTRE'
        }

        if candidate in non_city_words:
            return False

        return True

    def _convert_month_name_to_number(self, month_name: str) -> Optional[int]:
        """
        Converte nome do mês para número

        Args:
            month_name: Nome do mês em português

        Returns:
            Número do mês (1-12) ou None
        """
        month_mapping = {
            'janeiro': 1, 'jan': 1,
            'fevereiro': 2, 'fev': 2,
            'março': 3, 'mar': 3,
            'abril': 4, 'abr': 4,
            'maio': 5, 'mai': 5,
            'junho': 6, 'jun': 6,
            'julho': 7, 'jul': 7,
            'agosto': 8, 'ago': 8,
            'setembro': 9, 'set': 9,
            'outubro': 10, 'out': 10,
            'novembro': 11, 'nov': 11,
            'dezembro': 12, 'dez': 12
        }

        return month_mapping.get(month_name.lower())

    def get_preprocessing_summary(self, original_context: Dict, updated_context: Dict, changes: List[str]) -> str:
        """
        Gera resumo do pré-processamento realizado

        Args:
            original_context: Contexto original
            updated_context: Contexto atualizado
            changes: Lista de mudanças

        Returns:
            String com resumo das mudanças
        """
        if not changes:
            return "Nenhuma substituição necessária"

        summary_parts = []

        # Analisar mudanças em cidades
        city_changes = [c for c in changes if 'cidade' in c.lower()]
        if city_changes:
            summary_parts.append(f"Cidade: {len(city_changes)} mudança(s)")

        # Analisar mudanças temporais
        temporal_changes = [c for c in changes if any(term in c.lower() for term in ['ano', 'mes', 'periodo'])]
        if temporal_changes:
            summary_parts.append(f"Temporal: {len(temporal_changes)} mudança(s)")

        if summary_parts:
            return f"Pré-processamento: {', '.join(summary_parts)}"
        else:
            return f"Pré-processamento: {len(changes)} operação(ões)"


def preprocess_user_query(user_query: str, current_context: Dict, df_dataset: Optional[pd.DataFrame] = None) -> Tuple[Dict, List[str]]:
    """
    Função de conveniência para pré-processar query do usuário

    Args:
        user_query: Pergunta do usuário
        current_context: Contexto atual
        df_dataset: Dataset opcional

    Returns:
        Tuple[Dict, List[str]]: (contexto_atualizado, mudanças)
    """
    preprocessor = IntelligentQueryPreprocessor(df_dataset)
    return preprocessor.preprocess_query(user_query, current_context)