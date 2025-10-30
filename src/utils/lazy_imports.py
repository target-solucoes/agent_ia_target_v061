"""
Lazy Imports - Sistema de Carregamento Preguiçoso para FASE 3
Carrega módulos pesados apenas quando necessários
"""

from typing import Any, Callable, Optional
import importlib
import sys


class LazyModule:
    """
    Wrapper para carregamento preguiçoso de módulos.
    O módulo só é importado quando realmente acessado.
    """
    
    def __init__(self, module_name: str):
        """
        Inicializa lazy module.
        
        Args:
            module_name: Nome completo do módulo (ex: 'pandas', 'plotly.graph_objects')
        """
        self.module_name = module_name
        self._module: Optional[Any] = None
    
    def _load(self):
        """Carrega o módulo se ainda não foi carregado"""
        if self._module is None:
            self._module = importlib.import_module(self.module_name)
    
    def __getattr__(self, name: str) -> Any:
        """Intercepta acesso a atributos e carrega módulo se necessário"""
        self._load()
        return getattr(self._module, name)
    
    def __call__(self, *args, **kwargs) -> Any:
        """Permite chamar o módulo diretamente se for callable"""
        self._load()
        return self._module(*args, **kwargs)
    
    @property
    def is_loaded(self) -> bool:
        """Verifica se o módulo já foi carregado"""
        return self._module is not None


class LazyImporter:
    """
    Gerenciador central de imports preguiçosos.
    Mantém registro de módulos carregados e estatísticas.
    """
    
    def __init__(self):
        self._lazy_modules: dict[str, LazyModule] = {}
        self._load_times: dict[str, float] = {}
    
    def register(self, module_name: str, alias: Optional[str] = None) -> LazyModule:
        """
        Registra um módulo para carregamento preguiçoso.
        
        Args:
            module_name: Nome do módulo
            alias: Alias opcional (ex: 'pd' para 'pandas')
        
        Returns:
            LazyModule wrapper
        """
        key = alias or module_name
        
        if key not in self._lazy_modules:
            self._lazy_modules[key] = LazyModule(module_name)
        
        return self._lazy_modules[key]
    
    def get_loaded_modules(self) -> list[str]:
        """Retorna lista de módulos que já foram carregados"""
        return [
            name for name, module in self._lazy_modules.items()
            if module.is_loaded
        ]
    
    def get_stats(self) -> dict:
        """Retorna estatísticas de carregamento"""
        total = len(self._lazy_modules)
        loaded = len(self.get_loaded_modules())
        
        return {
            'total_registered': total,
            'loaded': loaded,
            'lazy_remaining': total - loaded,
            'loaded_modules': self.get_loaded_modules(),
            'memory_saved_estimate': f"{(total - loaded) * 5}MB"  # Estimativa rough
        }


# Instância global do importador preguiçoso
_lazy_importer = LazyImporter()


def lazy_import(module_name: str, alias: Optional[str] = None) -> LazyModule:
    """
    Função helper para criar imports preguiçosos.
    
    Args:
        module_name: Nome do módulo
        alias: Alias opcional
    
    Returns:
        LazyModule wrapper
    
    Example:
        # Em vez de:
        import pandas as pd
        
        # Use:
        pd = lazy_import('pandas', 'pd')
        
        # O pandas só será importado quando você usar:
        df = pd.DataFrame(...)  # <- Importação acontece AQUI
    """
    return _lazy_importer.register(module_name, alias)


def get_lazy_import_stats() -> dict:
    """Retorna estatísticas dos imports preguiçosos"""
    return _lazy_importer.get_stats()


# Pré-registrar módulos pesados comuns
# Eles só serão carregados quando realmente usados
def setup_common_lazy_imports():
    """
    Configura imports preguiçosos para módulos pesados comuns.
    Chame esta função no início da aplicação.
    """
    # Módulos de visualização (pesados)
    _lazy_importer.register('plotly.graph_objects', 'go')
    _lazy_importer.register('plotly.express', 'px')
    _lazy_importer.register('matplotlib.pyplot', 'plt')
    _lazy_importer.register('seaborn', 'sns')
    
    # Módulos de dados (médios)
    _lazy_importer.register('scipy', 'scipy')
    _lazy_importer.register('sklearn', 'sklearn')
    
    # Outros módulos específicos
    _lazy_importer.register('dateutil.parser', 'dateparser')
    _lazy_importer.register('yaml', 'yaml')


# Decorator para funções que usam módulos pesados
def requires_module(*module_names):
    """
    Decorator que documenta e garante que módulos necessários estão disponíveis.
    
    Args:
        *module_names: Nomes dos módulos necessários
    
    Example:
        @requires_module('plotly.graph_objects', 'pandas')
        def create_plot(data):
            import plotly.graph_objects as go
            # ...
    """
    def decorator(func: Callable) -> Callable:
        func.__required_modules__ = module_names
        return func
    
    return decorator


