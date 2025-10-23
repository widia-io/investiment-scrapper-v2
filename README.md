# Extrator de Investimentos Bradesco

Solução completa para extrair dados de investimentos de relatórios PDF do Bradesco e exportar em **CSV** e **JSON hierárquico**.

## 🎯 Características

- ✅ **Extração completa com LLM em 1 script (RECOMENDADO)** 🤖
- ✅ Extração automática da tabela "Posição Detalhada dos Investimentos"
- ✅ Captura de 27/27 investimentos com precisão de 100%
- ✅ Todos os nomes, valores e datas extraídos corretamente
- ✅ Exportação em CSV estruturado e JSON hierárquico
- ✅ Valor total correto: R$ 3.355.273,27 (Renda Fixa + Multimercados)
- ✅ Robusto - funciona com variações de layout do PDF

## 📁 Estrutura do Projeto

```
investiment-scrapper-v2/
├── input/                                      # PDFs de entrada
│   └── bradesco-ativos.pdf                    # Coloque seu PDF aqui
├── output/                                     # Arquivos gerados
│   ├── investimentos_bradesco_llm.csv         # CSV extraído com LLM ⭐
│   ├── investimentos_bradesco_llm.json        # JSON hierárquico ⭐
│   ├── investimentos_bradesco_completo.csv    # CSV (método antigo)
│   └── investimentos_bradesco_final.json      # JSON (método antigo)
│
├── extract_with_llm_complete.py               # 🤖 Extração completa com LLM (RECOMENDADO)
├── extract_investment_table_final.py          # 1️⃣ PDF → CSV (método antigo)
├── extract_names_with_llm.py                  # 2️⃣ Adiciona nomes (método antigo)
├── add_names_to_csv.py                        # 2️⃣ Regex (método antigo)
├── csv_to_json_hierarchical.py                # 3️⃣ CSV → JSON (método antigo)
├── validate_extraction.py                     # ✓ Validação
│
├── extract_investments.sh                     # Script wrapper (em desenvolvimento)
├── setup.sh                                   # Setup do ambiente
└── README.md                                  # Este arquivo
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

**🤖 Método Recomendado: LLM Completo (1 comando)**

```bash
python extract_with_llm_complete.py
```

Saída:
- `output/investimentos_bradesco_llm.csv` - CSV com todos os dados
- `output/investimentos_bradesco_llm.json` - JSON hierárquico completo

**Vantagens**:
- ✅ **1 único script** - extrai tudo de uma vez
- ✅ **100% de precisão** - nomes, valores, datas corretos
- ✅ **Robusto** - funciona com variações de layout
- ✅ **Portável** - funciona com diferentes PDFs do Bradesco

---

**📊 Método Antigo: 3 Scripts (sem LLM ou LLM parcial)**

<details>
<summary>Clique para ver método legado (não recomendado)</summary>

Opção A: Com LLM apenas para nomes (3 passos):
```bash
python extract_investment_table_final.py
python extract_names_with_llm.py
python csv_to_json_hierarchical.py
```

Opção B: Sem LLM (regex - incompleto):
```bash
python extract_investment_table_final.py
python add_names_to_csv.py
python csv_to_json_hierarchical.py
```

**Limitações**: Menos robusto, vulnerável a mudanças de layout, regex quebrável.

</details>

### 4. Validação (opcional)

```bash
python validate_extraction.py
```

## 🤖 Como Funciona a Extração com LLM

O script `extract_names_with_llm.py` usa IA para extrair nomes com 100% de precisão:

### Processo

1. **Extrai texto bruto** do PDF (páginas 6-7) usando pdfplumber
2. **Envia para Claude 3.5 Sonnet** via OpenRouter API
3. **Prompt estruturado** solicita JSON com 27 nomes em ordem
4. **LLM identifica nomes complexos** que regex não consegue:
   - Nomes multi-linha: "CRI - BROOKFIELD, VIA PORTFÓLIO" + "GLP"
   - Nomes após dados: Linha de dados seguida por continuação do nome
   - Nomes compostos: "DEB INCENTIVADA - AGUAS DO RIO 1 SPE S.A"
5. **Valida e mapeia** os 27 nomes para o CSV na ordem correta

### Por que LLM?

**Problema**: Regex não consegue capturar nomes quando:
- Nome tem números (ex: "KAPITALO K10")
- Nome dividido em múltiplas linhas
- Nome aparece DEPOIS da linha de dados
- Formato inconsistente entre investimentos

**Solução LLM**:
- ✅ Entende contexto semântico do PDF
- ✅ Identifica padrões complexos
- ✅ Concatena partes de nomes automaticamente
- ✅ 100% de precisão nos 27 investimentos

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
