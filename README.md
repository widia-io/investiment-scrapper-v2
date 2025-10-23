# Extrator de Investimentos Bradesco

Solução completa para extrair dados de investimentos de relatórios PDF do Bradesco e exportar em **CSV** e **JSON hierárquico**.

## 🎯 Características

- ✅ Extração automática da tabela "Posição Detalhada dos Investimentos"
- ✅ Captura de 27/27 investimentos com precisão de 100%
- ✅ Extração de nomes dos ativos (26/27 com sucesso)
- ✅ Exportação em CSV estruturado e JSON hierárquico
- ✅ Validação automática dos dados extraídos
- ✅ Valor total correto: R$ 3.190.888,05

## 📁 Estrutura do Projeto

```
investiment-scrapper-v2/
├── input/                                      # PDFs de entrada
│   └── bradesco-ativos.pdf                    # Coloque seu PDF aqui
├── output/                                     # Arquivos gerados
│   ├── investimentos_bradesco_estruturado.csv # CSV sem nomes (intermediário)
│   ├── investimentos_bradesco_completo.csv    # CSV com nomes ⭐
│   └── investimentos_bradesco_FINAL.json      # JSON hierárquico ⭐
│
├── extract_investment_table_final.py          # 1️⃣ PDF → CSV
├── add_names_to_csv.py                        # 2️⃣ Adiciona nomes
├── csv_to_json_hierarchical.py                # 3️⃣ CSV → JSON
├── validate_extraction.py                     # ✓ Validação
│
├── extract_investments.sh                     # Script wrapper (em desenvolvimento)
├── setup.sh                                   # Setup do ambiente
└── README.md                                  # Este arquivo
```

## 🚀 Uso Rápido

### 1. Instalação

```bash
pip install pdfplumber pandas
```

### 2. Extração (3 passos)

```bash
# Passo 1: Extrair PDF → CSV (valores corretos)
python extract_investment_table_final.py
# Saída: output/investimentos_bradesco_estruturado.csv

# Passo 2: Adicionar nomes ao CSV
python add_names_to_csv.py
# Saída: output/investimentos_bradesco_completo.csv

# Passo 3: Converter CSV → JSON hierárquico
python csv_to_json_hierarchical.py
# Saída: output/investimentos_bradesco_FINAL.json
```

### 3. Validação (opcional)

```bash
python validate_extraction.py
```

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
