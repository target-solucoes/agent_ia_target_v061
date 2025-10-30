"""
Numeric Formatter - Formatação de Métricas para LLM
Responsável por transformar métricas calculadas em prompts estruturados
"""

import json
from typing import Dict, Any


def gerar_prompt_insights(resumo_numerico: Dict[str, Any], tipo_grafico: str, max_insights: int = 5) -> str:
    """
    Gera prompt estruturado para a LLM criar insights inteligentes.
    
    Este prompt será injetado no contexto do agente para guiar
    a geração de insights baseados no resumo numérico.
    
    Args:
        resumo_numerico: Dicionário com métricas calculadas
        tipo_grafico: Tipo do gráfico
        max_insights: Número máximo de insights desejados (padrão: 5)
    
    Returns:
        String formatada com prompt para LLM
    """
    # Formatar resumo de forma legível
    resumo_formatado = json.dumps(resumo_numerico, indent=2, ensure_ascii=False)

    # Template base do prompt
    prompt = f"""
🧮 RESUMO NUMÉRICO ESTRUTURADO DISPONÍVEL

Você recebeu um resumo analítico pré-calculado com métricas derivadas:

```json
{resumo_formatado}
```

## 🎯 TAREFA: Gerar {max_insights} Insights Estratégicos

Use o resumo numérico acima como BASE ANALÍTICA para gerar insights não-óbvios.

### ✅ O QUE FAZER:
- Interpretar padrões e implicações (não apenas descrever números)
- Usar métricas derivadas (concentração_top3_pct, gap_1_2_pct, multiplo_1_vs_2, etc.)
- **⚠️ TRANSPARÊNCIA OBRIGATÓRIA**: SEMPRE incluir valores absolutos que fundamentam os cálculos
  - Formato: "X% (Valor Base = R\\$ A / Total = R\\$ B)"
  - Exemplo: "20.5% (Top 5 = R\\$ 4.1M / Total = R\\$ 20.0M)"
- Focar em PROPORÇÕES e RELAÇÕES, mas tornar transparentes os números usados
- Identificar oportunidades ou riscos estratégicos
- Usar **negrito** para palavras-chave importantes

### ❌ O QUE NÃO FAZER:
- Repetir valores que estão visíveis no gráfico
- Listar dados sem interpretação ("A é maior que B")
- Usar frases genéricas ("distribuição desigual")
- Mencionar mais de {max_insights} insights
- **Apresentar métricas derivadas SEM mostrar os valores base do cálculo**

### 📋 ESTRUTURA OBRIGATÓRIA:
Cada insight deve ter este formato:
- **Título descritivo**: Interpretação com números contextualizados (%, múltiplos, pontos percentuais) **+ valores absolutos entre parênteses**

### 🎨 EXEMPLOS DE TRANSFORMAÇÃO:

❌ ERRADO (sem valores base):
- "SC é o maior estado"
- "Top 5 clientes respondem por 20.5% do faturamento total"
- "O 1º colocado é 18.3% superior ao 2º"

✅ CORRETO (com valores base explícitos):
- "**Concentração significativa**: SC representa 43% do total **(R\\$ 8.6M / R\\$ 20.0M)**, superando RS em +12 p.p."
- "**Concentração do Top 5**: Top 5 clientes respondem por 20.5% do faturamento total **(Top 5 = R\\$ 4.1M / Total = R\\$ 20.0M)**"
- "**Liderança vs 2º**: O 1º colocado é 18.3% superior ao 2º **(R\\$ 1.18M vs R\\$ 1.0M, múltiplo 1.18x)**"

---
"""

    # Adicionar diretrizes específicas por tipo de gráfico
    if tipo_grafico == "horizontal_bar":
        prompt += """
### 📊 FOCO PARA RANKINGS:

**⚠️ TRANSPARÊNCIA OBRIGATÓRIA para rankings:**
Sempre incluir os valores absolutos que fundamentam cada métrica:

1. **Concentração** (top N representa X% do total) → **Formato: "(Top N = R\\$ X / Total = R\\$ Y)"**
   - Use: `concentracao_top3_pct`, `total_topn`, `total_universo`

2. **Gap entre liderança e demais** → **Formato: "(R\\$ X vs R\\$ Y, múltiplo Zx)"**
   - Use: `gap_1_2_pct`, `valor_max`, valores específicos, `multiplo_1_vs_2`

3. **Desvio do líder vs média** → **Formato: "(Líder = R\\$ X / Média = R\\$ Y)"**
   - Use: `desvio_lider_media_pct`, `valor_max`, `media`

4. **Contribuição do líder** → **Formato: "(R\\$ X / R\\$ Y = Z%)"**
   - Use: `contribuicao_lider_pct`, `valor_max`, `total_universo`

**Métricas-chave disponíveis**:
- `concentracao_top3_pct` / `concentracao_top5_pct`: % do total no top N
- `total_topn`: Soma do Top N exibido
- `total_universo`: Soma total do universo completo filtrado
- `gap_1_2_pct`: Diferença percentual entre 1º e 2º
- `valor_max`, `valor_min`: Valores do líder e último colocado
- `multiplo_1_vs_2`: Quantas vezes o líder é maior que o segundo
- `contribuicao_lider_pct`: Participação do líder no total
- `desvio_lider_media_pct`: Quanto o líder está acima da média
- `media`: Média dos valores

**Exemplos de insights COMPLETOS com transparência:**
- "**Concentração do Top 5**: 20.5% do faturamento total **(Top 5 = R\\$ 4.1M / Total = R\\$ 20.0M)**"
- "**Liderança vs 2º**: O 1º colocado é 18.3% superior **(R\\$ 1.18M vs R\\$ 1.0M, múltiplo 1.18x)**"
- "**Contribuição do líder**: Representa 8.4% do total de SC **(R\\$ 1.68M / R\\$ 20.0M)**"
- "**Dispersão do líder**: 105% acima da média **(Líder = R\\$ 1.68M / Média = R\\$ 0.82M)**"
"""

    elif tipo_grafico == "vertical_bar":
        prompt += """
### 📊 FOCO PARA COMPARAÇÕES:

**⚠️ TRANSPARÊNCIA OBRIGATÓRIA para comparações:**
Sempre incluir os valores absolutos que fundamentam cada métrica:

1. **Diferença percentual entre categorias** → **Formato: "(R\\$ X vs R\\$ Y, diferença de Z%)"**
   - Use: `diferenca_pct`, `valor_maior`, `valor_menor`

2. **Proporções relativas** → **Formato: "(SC = R\\$ X / Total = R\\$ Y = Z%)"**
   - Use: `contribuicao_maior_pct`, `contribuicao_menor_pct`, valores absolutos

3. **Diferença em pontos percentuais** → **Formato: "X% vs Y% (+Z p.p.)"**
   - Use: `diferenca_pontos_percentuais`, valores de participação

**Métricas-chave disponíveis**:
- `diferenca_pct`: Diferença % entre maior e menor
- `valor_maior`, `valor_menor`: Valores absolutos das categorias
- `diferenca_pontos_percentuais`: Diferença em p.p.
- `contribuicao_maior_pct` / `contribuicao_menor_pct`: Share de cada
- `proporcao_relativa`: Proporção formatada (ex: "60% vs 40%")
- `total_geral`: Soma total para contexto

**Exemplos de insights COMPLETOS com transparência:**
- "**SC lidera**: 43% do total **(R\\$ 8.6M / R\\$ 20.0M)**, superando RJ em 12 p.p. **(RJ = R\\$ 6.2M / R\\$ 20.0M = 31%)**"
- "**Diferença significativa**: Maior categoria supera a menor em 58% **(R\\$ 3.2M vs R\\$ 2.0M)**"
- "**Proporção equilibrada**: 52% vs 48% **(R\\$ 10.4M vs R\\$ 9.6M)**, indicando distribuição uniforme"
"""

    elif tipo_grafico == "line":
        prompt += """
### 📊 FOCO PARA SÉRIES TEMPORAIS:

**⚠️ TRANSPARÊNCIA OBRIGATÓRIA para séries temporais:**
Sempre incluir os valores absolutos que fundamentam cada métrica:

1. **Taxa de crescimento** → **Formato: "(R\\$ X → R\\$ Y, +Z%)"**
   - Use: `taxa_crescimento_pct`, `valor_inicial`, `valor_final`

2. **Picos e vales** → **Formato: "(Pico: R\\$ X em [data], Vale: R\\$ Y em [data])"**
   - Use: `pico_valor`, `pico_periodo`, `vale_valor`, `vale_periodo`

3. **Amplitude** → **Formato: "(Variação de R\\$ X, amplitude de Y%)"**
   - Use: `amplitude`, `amplitude_pct`

4. **Aceleração** → **Formato: "(H1 média R\\$ X vs H2 média R\\$ Y, +Z%)"**
   - Use: `aceleracao_segunda_metade_pct`, calcular médias quando possível

**Métricas-chave disponíveis**:
- `tendencia`: "crescente", "decrescente" ou "estável"
- `taxa_crescimento_pct`: Crescimento total do período
- `valor_inicial`, `valor_final`: Valores de início e fim
- `pico_valor` / `pico_periodo`: Valor máximo e quando ocorreu
- `vale_valor` / `vale_periodo`: Valor mínimo e quando ocorreu
- `amplitude`, `amplitude_pct`: Variação entre pico e vale
- `aceleracao_segunda_metade_pct`: Comparação H1 vs H2
- `comportamento_temporal`: Padrão identificado
- `variacao_media_pct`: Variação média período a período

**Exemplos de insights COMPLETOS com transparência:**
- "**Crescimento sustentado**: 32% no período **(R\\$ 15.2M → R\\$ 20.0M)**"
- "**Pico em julho**: R\\$ 2.5M, 18% acima da média mensal **(média = R\\$ 2.1M)**"
- "**Amplitude significativa**: Variação de R\\$ 1.2M **(Pico: R\\$ 2.5M em jul/15, Vale: R\\$ 1.3M em fev/15 = +92%)**"
- "**Aceleração no H2**: Segunda metade 25% superior **(H1 média = R\\$ 1.8M vs H2 média = R\\$ 2.25M)**"
"""

    elif tipo_grafico in ["grouped_vertical_bar", "stacked_bar"]:
        prompt += """
### 📊 FOCO PARA COMPARAÇÕES AGRUPADAS:

**⚠️ TRANSPARÊNCIA OBRIGATÓRIA para comparações agrupadas:**
Sempre incluir os valores absolutos que fundamentam cada métrica:

1. **Diferenças entre grupos/períodos** → **Formato: "(Março: R\\$ X, Abril: R\\$ Y, +Z%)"**
2. **Categorias que cresceram/decresceram** → **Formato: "(SC: R\\$ X → R\\$ Y, +Z%)"**
3. **Mudanças estruturais no mix** → **Formato: "(Período 1: A=X%, B=Y%; Período 2: A=W%, B=Z%)"**
4. **Liderança por grupo** → **Formato: "(Março: líder SC = R\\$ X; Abril: líder PR = R\\$ Y)"**

**Exemplos:**
- "**Crescimento assimétrico**: SC cresceu 25% entre março e abril **(R\\$ 2.0M → R\\$ 2.5M)**, enquanto PR manteve estabilidade **(R\\$ 1.8M → R\\$ 1.85M, +2.7%)**"
- "**Mudança de liderança**: Em março SC liderou com R\\$ 2.0M (40% do total); em abril PR assumiu com R\\$ 2.2M (42% do total)"
"""

    prompt += """
---

⚠️ IMPORTANTE:
- Use estas métricas para ENRIQUECER a seção de Insights da sua resposta
- NUNCA gere APENAS insights - SEMPRE inclua os 5 elementos obrigatórios:
  1. ## Título
  2. [Sentença introdutória com filtros em **negrito**]
  3. [Gráfico automático]
  4. ### 💡 Principais Insights ({max_insights} itens baseados nas métricas acima)
  5. ### 🔍 Próximos Passos

O gráfico mostra OS DADOS. Você fornece OS INSIGHTS (dentro da estrutura completa).
""".format(max_insights=max_insights)

    return prompt


def formatar_metricas_para_exibicao(resumo: Dict[str, Any]) -> str:
    """
    Formata resumo numérico para exibição legível (útil para debug).
    
    Args:
        resumo: Dicionário com métricas
    
    Returns:
        String formatada para exibição
    """
    linhas = []
    linhas.append("📊 Resumo Numérico:")
    linhas.append(f"  - Tipo: {resumo.get('tipo_grafico', 'N/A')}")
    linhas.append(f"  - Categorias: {resumo.get('num_categorias', 0)}")
    linhas.append(f"  - Total: {resumo.get('total_geral', 0):,.0f}")
    linhas.append(f"  - Média: {resumo.get('media', 0):,.0f}")

    if 'concentracao_top3_pct' in resumo:
        linhas.append(f"  - Concentração Top 3: {resumo['concentracao_top3_pct']}%")

    if 'gap_1_2_pct' in resumo:
        linhas.append(f"  - Gap 1º vs 2º: {resumo['gap_1_2_pct']}%")

    if 'tendencia' in resumo:
        linhas.append(f"  - Tendência: {resumo['tendencia']}")

    if 'taxa_crescimento_pct' in resumo:
        linhas.append(f"  - Crescimento: {resumo['taxa_crescimento_pct']:+.1f}%")

    return '\n'.join(linhas)

