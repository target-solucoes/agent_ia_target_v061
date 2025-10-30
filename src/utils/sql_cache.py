"""
SQL Cache - Cache de Resultados SQL para FASE 3
Evita executar queries idênticas múltiplas vezes
"""

import hashlib
import time
from typing import Optional, Any, Dict
import pandas as pd


class SQLResultCache:
    """
    Cache para resultados de queries SQL.
    Armazena DataFrames resultantes de queries para evitar re-execução.
    """
    
    def __init__(self, max_size: int = 50, ttl_seconds: int = 1800):
        """
        Inicializa cache de resultados SQL.
        
        Args:
            max_size: Número máximo de queries em cache
            ttl_seconds: Tempo de vida em segundos (1800 = 30 minutos)
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.hits = 0
        self.misses = 0
    
    def _generate_query_hash(self, query: str, params: Optional[Dict] = None) -> str:
        """
        Gera hash único para uma query SQL.
        
        Args:
            query: Query SQL (string)
            params: Parâmetros adicionais (opcional)
        
        Returns:
            Hash da query
        """
        # Normalizar query (remover espaços extras, lowercase para palavras-chave)
        normalized_query = " ".join(query.split())
        
        # Incluir parâmetros se houver
        if params:
            import json
            normalized_query += json.dumps(params, sort_keys=True)
        
        return hashlib.md5(normalized_query.encode()).hexdigest()
    
    def get(self, query: str, params: Optional[Dict] = None) -> Optional[pd.DataFrame]:
        """
        Recupera resultado da query do cache se existir.
        
        Args:
            query: Query SQL
            params: Parâmetros opcionais
        
        Returns:
            DataFrame cacheado ou None se não encontrado/expirado
        """
        query_hash = self._generate_query_hash(query, params)
        
        if query_hash not in self.cache:
            self.misses += 1
            return None
        
        entry = self.cache[query_hash]
        timestamp = entry.get('timestamp', 0)
        
        # Verificar se expirou
        if time.time() - timestamp > self.ttl_seconds:
            del self.cache[query_hash]
            self.misses += 1
            return None
        
        self.hits += 1
        
        # Retornar cópia do DataFrame para evitar modificações
        result_df = entry.get('result')
        return result_df.copy() if result_df is not None else None
    
    def set(self, query: str, result: pd.DataFrame, params: Optional[Dict] = None):
        """
        Armazena resultado de query no cache.
        
        Args:
            query: Query SQL
            result: DataFrame resultado
            params: Parâmetros opcionais
        """
        query_hash = self._generate_query_hash(query, params)
        
        # Limpar cache se atingiu tamanho máximo (LRU simples)
        if len(self.cache) >= self.max_size:
            # Remover entrada mais antiga
            oldest_key = min(self.cache.keys(), 
                           key=lambda k: self.cache[k].get('timestamp', 0))
            del self.cache[oldest_key]
        
        self.cache[query_hash] = {
            'result': result.copy(),  # Armazenar cópia
            'timestamp': time.time(),
            'query_preview': query[:100]  # Para debug
        }
    
    def invalidate(self, query: Optional[str] = None, params: Optional[Dict] = None):
        """
        Invalida cache de uma query específica ou todo o cache.
        
        Args:
            query: Query específica (None = invalidar tudo)
            params: Parâmetros opcionais
        """
        if query is None:
            self.cache.clear()
        else:
            query_hash = self._generate_query_hash(query, params)
            if query_hash in self.cache:
                del self.cache[query_hash]
    
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
            'total_requests': total_requests,
            'ttl_seconds': self.ttl_seconds
        }
    
    def get_cached_queries(self) -> list:
        """Retorna lista de queries atualmente em cache"""
        return [
            {
                'hash': k,
                'query_preview': v.get('query_preview', ''),
                'age_seconds': int(time.time() - v.get('timestamp', 0))
            }
            for k, v in self.cache.items()
        ]


# Cache global para queries SQL
_sql_cache = SQLResultCache(max_size=50, ttl_seconds=1800)


def get_cached_query(query: str, params: Optional[Dict] = None) -> Optional[pd.DataFrame]:
    """
    Wrapper para acessar cache SQL global.
    
    Args:
        query: Query SQL
        params: Parâmetros opcionais
    
    Returns:
        DataFrame cacheado ou None
    """
    return _sql_cache.get(query, params)


def cache_query_result(query: str, result: pd.DataFrame, params: Optional[Dict] = None):
    """
    Wrapper para armazenar resultado no cache SQL global.
    
    Args:
        query: Query SQL
        result: DataFrame resultado
        params: Parâmetros opcionais
    """
    _sql_cache.set(query, result, params)


def get_sql_cache_stats() -> Dict[str, Any]:
    """Retorna estatísticas do cache SQL global"""
    return _sql_cache.get_stats()


def clear_sql_cache():
    """Limpa cache SQL global"""
    _sql_cache.clear()


def invalidate_sql_cache(query: Optional[str] = None):
    """
    Invalida cache SQL.
    
    Args:
        query: Query específica (None = invalidar tudo)
    """
    _sql_cache.invalidate(query)


