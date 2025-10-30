"""
Configurações do agente e hierarquia de colunas
"""

# HIERARQUIA DE COLUNAS: Define níveis hierárquicos para filtros inteligentes
# IMPORTANTE: Filtros só se conflitam dentro da MESMA categoria hierárquica
COLUMN_HIERARCHY = {
    'cliente': [
        'Cod_Cliente',        # Mais específico (cliente individual)
        'Cod_Segmento_Cliente'  # Segmento do cliente (mais amplo)
    ],
    'regiao': [
        'Municipio_Cliente',  # Cidade do cliente (mais específico)
        'UF_Cliente'          # Estado do cliente (mais amplo)
    ],
    'produto': [
        'Cod_Produto',        # Produto específico
        'Cod_Familia_Produto', # Família do produto
        'Cod_Grupo_Produto',  # Grupo do produto
        'Cod_Linha_Produto',  # Linha do produto
        'Des_Linha_Produto'   # Descrição da linha (mais amplo)
    ],
    'vendedor': [
        'Cod_Vendedor',       # Vendedor específico
        'Cod_Regiao_Vendedor' # Região do vendedor (mais amplo)
    ]
}

# COMPORTAMENTO DE FILTROS: Define como cada tipo de campo deve ser tratado
FILTER_BEHAVIOR_CONFIG = {
    # Campos mutuamente exclusivos - apenas um valor por vez
    # Quando novo valor é mencionado, SUBSTITUI o anterior
    "exclusive_fields": {
        # Geográficos - apenas uma localização específica por vez
        'Municipio_Cliente': 'cidade_unica',
        'UF_Cliente': 'estado_unico',  # Pode ser múltiplo se explícito

        # Temporais específicos - períodos exatos se sobrepõem
        'Data': 'data_unica',
        'periodo_mes_ano': 'periodo_especifico',

        # Cliente específico - códigos únicos
        'Cod_Cliente': 'cliente_unico',
        'Cod_Segmento_Cliente': 'segmento_unico'
    },

    # Campos que podem ter múltiplos valores simultaneamente
    # Valores são ADICIONADOS, não substituídos
    "multi_value_fields": {
        # Produtos - múltiplos produtos/linhas podem ser analisados juntos
        'Cod_Familia_Produto', 'Cod_Grupo_Produto',
        'Cod_Linha_Produto', 'Des_Linha_Produto',

        # Representantes - múltiplos vendedores podem ser comparados
        'Cod_Vendedor', 'Cod_Regiao_Vendedor',

        # Ranges temporais - podem coexistir com filtros específicos
        'Data_>=', 'Data_<', 'Data_<=', 'Data_>'
    },

    # Grupos de campos relacionados que se sobrepõem
    "field_groups": {
        'temporal': {
            'specific': ['Data', 'periodo_mes_ano'],
            'range': ['Data_>=', 'Data_<', 'Data_<=', 'Data_>'],
            'descriptive': ['mes', 'ano', 'periodo']
        },
        'geographic': {
            'specific': ['Municipio_Cliente'],
            'broader': ['UF_Cliente']
        },
        'client': {
            'individual': ['Cod_Cliente'],
            'segment': ['Cod_Segmento_Cliente']
        }
    },

    # Campos que devem ser preservados no contexto quando não mencionados
    # Usado para gerar instruções dinâmicas no prompt
    "critical_preservation_fields": [
        'Cod_Cliente',           # Cliente específico
        'Municipio_Cliente',     # Cidade específica
        'UF_Cliente',            # Estado
        'Cod_Segmento_Cliente'   # Segmento do cliente
    ]
}

# Configurações do agente
AGENT_CONFIG = {
    "show_tool_calls": False,  # Será overridden por debug_mode
    "markdown": True,
    "run_code": True,
    "pip_install": False
}

# CONFIGURAÇÃO DE REMOÇÃO DE FILTROS - Detecção Inteligente
# Sistema para detectar quando usuário solicita explicitamente remover filtros
FILTER_REMOVAL_CONFIG = {
    # Padrões regex para detectar intenção de remoção
    # Formato: captura o termo mencionado (cidade, cliente, produto, etc.)
    "removal_patterns": [
        # "remover filtro de [termo]"
        r'\bremov(?:er|a|e)\s+(?:o\s+)?filtr[oa]s?\s+de\s+(\w+)',

        # "sem filtro de [termo]"
        r'\bsem\s+filtr[oa]s?\s+de\s+(\w+)',

        # "limpar [termo]" ou "limpar filtro de [termo]"
        r'\blimpar\s+(?:filtr[oa]s?\s+de\s+)?(\w+)',

        # "ignorar [termo]" ou "ignorar filtro de [termo]"
        r'\bignorar\s+(?:filtr[oa]s?\s+de\s+)?(\w+)',

        # "deletar [termo]" ou "apagar [termo]"
        r'\b(?:deletar|apagar)\s+(?:filtr[oa]s?\s+de\s+)?(\w+)',

        # "tirar [termo]" ou "retirar [termo]"
        r'\b(?:tirar|retirar)\s+(?:filtr[oa]s?\s+de\s+)?(\w+)',

        # "não filtrar por [termo]"
        r'\bn[ãa]o\s+filtrar\s+(?:por\s+)?(\w+)',
    ],

    # Mapeamento de termos → campos individuais
    # Quando usuário menciona termo, remove campo correspondente
    "field_mapping": {
        # Geográfico
        "cidade": ["Municipio_Cliente"],
        "cidades": ["Municipio_Cliente"],
        "municipio": ["Municipio_Cliente"],
        "estado": ["UF_Cliente"],
        "estados": ["UF_Cliente"],
        "uf": ["UF_Cliente"],
        "regiao": ["UF_Cliente", "Municipio_Cliente"],

        # Cliente
        "cliente": ["Cod_Cliente"],
        "clientes": ["Cod_Cliente"],
        "segmento": ["Cod_Segmento_Cliente"],

        # Temporal
        "data": ["Data", "Data_>=", "Data_<"],
        "datas": ["Data", "Data_>=", "Data_<"],
        "periodo": ["Data_>=", "Data_<"],
        "mes": ["Data_>=", "Data_<"],
        "ano": ["Data_>=", "Data_<"],

        # Produto
        "produto": ["Cod_Familia_Produto", "Cod_Grupo_Produto", "Cod_Linha_Produto", "Des_Linha_Produto"],
        "produtos": ["Cod_Familia_Produto", "Cod_Grupo_Produto", "Cod_Linha_Produto", "Des_Linha_Produto"],
        "familia": ["Cod_Familia_Produto"],
        "grupo": ["Cod_Grupo_Produto"],
        "linha": ["Cod_Linha_Produto", "Des_Linha_Produto"],

        # Representante
        "vendedor": ["Cod_Vendedor"],
        "vendedores": ["Cod_Vendedor"],
        "representante": ["Cod_Vendedor", "Cod_Regiao_Vendedor"],
    },

    # Mapeamento de categorias → múltiplos campos
    # Permite remoção de categoria completa
    "category_mapping": {
        "geografico": ["UF_Cliente", "Municipio_Cliente"],
        "geograficos": ["UF_Cliente", "Municipio_Cliente"],
        "temporal": ["Data", "Data_>=", "Data_<", "Data_<=", "Data_>"],
        "temporais": ["Data", "Data_>=", "Data_<", "Data_<=", "Data_>"],
    },

    # Padrões que indicam limpeza total de TODOS os filtros
    "clear_all_patterns": [
        r'\blimpar\s+todos\s+(?:os\s+)?filtros',
        r'\bremover\s+todos\s+(?:os\s+)?filtros',
        r'\bsem\s+filtros?(?:\s+algum)?$',
        r'\bsem\s+nenhum\s+filtro',
        r'\bzerar\s+filtros?',
        r'\bapagar\s+todos\s+(?:os\s+)?filtros',
        r'\blimpar\s+contexto',
    ]
}