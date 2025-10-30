"""
Performance Cache - Sistema de Caching para FASE 3
Implementa caching inteligente de métricas e resultados sem comprometer qualidade
"""

from functools import wraps, lru_cache
import hashlib
import json
import pandas as pd
from typing import Any, Callable, Dict, Optional
import time


class DataFrameHasher:
    """Utilitário para criar hash de DataFrames de forma eficiente"""
    
    @staticmethod
    def hash_dataframe(df: pd.DataFrame, columns: Optional[list] = None) -> str:
        """
        Cria hash único de um DataFrame baseado em conteúdo e estrutura.
        
        Args:
            df: DataFrame para hashear
            columns: Colunas específicas para incluir no hash (None = todas)
        
        Returns:
            String hash hexadecimal
        """
        if df is None or df.empty:
            return "empty_df"
        
        # Selecionar colunas relevantes
        if columns:
            df_subset = df[columns]
        else:
            df_subset = df
        
        # Criar representação determinística
        # Usar apenas shape e primeiras/últimas linhas para performance
        hash_components = [
            str(df_subset.shape),
            str(df_subset.columns.tolist()),
            str(df_subset.dtypes.tolist())
        ]
        
        # Adicionar amostras do conteúdo (primeira e última linha)
        if len(df_subset) > 0:
            hash_components.append(df_subset.iloc[0].to_json())
            if len(df_subset) > 1:
                hash_components.append(df_subset.iloc[-1].to_json())
        
        # Gerar hash
        combined = "|".join(hash_components)
        return hashlib.md5(combined.encode()).hexdigest()
    
    @staticmethod
    def hash_params(**kwargs) -> str:
        """
        Cria hash de parâmetros para usar como chave de cache.
        
        Args:
            **kwargs: Parâmetros para hashear
        
        Returns:
            String hash hexadecimal
        """
        # Serializar parâmetros de forma determinística
        serialized = json.dumps(kwargs, sort_keys=True, default=str)
        return hashlib.md5(serialized.encode()).hexdigest()


class MetricsCache:
    """
    Cache inteligente para métricas calculadas.
    Evita recalcular métricas para os mesmos dados.
    """
    
    def __init__(self, max_size: int = 128, ttl_seconds: int = 3600):
        """
        Inicializa cache de métricas.
        
        Args:
            max_size: Número máximo de entradas no cache
            ttl_seconds: Tempo de vida das entradas em segundos (3600 = 1 hora)
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """
        Recupera valor do cache se existir e não expirou.
        
        Args:
            key: Chave do cache
        
        Returns:
            Valor cacheado ou None se não encontrado/expirado
        """
        if key not in self.cache:
            self.misses += 1
            return None
        
        entry = self.cache[key]
        timestamp = entry.get('timestamp', 0)
        
        # Verificar se expirou
        if time.time() - timestamp > self.ttl_seconds:
            del self.cache[key]
            self.misses += 1
            return None
        
        self.hits += 1
        return entry.get('value')
    
    def set(self, key: str, value: Any):
        """
        Armazena valor no cache.
        
        Args:
            key: Chave do cache
            value: Valor a armazenar
        """
        # Limpar cache se atingiu tamanho máximo (LRU simples)
        if len(self.cache) >= self.max_size:
            # Remover entrada mais antiga
            oldest_key = min(self.cache.keys(), 
                           key=lambda k: self.cache[k].get('timestamp', 0))
            del self.cache[oldest_key]
        
        self.cache[key] = {
            'value': value,
            'timestamp': time.time()
        }
    
    def clear(self):
        """Limpa todo o cache"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache"""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': round(hit_rate, 2),
            'total_requests': total_requests
        }


# Cache global para métricas numéricas
_metrics_cache = MetricsCache(max_size=128, ttl_seconds=3600)


def cached_metrics(func: Callable) -> Callable:
    """
    Decorator para cachear cálculos de métricas.
    
    Cacheia baseado no hash do DataFrame e parâmetros.
    Ideal para gerar_resumo_numerico e funções de cálculo.
    
    Example:
        @cached_metrics
        def calcular_metricas_ranking(df, label_col, value_col, total_universo):
            # Cálculos pesados aqui
            return metricas
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Identificar DataFrame (primeiro arg geralmente)
        df = args[0] if args else None
        
        if df is None or not isinstance(df, pd.DataFrame):
            # Sem DataFrame, executar sem cache
            return func(*args, **kwargs)
        
        # Criar chave de cache
        df_hash = DataFrameHasher.hash_dataframe(df)
        params_hash = DataFrameHasher.hash_params(
            func_name=func.__name__,
            args=str(args[1:]),  # Excluir DataFrame do hash de args
            kwargs=str(kwargs)
        )
        cache_key = f"{df_hash}:{params_hash}"
        
        # Tentar recuperar do cache
        cached_result = _metrics_cache.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        # Cache miss - calcular
        result = func(*args, **kwargs)
        
        # Armazenar no cache
        _metrics_cache.set(cache_key, result)
        
        return result
    
    return wrapper


def get_cache_stats() -> Dict[str, Any]:
    """Retorna estatísticas do cache global de métricas"""
    return _metrics_cache.get_stats()


def clear_cache():
    """Limpa cache global de métricas"""
    _metrics_cache.clear()


# Decorator adicional para funções simples (sem DataFrame)
@lru_cache(maxsize=256)
def cached_simple(func: Callable) -> Callable:
    """
    Decorator LRU cache para funções simples sem DataFrame.
    
    Use para funções de formatação, parsing, etc.
    """
    return func


