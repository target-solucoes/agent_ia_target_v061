"""
Query Intent Analyzer for Dimension Assignment in Stacked Bar Charts

This module provides intelligent analysis of user queries to determine
which dimension should be on the X-axis and which should be represented
by colors in stacked bar charts.

Key Features:
- Pattern-based detection using compiled regex (high performance)
- Portuguese language support
- Fallback to first-mentioned dimension principle
- Zero LLM calls (pure Python analysis)
- Overhead < 10ms per query

Author: AI Agent
"""

import re
from typing import Dict, List, Optional, Tuple
from functools import lru_cache


class QueryIntentAnalyzer:
    """
    Analyzes user queries to determine dimension assignment for visualizations.

    This class uses pattern matching and heuristics to identify which dimension
    the user wants to compare (X-axis) vs which dimension shows composition (colors).
    """

    # Compiled regex patterns for performance
    # Pattern: "Top N [DIM1] para/nos [DIM2]" → DIM2 on X-axis, DIM1 in colors
    PATTERN_FOR = re.compile(
        r'(?:top|maiores?|melhores?|principais)\s+\d*\s*(\w+(?:\s+\w+){0,3})\s+'
        r'(?:para|nos?|nas?|dos?|das?|em)\s+(?:os?|as?)?\s*\d*\s*'
        r'(?:maiores?|melhores?|principais|top)?\s*(\w+(?:\s+\w+){0,3})',
        re.IGNORECASE
    )

    # Pattern: "Top N [DIM1] por [DIM2]" → DIM1 on X-axis, DIM2 in colors
    PATTERN_BY = re.compile(
        r'(?:top|maiores?|melhores?|principais)\s+\d*\s*(\w+(?:\s+\w+){0,3})\s+'
        r'(?:por|agrupados?\s+por|divididos?\s+por)\s+(\w+(?:\s+\w+){0,3})',
        re.IGNORECASE
    )

    # Pattern: "[DIM1] nos/para [DIM2]" → DIM2 on X-axis, DIM1 in colors
    PATTERN_IN = re.compile(
        r'(\w+(?:\s+\w+){0,3})\s+(?:nos?|nas?|para|em)\s+(?:os?|as?)?\s*(\w+(?:\s+\w+){0,3})',
        re.IGNORECASE
    )

    def __init__(self):
        """Initialize the QueryIntentAnalyzer."""
        self._dimension_cache: Dict[str, Dict] = {}

    def extract_dimension_order(
        self,
        query: str,
        columns: List[str],
        debug: bool = False
    ) -> Optional[Dict[str, any]]:
        """
        Extract dimension ordering from user query.

        Args:
            query: User's natural language query
            columns: List of available column names in the dataset
            debug: If True, includes debug information in response

        Returns:
            Dictionary with:
                - x_dimension: Column name for X-axis
                - color_dimension: Column name for colors/legend
                - confidence: Float (0.0-1.0) indicating confidence level
                - pattern: String indicating which pattern was matched
                - debug_info: Optional debug information

            Returns None if no clear dimension order can be determined.
        """
        # Check cache first
        cache_key = f"{query}|{','.join(sorted(columns))}"
        if cache_key in self._dimension_cache:
            return self._dimension_cache[cache_key]

        # Normalize query for matching
        query_normalized = self._normalize_query(query)

        # Try each pattern in priority order
        result = None

        # Priority 1: "Top N [DIM1] para [DIM2]" pattern
        result = self._try_pattern_for(query_normalized, columns, debug)
        if result:
            result['pattern'] = 'for_pattern'
            result['confidence'] = 0.95
            self._dimension_cache[cache_key] = result
            return result

        # Priority 2: "Top N [DIM1] por [DIM2]" pattern
        result = self._try_pattern_by(query_normalized, columns, debug)
        if result:
            result['pattern'] = 'by_pattern'
            result['confidence'] = 0.90
            self._dimension_cache[cache_key] = result
            return result

        # Priority 3: "[DIM1] nos/para [DIM2]" pattern
        result = self._try_pattern_in(query_normalized, columns, debug)
        if result:
            result['pattern'] = 'in_pattern'
            result['confidence'] = 0.85
            self._dimension_cache[cache_key] = result
            return result

        # Priority 4: First-mentioned dimension fallback
        result = self._try_first_mentioned(query_normalized, columns, debug)
        if result:
            result['pattern'] = 'first_mentioned'
            result['confidence'] = 0.70
            self._dimension_cache[cache_key] = result
            return result

        # No pattern matched
        return None

    def _normalize_query(self, query: str) -> str:
        """
        Normalize query for pattern matching.

        Args:
            query: Raw user query

        Returns:
            Normalized query string
        """
        # Convert to lowercase
        normalized = query.lower()

        # Remove extra whitespace
        normalized = ' '.join(normalized.split())

        # Remove special characters but keep spaces
        normalized = re.sub(r'[^\w\s]', ' ', normalized)

        return normalized

    def _try_pattern_for(
        self,
        query: str,
        columns: List[str],
        debug: bool
    ) -> Optional[Dict]:
        """
        Try to match "Top N [DIM1] para [DIM2]" pattern.

        This pattern indicates: DIM2 on X-axis, DIM1 in colors
        Example: "Top 3 produtos para 5 estados" → states on X, products in colors
        """
        match = self.PATTERN_FOR.search(query)
        if not match:
            return None

        dim1_text = match.group(1).strip()
        dim2_text = match.group(2).strip()

        # Map text to actual column names
        dim1_col = self._find_matching_column(dim1_text, columns)
        dim2_col = self._find_matching_column(dim2_text, columns)

        if dim1_col and dim2_col and dim1_col != dim2_col:
            result = {
                'x_dimension': dim2_col,        # DIM2 goes to X-axis
                'color_dimension': dim1_col,    # DIM1 goes to colors
            }

            if debug:
                result['debug_info'] = {
                    'matched_text': match.group(0),
                    'dim1_text': dim1_text,
                    'dim2_text': dim2_text,
                    'dim1_col': dim1_col,
                    'dim2_col': dim2_col
                }

            return result

        return None

    def _try_pattern_by(
        self,
        query: str,
        columns: List[str],
        debug: bool
    ) -> Optional[Dict]:
        """
        Try to match "Top N [DIM1] por [DIM2]" pattern.

        This pattern indicates: DIM1 on X-axis, DIM2 in colors
        Example: "Top 5 estados por produto" → states on X, products in colors
        """
        match = self.PATTERN_BY.search(query)
        if not match:
            return None

        dim1_text = match.group(1).strip()
        dim2_text = match.group(2).strip()

        # Map text to actual column names
        dim1_col = self._find_matching_column(dim1_text, columns)
        dim2_col = self._find_matching_column(dim2_text, columns)

        if dim1_col and dim2_col and dim1_col != dim2_col:
            result = {
                'x_dimension': dim1_col,        # DIM1 goes to X-axis
                'color_dimension': dim2_col,    # DIM2 goes to colors
            }

            if debug:
                result['debug_info'] = {
                    'matched_text': match.group(0),
                    'dim1_text': dim1_text,
                    'dim2_text': dim2_text,
                    'dim1_col': dim1_col,
                    'dim2_col': dim2_col
                }

            return result

        return None

    def _try_pattern_in(
        self,
        query: str,
        columns: List[str],
        debug: bool
    ) -> Optional[Dict]:
        """
        Try to match "[DIM1] nos/para [DIM2]" pattern.

        This pattern indicates: DIM2 on X-axis, DIM1 in colors
        Example: "produtos nos estados" → states on X, products in colors
        """
        match = self.PATTERN_IN.search(query)
        if not match:
            return None

        dim1_text = match.group(1).strip()
        dim2_text = match.group(2).strip()

        # Map text to actual column names
        dim1_col = self._find_matching_column(dim1_text, columns)
        dim2_col = self._find_matching_column(dim2_text, columns)

        if dim1_col and dim2_col and dim1_col != dim2_col:
            result = {
                'x_dimension': dim2_col,        # DIM2 goes to X-axis
                'color_dimension': dim1_col,    # DIM1 goes to colors
            }

            if debug:
                result['debug_info'] = {
                    'matched_text': match.group(0),
                    'dim1_text': dim1_text,
                    'dim2_text': dim2_text,
                    'dim1_col': dim1_col,
                    'dim2_col': dim2_col
                }

            return result

        return None

    def _try_first_mentioned(
        self,
        query: str,
        columns: List[str],
        debug: bool
    ) -> Optional[Dict]:
        """
        Fallback: Use first-mentioned dimension principle.

        Identifies all column mentions and assigns:
        - First mentioned dimension → color dimension (composition)
        - Second mentioned dimension → X-axis (comparison base)
        """
        mentions = []

        for col in columns:
            # Find position of column mention in query
            col_normalized = self._normalize_query(col)
            col_patterns = self._get_column_patterns(col_normalized)

            for pattern in col_patterns:
                match = re.search(pattern, query)
                if match:
                    mentions.append((match.start(), col))
                    break

        # Sort by position in query
        mentions.sort(key=lambda x: x[0])

        # Need at least 2 different dimensions
        unique_dims = []
        for _, col in mentions:
            if col not in unique_dims:
                unique_dims.append(col)

        if len(unique_dims) >= 2:
            result = {
                'x_dimension': unique_dims[1],      # Second mentioned → X-axis
                'color_dimension': unique_dims[0],  # First mentioned → colors
            }

            if debug:
                result['debug_info'] = {
                    'all_mentions': mentions,
                    'unique_dims': unique_dims,
                    'reasoning': 'first_mentioned_fallback'
                }

            return result

        return None

    def _find_matching_column(self, text: str, columns: List[str]) -> Optional[str]:
        """
        Find the column name that best matches the given text.

        Args:
            text: Text extracted from query
            columns: List of available column names

        Returns:
            Matching column name or None
        """
        text_normalized = text.lower().strip()

        # First try: exact match
        for col in columns:
            if col.lower() == text_normalized:
                return col

        # Second try: substring match
        for col in columns:
            col_lower = col.lower()
            if text_normalized in col_lower or col_lower in text_normalized:
                return col

        # Third try: common aliases and variations
        alias_map = {
            'produto': ['produto', 'produtos', 'linha', 'linhas', 'item', 'itens'],
            'estado': ['estado', 'estados', 'uf', 'ufs'],
            'cliente': ['cliente', 'clientes', 'consumidor', 'consumidores'],
            'representante': ['representante', 'representantes', 'vendedor', 'vendedores'],
            'mes': ['mes', 'meses', 'periodo', 'periodos'],
            'ano': ['ano', 'anos'],
        }

        for col in columns:
            col_base = col.lower().replace('_', ' ').strip()
            for alias_key, aliases in alias_map.items():
                if alias_key in col_base:
                    if any(alias in text_normalized for alias in aliases):
                        return col

        return None

    def _get_column_patterns(self, column: str) -> List[str]:
        """
        Generate regex patterns for finding a column mention in text.

        Args:
            column: Normalized column name

        Returns:
            List of regex patterns to match
        """
        patterns = []

        # Exact match with word boundaries
        patterns.append(r'\b' + re.escape(column) + r'\b')

        # Plural/singular variations
        if column.endswith('s'):
            singular = column[:-1]
            patterns.append(r'\b' + re.escape(singular) + r'\b')
        else:
            plural = column + 's'
            patterns.append(r'\b' + re.escape(plural) + r'\b')

        return patterns

    def clear_cache(self):
        """Clear the dimension cache."""
        self._dimension_cache.clear()


# Singleton instance for performance
_analyzer_instance = None


def get_analyzer() -> QueryIntentAnalyzer:
    """
    Get the singleton QueryIntentAnalyzer instance.

    Returns:
        QueryIntentAnalyzer instance
    """
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = QueryIntentAnalyzer()
    return _analyzer_instance
