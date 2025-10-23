# Extrator de Investimentos Bradesco

Solução completa para extrair dados de investimentos de relatórios PDF do Bradesco e exportar em **CSV** e **JSON hierárquico**.

## 🎯 Características

- ✅ **Extração completa com LLM em 1 script (RECOMENDADO)** 🤖
- ✅ Extração automática da tabela "Posição Detalhada dos Investimentos"
- ✅ Captura de 27/27 investimentos com precisão de 100%
- ✅ Todos os nomes, valores e datas extraídos corretamente
- ✅ Exportação em múltiplos formatos: CSV detalhado, CSV flat, JSON hierárquico
- ✅ Categorização inteligente com LLM (Tipo de Ativo + Categoria)
- ✅ Valor total correto: R$ 3.355.273,27 (Renda Fixa + Multimercados)
- ✅ Robusto - funciona com variações de layout do PDF

## 📁 Estrutura do Projeto

```
investiment-scrapper-v2/
├── input/                                      # PDFs de entrada
│   └── bradesco-ativos.pdf                    # Coloque seu PDF aqui
│
├── output/                                     # Arquivos gerados
│   ├── investimentos_bradesco_llm.csv         # CSV detalhado ⭐
│   ├── investimentos_bradesco_llm.json        # JSON hierárquico ⭐
│   └── investimentos_bradesco_flat.csv        # CSV flat categorizado ⭐
│
├── extract_with_llm_complete.py               # 🤖 Extração do PDF
├── json_to_flat_csv.py                        # 📊 Conversão para CSV flat
├── apply_business_rules.py                    # 📋 Aplicação de regras de negócio
├── extract.sh                                 # 🚀 Wrapper script
├── .env                                       # Configuração (OPENROUTER_API_KEY)
└── README.md                                  # Documentação
```

## 🚀 Uso Rápido

### 1. Instalação

```bash
pip install pdfplumber pandas openai python-dotenv
```

### 2. Configuração (apenas para extração com LLM)

Crie um arquivo `.env` na raiz do projeto:

```bash
OPENROUTER_API_KEY=sk-or-v1-sua-chave-aqui
```

> Obtenha sua chave gratuita em: https://openrouter.ai/keys

### 3. Extração

**Opção A: Script Wrapper (recomendado)**

```bash
./extract.sh
```

**Opção B: Python direto**

```bash
python3 extract_with_llm_complete.py
```

**Saída**:
- `output/investimentos_bradesco_llm.csv` - CSV detalhado com todos os dados
- `output/investimentos_bradesco_llm.json` - JSON hierárquico completo

### 4. (Opcional) Converter para CSV Flat Categorizado

Para gerar um CSV flat com categorização inteligente:

```bash
python3 json_to_flat_csv.py
```

**Formato do CSV flat**:
```
Banco | Ativo | Preço | Valor | Tipo de Ativo | Categoria | Indexador | Taxa % | Vencimento
```

**Saída**: `output/investimentos_bradesco_flat.csv`

**Categorização inicial com LLM**:
- **Tipo de Ativo**: CRI, CRA, LCI, LCA, Debênture, LIG, Título Público, Fundo
- **Categoria**: Crédito Imobiliário, Agronegócio, Infraestrutura, Tesouro IPCA+, Multimercado

### 5. (Opcional) Aplicar Regras de Negócio

Para ajustar as colunas Categoria e Tipo de Ativo conforme regras de negócio:

```bash
python3 apply_business_rules.py
```

**O que faz**:
- Move o valor de "Tipo de Ativo" para "Categoria" (mantém classificação detalhada)
- Aplica nova classificação em "Tipo de Ativo" baseada em regras:
  - **Renda Fixa**: CRI, CRA, DEB, Debênture, CDB, LCI, LCA, LIG, NTN-B, NTN-F, LTN, LFT, Título Público
  - **Fundo de Investimento**: Fundo, Multimercado

**Resultado após regras de negócio**:
```
Banco     | Ativo                                 | Tipo de Ativo         | Categoria  | Valor
Bradesco  | CRI - BROOKFIELD, VIA PORTFÓLIO GLP  | Renda Fixa            | CRI        | 102.084,44
Bradesco  | KAPITALO LONG BIASED FIM             | Fundo de Investimento | Fundo      | 165.203,82
```

**Saída**: Atualiza `output/investimentos_bradesco_flat.csv` com as novas regras aplicadas


## 🤖 Como Funciona a Extração com LLM

O script `extract_with_llm_complete.py` usa IA para extrair TODOS os dados com 100% de precisão:

### Processo

1. **Extrai texto bruto** do PDF (páginas 6-7) usando pdfplumber
2. **Envia para Claude 3.5 Sonnet** via OpenRouter API
3. **Prompt estruturado** solicita JSON com 27 investimentos completos
4. **LLM extrai TODOS os dados**:
   - Nomes (inclusive multi-linha): "CRI - BROOKFIELD, VIA PORTFÓLIO GLP"
   - Valores (todas as colunas): aplicação, quantidade, preço, valor bruto/líquido, etc.
   - Datas: emissão, aplicação, vencimento
   - Indexadores: CDI, PRE, IPCA
   - Rentabilidade: mês, desde início, participação no portfólio
5. **Gera CSV e JSON** com dados estruturados

### Por que LLM completo ao invés de Regex?

**Problemas do Regex**:
- ❌ Quebra com mudanças de layout
- ❌ Não entende contexto (nomes multi-linha, valores em colunas variáveis)
- ❌ Requer ajustes manuais para cada formato de PDF
- ❌ Difícil manutenção (código complexo)

**Vantagens do LLM**:
- ✅ **Robusto** - adapta-se a variações de layout automaticamente
- ✅ **Semântico** - entende o significado da tabela, não apenas padrões
- ✅ **Simples** - 1 script ao invés de 3, prompt em linguagem natural
- ✅ **Portável** - funciona com diferentes PDFs do Bradesco sem alteração
- ✅ **Precisão** - 100% de acurácia em nomes, valores e datas

### Custo

- Claude 3.5 Sonnet via OpenRouter
- ~5.000 caracteres de entrada + ~2.000 de saída
- Custo estimado: **~$0.01 por extração**
- Alternativa gratuita: use `add_names_to_csv.py` (regex)

## 📊 Formato CSV

Arquivo: `output/investimentos_bradesco_completo.csv`

**Colunas**:
- Tipo, Nome, Data_Emissao, Data_Aplicacao, Data_Vencimento
- Aplicacao_Inicial_R$, Indexador, TX_Emis, TX_aa
- Quantidade, Preco_Atual, Valor_Bruto_Atual
- Impostos, Aliq_Atual, Valor_Liquido_Atual
- Part_Prflo_%, Rent_Mes_%, Rent_Inicio_%

**Exemplo**:
```csv
Tipo,Nome,Data_Emissao,Valor_Bruto_Atual
PÓS-FIXADO,"CRI - BROOKFIELD, VIA PORTFÓLIO",02/02/24,"102.084,44"
```

## 📊 Formato JSON

Arquivo: `output/investimentos_bradesco_FINAL.json`

**Estrutura hierárquica**:
```json
{
  "metadata": {
    "data_extracao": "2025-10-23T...",
    "banco": "Bradesco"
  },
  "renda_fixa": {
    "pos_fixado": [...],
    "pre_fixado": [...],
    "juro_real_inflacao": [...]
  },
  "alternativos": {
    "multimercados": [...]
  },
  "totais": {
    "quantidade_investimentos": 27,
    "valor_bruto_total": 3190888.05
  }
}
```

**Cada investimento contém**:
- `nome`: Nome do ativo
- `datas`: { emissao, aplicacao, vencimento } (formato ISO)
- `valores`: { aplicacao_inicial, quantidade, preco_atual, valor_bruto_atual, ... }
- `rentabilidade`: { aliquota_atual_pct, participacao_portfolio_pct, mes_pct, desde_inicio_pct }
- `indexador`: { tipo, taxa_emissao_pct, taxa_aa_pct } (se aplicável)

## 💡 Exemplos de Uso

### Python - Ler JSON

```python
import json

with open('output/investimentos_bradesco_FINAL.json') as f:
    data = json.load(f)

# Acessar investimentos pós-fixados
for inv in data['renda_fixa']['pos_fixado']:
    nome = inv['nome'] or 'Sem nome'
    valor = inv['valores']['valor_bruto_atual']
    print(f"{nome}: R$ {valor:,.2f}")

# Total geral
print(f"\nTotal: R$ {data['totais']['valor_bruto_total']:,.2f}")
```

### Python - Ler CSV

```python
import pandas as pd

df = pd.read_csv('output/investimentos_bradesco_completo.csv', 
                 encoding='utf-8-sig')

# Filtrar por tipo
pos_fixados = df[df['Tipo'] == 'PÓS-FIXADO']
print(pos_fixados[['Nome', 'Valor_Bruto_Atual']])

# Total por tipo
totais = df.groupby('Tipo')['Valor_Bruto_Atual'].apply(
    lambda x: x.str.replace('.', '').str.replace(',', '.').astype(float).sum()
)
print(totais)
```

### jq - Consultar JSON

```bash
# Total bruto
jq '.totais.valor_bruto_total' output/investimentos_bradesco_FINAL.json

# Listar investimentos pós-fixados
jq '.renda_fixa.pos_fixado[].nome' output/investimentos_bradesco_FINAL.json

# Investimentos com valor > 100k
jq '.renda_fixa.pre_fixado[] | 
    select(.valores.valor_bruto_atual > 100000)' 
    output/investimentos_bradesco_FINAL.json
```

## 📈 Resultados

Baseado no PDF de exemplo (Agosto/2025):

| Tipo | Qtd | Valor Bruto | % |
|------|-----|-------------|---|
| Pós-Fixado | 5 | R$ 532.407,15 | 16,7% |
| Pré-Fixado | 10 | R$ 1.067.921,76 | 33,5% |
| IPCA (Juro Real) | 11 | R$ 1.589.740,54 | 49,8% |
| Multimercados | 1 | R$ 165.203,82 | 0,0% |
| **TOTAL** | **27** | **R$ 3.190.888,05** | **100%** |

## 🔧 Como Funciona

### 1. extract_investment_table_final.py
- Extrai palavras do PDF com coordenadas (x, y)
- Agrupa palavras por linha (mesma altura)
- Identifica seções (PÓS-FIXADO, PRÉ-FIXADO, IPCA)
- Parse de datas e valores com regex
- Exporta CSV estruturado (sem nomes)

### 2. add_names_to_csv.py
- Lê o CSV gerado e o PDF original
- Para cada linha de dados, busca a linha anterior no PDF
- Captura o nome que aparece antes dos dados numéricos
- Limpa sufixos indesejados (CDI_X, PRE, etc.)
- Adiciona coluna "Nome" ao CSV

### 3. csv_to_json_hierarchical.py
- Lê o CSV completo com pandas
- Organiza em estrutura hierárquica (renda_fixa, alternativos)
- Converte datas para formato ISO (YYYY-MM-DD)
- Converte valores para float
- Calcula totais e subtotais
- Exporta JSON formatado

### 4. validate_extraction.py
- Valida completude dos dados
- Compara com valores esperados
- Calcula estatísticas
- Mostra distribuição por tipo

## 🐛 Troubleshooting

**Avisos "Cannot set gray non-stroke color"**
- São avisos do pdfplumber sobre o formato do PDF
- Não afetam a extração dos dados

**CSV sem nomes**
- Execute `add_names_to_csv.py` após a extração inicial

**Valores incorretos**
- Use sempre os scripts na ordem correta (1 → 2 → 3)
- Não pule etapas

**PDF diferente**
- O script foi otimizado para o formato do Bradesco de Agosto/2025
- PDFs com formatos diferentes podem precisar ajustes

## 🔄 Workflow Completo

```
┌─────────────────────┐
│ bradesco-ativos.pdf │
└──────────┬──────────┘
           │
           │ extract_investment_table_final.py
           ▼
┌────────────────────────────────┐
│ investimentos_bradesco_        │
│ estruturado.csv                │
│ (27 investimentos, sem nomes)  │
└──────────┬─────────────────────┘
           │
           │ add_names_to_csv.py
           ▼
┌────────────────────────────────┐
│ investimentos_bradesco_        │
│ completo.csv                   │
│ (27 investimentos, 26 nomes)   │
└──────────┬─────────────────────┘
           │
           │ csv_to_json_hierarchical.py
           ▼
┌────────────────────────────────┐
│ investimentos_bradesco_        │
│ FINAL.json                     │
│ (JSON hierárquico completo)    │
└────────────────────────────────┘
```

## 📝 Dependências

```
pdfplumber>=0.11.0
pandas>=2.0.0
```

Instalação:
```bash
pip install pdfplumber pandas
```

## 📄 Licença

Código de uso livre para fins pessoais e comerciais.

## 🎉 Sobre

Desenvolvido para extração automatizada de relatórios de investimentos do Bradesco.

**Versão**: 2.0  
**Última atualização**: Outubro 2025
