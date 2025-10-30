"""
Exemplos detalhados para o chatbot Agno
Carregados sob demanda para reduzir tamanho do prompt principal
"""

# =============================================================================
# EXEMPLOS DE RESPOSTAS COMPLETAS
# =============================================================================

EXAMPLE_RANKING_WITH_FILTERS = """
## Top 5 Produtos Mais Vendidos

Analisando os produtos com maior faturamento na **região Sul** durante o **primeiro trimestre de 2025**, com foco em **Pneus Premium**.

### 💡 Principais Insights

- **Concentração elevada**: Top 3 produtos representam 71% do faturamento total dos 5 principais
- **Liderança destacada**: Primeiro colocado com 35% do volume, equivalente a 1,8x o segundo
- **Gap significativo**: Diferença de R$ 420K entre 3º e 4º posição indica oportunidade de reposicionamento
- **Performance regional**: Produto líder tem 65% das vendas concentradas em SC

### 🔍 Próximos Passos

Posso aprofundar esta análise:
- Compare este trimestre com o mesmo período do ano anterior
- Analise margem de lucro destes top 5 produtos
- Investigue mix de vendas por vendedor/representante
"""

EXAMPLE_TEMPORAL_NO_FILTERS = """
## Evolução de Vendas - 2015

Explorando a evolução mensal de vendas ao longo de **2015**, sem filtros adicionais aplicados à análise.

### 💡 Principais Insights

- **Crescimento sustentado**: Tendência ascendente com aumento de 32% entre janeiro e dezembro
- **Sazonalidade identificada**: Picos consistentes em março (+15%), julho (+18%) e dezembro (+25%)
- **Aceleração no segundo semestre**: 58% do faturamento anual concentrado entre julho e dezembro
- **Volatilidade controlada**: Variação média mês-a-mês de 8%, indicando previsibilidade

### 🔍 Próximos Passos

Posso aprofundar esta análise:
- Compare 2015 com anos anteriores (2014 e 2013)
- Detalhe performance por região geográfica
- Identifique produtos que impulsionaram os picos sazonais
"""

EXAMPLE_COMPARISON_COMPLEX_FILTERS = """
## Comparação de Vendas: São Paulo vs Rio de Janeiro

Comparando o desempenho de vendas entre **SP e RJ** no **segundo semestre de 2024**, especificamente para o segmento **Atacado** na **Linha Industrial**.

### 💡 Principais Insights

- **SP lidera com margem expressiva**: Faturamento de R$ 2,8M representa 62% do total, superando RJ em +24 p.p.
- **Crescimento assimétrico**: SP cresceu 18% vs 2024-S1, enquanto RJ manteve estabilidade (+2%)
- **Concentração de clientes**: 80% do volume de SP vem de 3 clientes principais, vs 55% em RJ
- **Oportunidade em RJ**: Base mais diversificada indica potencial de expansão com menor risco

### 🔍 Próximos Passos

Posso aprofundar esta análise:
- Analise margem de contribuição por estado para avaliar rentabilidade
- Investigue performance por vendedor em cada região
- Compare com outras linhas de produto para identificar padrões
"""

# =============================================================================
# EXEMPLOS BEFORE/AFTER (Insights Ruins vs Bons)
# =============================================================================

INSIGHT_EXAMPLES_BEFORE_AFTER = {
    "ranking_clientes": {
        "incorreto": """
### 💡 Principais Insights
- SC é responsável pela maior fatia das vendas
- RS é o segundo maior contribuinte
- A distribuição entre os estados é desigual
- Top 3 clientes representam 71% do volume total (SEM valores absolutos)
""",
        "correto": """
### 💡 Principais Insights
- **Concentração significativa**: Os top 3 clientes representam 71% do volume total dos 5 principais **(Top 3 = 27.0M un / Top 5 = 38.0M un)**
- **Cliente líder destaca-se**: Primeira posição com 38M unidades equivale a 37% do top 5 **(14.1M un / 38.0M un)**
- **Gap expressivo**: Diferença de 17M unidades entre 1º e 2º colocado **(18.5M un vs 11.2M un, múltiplo 1.65x)** indica forte liderança consolidada
- **Desvio do líder**: 105% acima da média **(Líder = 18.5M un / Média = 9.0M un)**
"""
    },
    
    "comparacao_estados": {
        "incorreto": """
### 💡 Principais Insights
- SC é o estado com maior volume
- RS é o segundo
- PR é o terceiro
- A distribuição é diferente entre os estados
- SC lidera com 43% do total (SEM valores absolutos)
""",
        "correto": """
### 💡 Principais Insights
- **SC lidera com 43% do total de vendas** **(R\\$ 8.6M / R\\$ 20.0M)**, superando RS em +12 p.p. **(RS = R\\$ 6.2M / R\\$ 20.0M = 31%)** e PR em +19 p.p. **(PR = R\\$ 4.8M / R\\$ 20.0M = 24%)**
- **Concentração parcial**: RS e PR combinados representam 57% do total **(R\\$ 11.0M / R\\$ 20.0M)**, indicando que o mercado não está completamente monopolizado
- **Gap significativo**: SC vendeu R\\$ 1.2M a mais que a média dos outros dois estados **(SC = R\\$ 8.6M vs Média RS+PR = R\\$ 5.5M, +56% acima da média regional)**
"""
    },
    
    "analise_temporal": {
        "incorreto": """
### 💡 Principais Insights
- Vendas cresceram ao longo do ano
- Dezembro teve o melhor resultado
- Janeiro foi o pior mês
- Crescimento de 32% no período (SEM valores absolutos)
""",
        "correto": """
### 💡 Principais Insights
- **Crescimento sustentado**: Tendência ascendente de 32% entre janeiro e dezembro **(R\\$ 1.8M → R\\$ 2.4M, +R\\$ 600K)**
- **Sazonalidade marcada**: Picos em março **(R\\$ 2.1M, +15% vs fev)**, julho **(R\\$ 2.3M, +18% vs jun)** e dezembro **(R\\$ 2.4M, +25% vs nov)** coincidem com campanhas sazonais
- **Segundo semestre forte**: Concentra 58% do faturamento anual **(H2 = R\\$ 11.6M / Total = R\\$ 20.0M)**, sugerindo aceleração no H2 **(H2 média = R\\$ 1.93M vs H1 média = R\\$ 1.40M, +38%)**
- **Amplitude significativa**: Variação de R\\$ 1.1M entre pico e vale **(Pico: R\\$ 2.4M em dez, Vale: R\\$ 1.3M em fev = +85%)**
"""
    },
    
    "analise_produtos": {
        "incorreto": """
### 💡 Principais Insights
- Produto A: R$ 1.000.000
- Produto B: R$ 800.000
- Produto C: R$ 600.000
- Produto D: R$ 450.000
- Produto E: R$ 320.000
""",
        "correto": """
### 💡 Principais Insights
- **Concentração elevada**: Top 3 produtos (A, B, C) representam 74% do faturamento total, indicando dependência de poucos SKUs
- **Produto líder domina**: Produto A com R$ 1M corresponde a 31% das vendas, sendo 1,25x maior que B
- **Oportunidade de crescimento**: Produtos D e E (juntos 24% das vendas) apresentam margem superior e potencial de expansão
"""
    }
}

# =============================================================================
# EXEMPLOS DE PRÓXIMOS PASSOS CONTEXTUAIS
# =============================================================================

NEXT_STEPS_EXAMPLES = {
    "ranking_com_filtro_temporal": """
- Compare este período com o trimestre anterior
- Analise margem de lucro destes top produtos
- Investigue sazonalidade por categoria
""",
    
    "serie_temporal_sem_filtros": """
- Detalhe esta evolução por estado/região
- Identifique produtos que impulsionaram crescimento
- Compare com anos anteriores
""",
    
    "comparacao_com_filtro_cliente": """
- Analise performance deste cliente em outros estados
- Compare com outros clientes do mesmo segmento
- Investigue margem de contribuição por estado
"""
}

# =============================================================================
# EXEMPLOS DE QUERIES SQL CORRETAS
# =============================================================================

SQL_EXAMPLES = {
    "ranking_simples": """
-- Top 5 clientes por faturamento
SELECT Cod_Cliente, SUM(Valor_Vendido) AS Total_Vendido
FROM dados_comerciais
WHERE LOWER(Municipio_Cliente) = 'joinville'
GROUP BY Cod_Cliente
ORDER BY Total_Vendido DESC LIMIT 5
""",
    
    "serie_temporal_unica": """
-- Evolução mensal de vendas em 2015
SELECT DATE_TRUNC('month', Data) as mes_ano, SUM(Valor_Vendido) as total_vendas
FROM dados_comerciais
WHERE EXTRACT(YEAR FROM Data) = 2015
GROUP BY mes_ano
ORDER BY mes_ano
""",
    
    "serie_temporal_multipla": """
-- Comparar vendas de SC, PR e RS ao longo do tempo
SELECT
  DATE_TRUNC('month', Data) as mes_ano,
  UF_Cliente as categoria,
  SUM(Valor_Vendido) as total_vendas
FROM dados_comerciais
WHERE UF_Cliente IN ('SC', 'PR', 'RS')
GROUP BY mes_ano, UF_Cliente
ORDER BY mes_ano, UF_Cliente
""",
    
    "comparacao_vertical_bar": """
-- Comparar vendas entre março e abril de 2015
SELECT
  CASE
    WHEN EXTRACT(MONTH FROM Data) = 3 THEN 'Março/2015'
    WHEN EXTRACT(MONTH FROM Data) = 4 THEN 'Abril/2015'
  END as periodo,
  SUM(Valor_Vendido) as total
FROM dados_comerciais
WHERE EXTRACT(YEAR FROM Data) = 2015
  AND EXTRACT(MONTH FROM Data) IN (3, 4)
GROUP BY periodo
ORDER BY MIN(Data)
"""
}

# =============================================================================
# EXEMPLOS DE CENÁRIOS DE FILTROS
# =============================================================================

FILTER_SCENARIO_EXAMPLES = {
    "preservacao_automatica": """
Filtros ativos: Municipio_Cliente = JOINVILLE, Data_>= 2016-06-01
Nova pergunta: "Qual é o total de vendas em 2015?" (SEM mencionar Joinville)
Comportamento: Sistema preserva automaticamente filtro de Joinville + adiciona filtro de 2015
""",
    
    "substituicao_cidade": """
Filtros ativos: Municipio_Cliente = JOINVILLE, Data_>= 2016-06-01
Nova pergunta: "e em Curitiba?"
SQL CORRETO:
WHERE Municipio_Cliente = 'CURITIBA'
  AND Data >= '2016-06-01'
""",
    
    "preservacao_cliente": """
Filtros ativos: Cod_Cliente = 19114, UF_Cliente = PR, Data_>= 2015-01-01
Nova pergunta: "qual foi o total vendido?" (SEM mencionar cliente)
SQL CORRETO:
WHERE Cod_Cliente = '19114'  -- PRESERVA (não mencionado!)
  AND UF_Cliente = 'PR'
  AND Data >= '2015-01-01'
""",
    
    "substituicao_cliente": """
Filtros ativos: Cod_Cliente = 19114, UF_Cliente = PR, Data_>= 2015-01-01
Nova pergunta: "Qual o total vendido pelo cliente 22910?"
SQL CORRETO:
WHERE Cod_Cliente = '22910'  -- SUBSTITUI 19114 por 22910
  AND UF_Cliente = 'PR'
  AND Data >= '2015-01-01'
"""
}

# =============================================================================
# TEMPLATE DE RESPOSTA COMPLETA
# =============================================================================

RESPONSE_TEMPLATE_COMPLETE = """
## [Título Claro e Específico]

[Sentença introdutória: 1-2 sentenças curtas, naturais e contextualizadas mencionando os filtros ativos em **negrito**]

Exemplos:
- "Analisando o faturamento de **Joinville** no período de **junho a agosto de 2016**."
- "Comparando vendas em **SC e PR** durante o **primeiro trimestre de 2015**."
- "Investigando o desempenho do **cliente 19114** sem filtros adicionais aplicados."

[GRÁFICO SERÁ INSERIDO AUTOMATICAMENTE AQUI]

### 💡 Principais Insights

- **[Título do Insight 1]**: [Interpretação com métrica derivada - %, múltiplos, gaps, p.p.]
- **[Título do Insight 2]**: [Padrão ou tendência identificada com números contextualizados]
- **[Título do Insight 3]**: [Comparação relativa ou análise de concentração]
- **[Título do Insight 4]**: [Oportunidade, risco ou recomendação estratégica]

### 🔍 Próximos Passos

Posso aprofundar esta análise:
- [Sugestão específica e acionável 1]
- [Sugestão específica e acionável 2]
"""

