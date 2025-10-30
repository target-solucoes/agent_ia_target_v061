"""
DataFrame Optimizer - Otimizações para operações com pandas DataFrame
FASE 3: Reduz cópias desnecessárias e melhora performance
"""

import pandas as pd
import numpy as np
from typing import List, Optional, Union


class DataFrameOptimizer:
    """
    Utilitários para otimizar operações com DataFrames.
    Foco em reduzir cópias e melhorar performance sem comprometer resultados.
    """
    
    @staticmethod
    def optimize_dtypes(df: pd.DataFrame, inplace: bool = False) -> pd.DataFrame:
        """
        Otimiza tipos de dados do DataFrame para reduzir uso de memória.
        
        Converte:
        - int64 → int32 (se valores cabem)
        - float64 → float32 (se precisão permite)
        - object → category (se cardinalidade baixa)
        
        Args:
            df: DataFrame para otimizar
            inplace: Se True, modifica o DataFrame original
        
        Returns:
            DataFrame otimizado
        """
        if not inplace:
            df = df.copy()
        
        for col in df.columns:
            col_type = df[col].dtype
            
            # Otimizar integers
            if col_type == 'int64':
                col_min = df[col].min()
                col_max = df[col].max()
                
                if col_min >= np.iinfo(np.int32).min and col_max <= np.iinfo(np.int32).max:
                    df[col] = df[col].astype('int32')
            
            # Otimizar floats (cuidado com precisão)
            elif col_type == 'float64':
                df[col] = df[col].astype('float32')
            
            # Otimizar strings (category se baixa cardinalidade)
            elif col_type == 'object':
                num_unique = df[col].nunique()
                num_total = len(df[col])
                
                # Se menos de 50% são valores únicos, usar category
                if num_unique / num_total < 0.5:
                    df[col] = df[col].astype('category')
        
        return df
    
    @staticmethod
    def efficient_sort(df: pd.DataFrame, by: Union[str, List[str]], 
                      ascending: bool = True, limit: Optional[int] = None) -> pd.DataFrame:
        """
        Ordenação eficiente com opção de limitar resultados.
        
        Se limit é especificado, usa nlargest/nsmallest que é mais eficiente
        que sort + head.
        
        Args:
            df: DataFrame para ordenar
            by: Coluna(s) para ordenar
            ascending: Ordem ascendente ou descendente
            limit: Número de linhas a retornar (None = todas)
        
        Returns:
            DataFrame ordenado
        """
        if limit is None:
            return df.sort_values(by=by, ascending=ascending).reset_index(drop=True)
        
        # Para top N, nlargest/nsmallest é mais eficiente
        if isinstance(by, str):
            if ascending:
                return df.nsmallest(limit, by).reset_index(drop=True)
            else:
                return df.nlargest(limit, by).reset_index(drop=True)
        else:
            # Múltiplas colunas - usar sort tradicional
            return df.sort_values(by=by, ascending=ascending).head(limit).reset_index(drop=True)
    
    @staticmethod
    def efficient_group_aggregate(df: pd.DataFrame, group_by: Union[str, List[str]], 
                                 agg_dict: dict, limit_per_group: Optional[int] = None) -> pd.DataFrame:
        """
        Agregação eficiente com suporte a limitar resultados por grupo.
        
        Args:
            df: DataFrame para agregar
            group_by: Coluna(s) para agrupar
            agg_dict: Dicionário de agregações {coluna: função}
            limit_per_group: Limitar N primeiros de cada grupo
        
        Returns:
            DataFrame agregado
        """
        grouped = df.groupby(group_by)
        
        if limit_per_group:
            # Limitar antes de agregar (mais eficiente)
            df_limited = grouped.head(limit_per_group)
            return df_limited.groupby(group_by).agg(agg_dict).reset_index()
        else:
            return grouped.agg(agg_dict).reset_index()
    
    @staticmethod
    def memory_usage_report(df: pd.DataFrame, detailed: bool = False) -> dict:
        """
        Gera relatório de uso de memória do DataFrame.
        
        Args:
            df: DataFrame para analisar
            detailed: Se True, retorna uso por coluna
        
        Returns:
            Dicionário com informações de memória
        """
        total_bytes = df.memory_usage(deep=True).sum()
        total_mb = total_bytes / (1024 * 1024)
        
        report = {
            'total_bytes': total_bytes,
            'total_mb': round(total_mb, 2),
            'num_rows': len(df),
            'num_cols': len(df.columns),
            'memory_per_row_bytes': total_bytes / len(df) if len(df) > 0 else 0
        }
        
        if detailed:
            col_usage = df.memory_usage(deep=True)
            report['columns'] = {
                col: {
                    'bytes': int(col_usage[col]),
                    'mb': round(col_usage[col] / (1024 * 1024), 2),
                    'percent': round((col_usage[col] / total_bytes) * 100, 2)
                }
                for col in df.columns
            }
        
        return report
    
    @staticmethod
    def efficient_filter(df: pd.DataFrame, conditions: List[tuple]) -> pd.DataFrame:
        """
        Aplica múltiplos filtros de forma eficiente.
        
        Args:
            df: DataFrame para filtrar
            conditions: Lista de tuplas (coluna, operador, valor)
                Operadores: '==', '!=', '>', '<', '>=', '<=', 'in', 'not in'
        
        Returns:
            DataFrame filtrado
        
        Example:
            conditions = [
                ('idade', '>', 18),
                ('cidade', 'in', ['SP', 'RJ']),
                ('ativo', '==', True)
            ]
        """
        mask = pd.Series([True] * len(df), index=df.index)
        
        for col, op, val in conditions:
            if op == '==':
                mask &= (df[col] == val)
            elif op == '!=':
                mask &= (df[col] != val)
            elif op == '>':
                mask &= (df[col] > val)
            elif op == '<':
                mask &= (df[col] < val)
            elif op == '>=':
                mask &= (df[col] >= val)
            elif op == '<=':
                mask &= (df[col] <= val)
            elif op == 'in':
                mask &= df[col].isin(val)
            elif op == 'not in':
                mask &= ~df[col].isin(val)
        
        return df[mask]
    
    @staticmethod
    def efficient_top_n(df: pd.DataFrame, value_col: str, n: int = 10,
                       ascending: bool = False) -> pd.DataFrame:
        """
        Retorna top N linhas de forma eficiente usando nlargest/nsmallest.
        
        Args:
            df: DataFrame
            value_col: Coluna para ordenar
            n: Número de linhas
            ascending: Se True, usa nsmallest; se False, usa nlargest
        
        Returns:
            DataFrame com top N linhas
        """
        if ascending:
            return df.nsmallest(n, value_col)
        else:
            return df.nlargest(n, value_col)


# Funções helper para uso direto
def optimize_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica otimizações padrão ao DataFrame.
    
    Args:
        df: DataFrame para otimizar
    
    Returns:
        DataFrame otimizado
    """
    optimizer = DataFrameOptimizer()
    return optimizer.optimize_dtypes(df, inplace=False)


def efficient_top_n(df: pd.DataFrame, col: str, n: int, ascending: bool = False) -> pd.DataFrame:
    """
    Helper para obter top N linhas eficientemente.
    
    Args:
        df: DataFrame
        col: Coluna para ordenar
        n: Número de linhas
        ascending: Ordem
    
    Returns:
        Top N linhas
    """
    return DataFrameOptimizer.efficient_top_n(df, col, n, ascending)


