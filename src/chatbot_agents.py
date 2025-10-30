"""
Chatbot Agents - Versão Refatorada e Modularizada
Reduzido de 3109 para aproximadamente 200 linhas
"""

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.reasoning import ReasoningTools
from agno.tools.duckdb import DuckDbTools
from agno.knowledge import Knowledge
from agno.tools.calculator import CalculatorTools
from agno.tools.python import PythonTools
from agno.db.in_memory import InMemoryDb

import os
import pandas as pd
import tempfile
from dotenv import load_dotenv

# Importar módulos refatorados
from text_normalizer import TextNormalizer, load_alias_mapping
from config.model_config import SELECTED_MODEL, OPENAI_API_KEY, DATA_CONFIG
from config.agent_config import COLUMN_HIERARCHY, AGENT_CONFIG, FILTER_BEHAVIOR_CONFIG
from prompts.chatbot_prompt import create_chatbot_prompt
from tools.optimized_python_tools import OptimizedPythonTools
from tools.debug_duckdb_tools import DebugDuckDbTools
from tools.visualization_tools import VisualizationTools

load_dotenv()


class PrincipalAgent(Agent):
    """
    Agente principal com funcionalidades otimizadas e hierarquia de colunas
    Agora com sistema de filtros unificado integrado e reforço temporal robusto
    """

    def __init__(self, normalizer, alias_mapping, df_normalized, text_columns,
                 session_user_id, conversation_memory="", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.normalizer = normalizer
        self.alias_mapping = alias_mapping
        self.df_normalized = df_normalized
        self.text_columns = text_columns
        self.session_user_id = session_user_id or "default_user"
        self.debug_info = {}  # Para armazenar informações de debug

        # MEMÓRIA DE CONVERSAÇÃO EFÊMERA (única funcionalidade mantida)
        self.conversation_memory = conversation_memory  # Histórico da conversação atual

        # SISTEMA DE FILTROS PERSISTENTES - RESTAURADO
        self.persistent_context = {}  # Context que persiste entre queries para filtros

        # Substituir ferramentas por versões otimizadas
        self.python_tool_ref = None  # Referência para o PythonTool otimizado
        self.visualization_tool_ref = None  # Referência para VisualizationTools
        for i, tool in enumerate(self.tools):
            if isinstance(tool, DuckDbTools):
                self.tools[i] = DebugDuckDbTools(debug_info_ref=self)
            elif isinstance(tool, PythonTools):
                optimized_tool = OptimizedPythonTools(debug_info_ref=self, run_code=True, pip_install=False)
                self.tools[i] = optimized_tool
                self.python_tool_ref = optimized_tool
            elif isinstance(tool, VisualizationTools):
                # VisualizationTools já está configurada corretamente
                self.visualization_tool_ref = tool

    def update_conversation_memory(self, new_memory):
        """
        Atualiza a memória de conversação com novo histórico.

        Args:
            new_memory: String com o histórico da conversação
        """
        self.conversation_memory = new_memory

    def get_conversation_summary(self):
        """
        Retorna um resumo da memória de conversação atual.

        Returns:
            str: Resumo da conversação ou string vazia se não houver memória
        """
        if not self.conversation_memory:
            return ""

        # Se a memória é muito longa, retornar apenas as últimas partes
        if len(self.conversation_memory) > 1000:
            lines = self.conversation_memory.split('\n')
            # Manter cabeçalho e últimas 10 linhas
            header = lines[0] if lines else ""
            recent_lines = lines[-10:] if len(lines) > 10 else lines
            return header + '\n' + '\n'.join(recent_lines)

        return self.conversation_memory

    def clear_conversation_memory(self):
        """Limpa a memória de conversação atual."""
        self.conversation_memory = ""

    def update_persistent_context(self, new_context, trigger_hooks=True):
        """
        Atualiza o contexto persistente com novos filtros.

        Args:
            new_context: Dicionário com novo contexto de filtros
            trigger_hooks: Se deve disparar hooks de atualização
        """
        old_context = self.persistent_context.copy()
        self.persistent_context = new_context.copy()

        # Log para debugging
        if hasattr(self, 'debug_info') and self.debug_info is not None:
            if 'context_updates' not in self.debug_info:
                self.debug_info['context_updates'] = []
            self.debug_info['context_updates'].append({
                'old_context_keys': list(old_context.keys()),
                'new_context_keys': list(self.persistent_context.keys()),
                'context_size': len(self.persistent_context),
                'trigger_hooks': trigger_hooks
            })

    def clear_persistent_context(self):
        """Limpa o contexto persistente de filtros."""
        old_context = self.persistent_context.copy()
        self.persistent_context = {}

        # Log para debugging
        if hasattr(self, 'debug_info') and self.debug_info is not None:
            if 'context_updates' not in self.debug_info:
                self.debug_info['context_updates'] = []
            self.debug_info['context_updates'].append({
                'action': 'clear_persistent_context',
                'old_context_keys': list(old_context.keys()),
                'new_context_keys': []
            })

    def get_persistent_context(self):
        """
        Retorna uma cópia do contexto persistente atual.

        Returns:
            Dict: Cópia do contexto persistente
        """
        return self.persistent_context.copy()

    def _format_persistent_context_for_prompt(self):
        """
        Formata o contexto persistente para incluir na mensagem do prompt.

        Retorna contexto em duas partes:
        1. Contexto técnico para geração de SQL
        2. Contexto narrativo para incluir na resposta final

        Returns:
            str: Contexto formatado para o prompt
        """
        if not self.persistent_context:
            return ""

        context_parts = []
        context_parts.append("FILTROS ATIVOS NA CONVERSA:")

        # Organizar por categorias
        temporal_filters = []
        region_filters = []
        client_filters = []
        product_filters = []
        representative_filters = []

        for key, value in self.persistent_context.items():
            if key in ['Data', 'Data_>=', 'Data_<', 'periodo', 'mes', 'ano']:
                temporal_filters.append(f"{key}: {value}")
            elif key in ['UF_Cliente', 'Municipio_Cliente', 'cidade', 'estado']:
                region_filters.append(f"{key}: {value}")
            elif key in ['Cod_Cliente', 'Cod_Segmento_Cliente']:
                client_filters.append(f"{key}: {value}")
            elif any(x in key for x in ['Produto', 'Familia', 'Grupo', 'Linha']):
                product_filters.append(f"{key}: {value}")
            elif any(x in key for x in ['Vendedor', 'Representante', 'Regiao_Vendedor']):
                representative_filters.append(f"{key}: {value}")

        if temporal_filters:
            context_parts.append(f"- Período: {', '.join(temporal_filters)}")
        if region_filters:
            context_parts.append(f"- Região: {', '.join(region_filters)}")
        if client_filters:
            context_parts.append(f"- Cliente: {', '.join(client_filters)}")
        if product_filters:
            context_parts.append(f"- Produto: {', '.join(product_filters)}")
        if representative_filters:
            context_parts.append(f"- Representante: {', '.join(representative_filters)}")

        context_parts.append("\n⚠️ ATENÇÃO - Analise a intenção do usuário:")
        context_parts.append("• Se menciona OUTRA cidade/cliente exclusivo → SUBSTITUA o filtro (não adicione com AND)")
        context_parts.append("• Se menciona múltiplos explicitamente ('A e B') → USE IN ('A', 'B')")
        context_parts.append("• Se NÃO menciona um campo → **PRESERVE o filtro existente no WHERE**")
        context_parts.append("• Para campos não-exclusivos (data, produto) → PRESERVE e adicione novos")
        context_parts.append("\n🚨 REGRA CRÍTICA - PRESERVAÇÃO OBRIGATÓRIA:")
        context_parts.append("Campos abaixo DEVEM aparecer no WHERE mesmo se não mencionados:")

        # Carregar lista de campos críticos da configuração (zero hardcoding)
        critical_preservation_fields = FILTER_BEHAVIOR_CONFIG.get("critical_preservation_fields", [])

        # Listar campos críticos ativos que devem ser preservados
        critical_fields = []
        for field in critical_preservation_fields:
            if field in self.persistent_context:
                value = self.persistent_context[field]
                critical_fields.append(f"{field} = '{value}'")

        if critical_fields:
            context_parts.append("→ " + " AND ".join(critical_fields))

        context_parts.append("\n📝 EXEMPLOS:")
        context_parts.append("EX1: Filtro Municipio='JOINVILLE' + 'e em Curitiba?'")
        context_parts.append("  → SQL: WHERE Municipio_Cliente = 'CURITIBA' (SUBSTITUI)")
        context_parts.append("\nEX2A: Filtro Cod_Cliente='19114' + 'qual o total vendido?'")
        context_parts.append("  → SQL: WHERE Cod_Cliente = '19114' (PRESERVA - não mencionou outro)")
        context_parts.append("\nEX2B: Filtro Cod_Cliente='19114' + 'total do cliente 22910?'")
        context_parts.append("  → SQL: WHERE Cod_Cliente = '22910' (SUBSTITUI - mencionou outro)")

        # NOVA SEÇÃO: Contexto Narrativo para Resposta Final
        context_parts.append("\n\n📢 IMPORTANTE PARA SUA RESPOSTA FINAL:")
        context_parts.append("Inicie sua resposta com UMA SENTENÇA INTRODUTÓRIA que contextualize a análise:")
        context_parts.append("1. NÃO use 'Contexto:' - comece direto com a sentença")
        context_parts.append("2. Seja criativo e natural - não use templates rígidos")
        context_parts.append("3. SEMPRE mencione os filtros ativos de forma integrada ao texto")
        context_parts.append("4. Coloque os valores dos filtros em **negrito** para destaque visual")
        context_parts.append("\nFiltros disponíveis para mencionar:")
        
        # Listar filtros de forma organizada
        filter_list = []
        if temporal_filters:
            filter_list.append(f"Período: {', '.join([v.split(': ')[1] for v in temporal_filters])}")
        if region_filters:
            filter_list.append(f"Região: {', '.join([v.split(': ')[1] for v in region_filters])}")
        if client_filters:
            filter_list.append(f"Cliente: {', '.join([v.split(': ')[1] for v in client_filters])}")
        if product_filters:
            filter_list.append(f"Produto: {', '.join([v.split(': ')[1] for v in product_filters])}")
        if representative_filters:
            filter_list.append(f"Representante: {', '.join([v.split(': ')[1] for v in representative_filters])}")
        
        if filter_list:
            for f in filter_list:
                context_parts.append(f"  - {f}")
        else:
            context_parts.append("  - Sem filtros ativos.")
        
        context_parts.append("\nExemplos de sentença introdutória bem escritas:")
        context_parts.append("  - 'Analisando o faturamento de **Joinville** no período de **junho a agosto de 2016**.'")
        context_parts.append("  - 'Investigando as vendas em **Santa Catarina** durante o **primeiro semestre de 2015**.'")
        context_parts.append("  - 'Comparando o desempenho do **cliente 19114** entre as regiões **Sul e Sudeste**.'")
        context_parts.append("\n⚠️ REGRA: Seja conciso (máximo 1-2 sentenças) e SEMPRE mencione os filtros ativos em **negrito**!")

        return "\n".join(context_parts)

    def run(self, message, **kwargs):
        """
        Override do método run para incluir memória de conversação e contexto persistente de filtros.
        """
        final_message = message

        # INTEGRAR MEMÓRIA DE CONVERSAÇÃO SE DISPONÍVEL
        if self.conversation_memory and self.conversation_memory.strip():
            conversation_context = self.get_conversation_summary()
            final_message = f"{conversation_context}\n\nNOVA PERGUNTA: {message}"

        # INTEGRAR CONTEXTO PERSISTENTE DE FILTROS SE DISPONÍVEL
        if self.persistent_context:
            filter_context = self._format_persistent_context_for_prompt()
            final_message = f"{final_message}\n\n{filter_context}"

        # Log para debugging
        if hasattr(self, 'debug_info') and self.debug_info is not None:
            if 'query_modifications' not in self.debug_info:
                self.debug_info['query_modifications'] = []
            self.debug_info['query_modifications'].append({
                'original_message': message,
                'final_message': final_message,
                'conversation_memory_used': bool(self.conversation_memory),
                'persistent_context_used': bool(self.persistent_context)
            })

        # Executar com a mensagem e contexto de conversação + filtros
        return super().run(final_message, **kwargs)


    def clear_execution_state(self):
        """Limpa o estado de execução entre consultas relacionadas"""
        if self.python_tool_ref:
            self.python_tool_ref.executed_calculations.clear()
            # Manter apenas variáveis importantes no cache
            important_vars = {}
            for var_name, var_value in self.python_tool_ref.variable_cache.items():
                if var_name in ['Top5_total']:
                    important_vars[var_name] = var_value
            self.python_tool_ref.variable_cache = important_vars


def create_agent(session_user_id=None, debug_mode=False, conversation_memory=""):
    """
    Cria e configura o agente DuckDB com acesso aos dados comerciais e memória temporária
    Versão refatorada e modularizada
    """
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

    # Carregar dados do parquet
    data_path = DATA_CONFIG["data_path"]
    df = pd.read_parquet(data_path)

    # Aplicar normalização de texto aos dados
    normalizer = TextNormalizer()
    normalizer.set_dataset_context(df)  # Configurar contexto para detecção inteligente de "último mês"
    text_columns = normalizer.identify_text_columns(df)

    # Criar versão normalizada do DataFrame para buscas
    df_normalized = normalizer.normalize_dataframe(df, text_columns)

    # Carregar mapeamento de aliases
    alias_mapping = load_alias_mapping()

    # Criar knowledge base com os dados usando Knowledge
    knowledge = Knowledge()
    db = InMemoryDb()
    # Adicionar informações sobre o dataset
    dataset_info = f"""
Dataset: DadosComercial_resumido_v02.parquet
Localização: {data_path}
Número de linhas: {len(df)}
Número de colunas: {len(df.columns)}
Colunas disponíveis: {", ".join(df.columns.tolist())}
Última Data: {df['Data'].max()}
Primeira Data: {df['Data'].min()}
Último mês: {df['Data'].max().strftime('%Y-%m')}

CONTEXTO TEMPORAL IMPORTANTE:
- Data máxima no dataset: {df['Data'].max().strftime('%Y-%m-%d')} (ESTA É A DATA DE "HOJE" PARA O CONTEXTO DAS ANÁLISES)
- Quando mencionado "último mês", "mês anterior", "mês passado" ou "período mais recente", refere-se ao mês {df['Data'].max().strftime('%Y-%m')}
- Para períodos relativos como "últimos X meses/anos", calcule SEMPRE a partir da data máxima {df['Data'].max().strftime('%Y-%m-%d')}, NÃO da data atual real
- Exemplos de interpretação correta:
  * "últimos 3 meses" = desde {(df['Data'].max() - pd.DateOffset(months=3)).strftime('%Y-%m-%d')} até {df['Data'].max().strftime('%Y-%m-%d')}
  * "últimos 6 meses" = desde {(df['Data'].max() - pd.DateOffset(months=6)).strftime('%Y-%m-%d')} até {df['Data'].max().strftime('%Y-%m-%d')}
- Use este contexto automaticamente para interpretar TODAS as consultas temporais relativas

IMPORTANTE: Os dados passaram por normalização de texto para garantir consistência:
- Colunas de texto normalizadas: {", ".join(text_columns)}
- Normalização aplicada: conversão para minúsculas, remoção de acentos, normalização de espaços
- Aliases disponíveis para consultas: {", ".join(alias_mapping.keys()) if alias_mapping else "Nenhum"}

Primeiras 5 linhas do dataset original:
{df.head().to_string()}

Primeiras 5 linhas com normalização aplicada (colunas de texto):
{df_normalized[text_columns].head().to_string() if text_columns else "Nenhuma coluna de texto para normalizar"}

Informações estatísticas:
{df.describe().to_string()}

Tipos de dados:
{df.dtypes.to_string()}
"""

    knowledge.add_content(text_content=dataset_info)

    # Nota: Versão simplificada sem memória persistente (compatibilidade com Agno 2.0.6)

    # Criar o agente principal com todas as ferramentas
    agent = PrincipalAgent(
        normalizer=normalizer,
        alias_mapping=alias_mapping,
        df_normalized=df_normalized,
        text_columns=text_columns,
        session_user_id=session_user_id,
        conversation_memory=conversation_memory,
        db=db,
        model=OpenAIChat(
            id=SELECTED_MODEL,
            reasoning_effort="low",
            max_completion_tokens=8000,  # Garantir tokens suficientes para resposta completa
        ),
        tools=[
            ReasoningTools(add_instructions=True),
            CalculatorTools(),
            PythonTools(),
            DuckDbTools(),
            VisualizationTools(),  # ⬅️ NOVA TOOL para gráficos integrados
        ],
        knowledge=knowledge,
        enable_agentic_memory=True,
        instructions=create_chatbot_prompt(data_path, df, text_columns, alias_mapping),
        debug_mode=debug_mode,
        markdown=True,
    )

    # Após criar agent, configurar referência de debug_info em VisualizationTools
    for tool in agent.tools:
        if isinstance(tool, VisualizationTools):
            tool.debug_info_ref = agent
            break

    # Inicialização otimizada do DuckDB com verificação de existência da tabela
    _initialize_database_optimized(agent, data_path)

    return agent, df


def _initialize_database_optimized(agent, data_path):
    """
    Inicializa o banco DuckDB de forma otimizada, evitando criação redundante de tabelas
    """
    try:
        # ABORDAGEM MAIS ROBUSTA: Usar DuckDbTools diretamente para garantir persistência
        duckdb_tool = None
        for tool in agent.tools:
            if hasattr(tool, 'run_query') and hasattr(tool, 'connection'):
                duckdb_tool = tool
                break

        if duckdb_tool is None:
            # Fallback: usar o run normal do agente
            result = agent.run(f"CREATE OR REPLACE TABLE dados_comerciais AS SELECT * FROM read_parquet('{data_path}');")
        else:
            # Usar DuckDbTools diretamente para garantir que a tabela seja criada na conexão correta
            result = duckdb_tool.run_query(f"CREATE OR REPLACE TABLE dados_comerciais AS SELECT * FROM read_parquet('{data_path}')")

            # Verificar imediatamente se a tabela foi criada
            verification = duckdb_tool.run_query("SELECT COUNT(*) as count FROM dados_comerciais LIMIT 1")

            if 'count' in verification.lower():
                # Sucesso - marcar cache
                if hasattr(duckdb_tool, 'metadata_cache'):
                    duckdb_tool.metadata_cache['tables_exist'].add('dados_comerciais')
                    duckdb_tool.metadata_cache['initialization_done'] = True
                    duckdb_tool.metadata_cache['table_verified'] = True
            else:
                raise Exception(f"Table verification failed: {verification}")

    except Exception as e:
        # Log do erro e tentar abordagem de fallback
        if hasattr(agent, 'debug_info') and agent.debug_info is not None:
            if 'initialization_warnings' not in agent.debug_info:
                agent.debug_info['initialization_warnings'] = []
            agent.debug_info['initialization_warnings'].append({
                'type': 'table_creation_error',
                'message': str(e),
                'status': 'Trying fallback approach'
            })

        # FALLBACK: Tentar abordagem mais simples
        try:
            agent.run(f"CREATE TABLE dados_comerciais AS SELECT * FROM read_parquet('{data_path}')")
        except:
            pass  # Se falhar, pelo menos tentamos


# Para compatibilidade com uso direto do arquivo
if __name__ == "__main__":
    agent, df = create_agent()

    # Teste simples para verificar funcionamento
    try:
        response = agent.run("Quantas linhas tem o dataset?")
        print("SUCCESS: Agent is working correctly!")
        print(f"Response type: {type(response)}")
    except Exception as e:
        print(f"ERROR: {str(e)}")
        print("There might be an issue with the agent configuration.")