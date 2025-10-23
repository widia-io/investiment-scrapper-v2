# Extrator de Investimentos Bradesco

Script Python para extrair a tabela "Posição Detalhada dos Investimentos" de relatórios PDF do Bradesco e exportar para CSV estruturado.

## 📋 Descrição

Este script extrai automaticamente os dados de investimentos do relatório PDF do Bradesco, identificando:
- Títulos de Renda Fixa (Pós-fixado, Pré-fixado, IPCA)
- Fundos Multimercados
- Todas as informações relevantes (datas, valores, taxas, rentabilidade)

## 🚀 Como Usar

### 1. Instalação de Dependências

```bash
pip install pdfplumber pandas
```

### 2. Estrutura de Diretórios

```
investiment-scrapper-v2/
├── input/
│   └── bradesco-ativos.pdf          # Coloque seu PDF aqui
├── output/
│   └── investimentos_bradesco_estruturado.csv  # Será gerado aqui
└── extract_investment_table_final.py
```

### 3. Executar o Script

```bash
python extract_investment_table_final.py
```

## 📊 Dados Extraídos

O CSV gerado contém as seguintes colunas:

| Coluna | Descrição |
|--------|-----------|
| `Tipo` | Tipo de investimento (PÓS-FIXADO, PRÉ-FIXADO, JURO REAL - INFLAÇÃO, MULTIMERCADOS) |
| `Nome` | Nome do ativo/fundo |
| `Data_Emissao` | Data de emissão |
| `Data_Aplicacao` | Data da aplicação |
| `Data_Vencimento` | Data de vencimento |
| `Aplicacao_Inicial_R$` | Valor da aplicação inicial |
| `Indexador` | Indexador (CDI, PRE, IPCA) |
| `TX_Emis` | Taxa de emissão |
| `TX_aa` | Taxa ao ano |
| `Quantidade` | Quantidade |
| `Preco_Atual` | Preço atual |
| `Valor_Bruto_Atual` | Valor bruto atual |
| `Impostos` | Impostos |
| `Aliq_Atual` | Alíquota atual |
| `Valor_Liquido_Atual` | Valor líquido atual |
| `Part_Prflo_%` | Participação no portfólio (%) |
| `Rent_Mes_%` | Rentabilidade do mês (%) |
| `Rent_Inicio_%` | Rentabilidade desde o início (%) |

## 📈 Exemplo de Saída

```
Tipo,Nome,Data_Emissao,Data_Aplicacao,Data_Vencimento,Aplicacao_Inicial_R$,...
PÓS-FIXADO,LCA - BANCO BRADESCO S.A.,17/04/25,17/04/25,01/04/29,80.000,00,...
PRÉ-FIXADO,CRI - ALLOS S.A.,17/04/24,17/04/24,15/04/31,100.000,00,...
JURO REAL - INFLAÇÃO,CRA - JBS S.A.,05/10/23,05/10/23,16/09/30,100.000,00,...
```

## 🔍 Resumo da Extração

O script mostra um resumo ao final:

```
📊 Total de investimentos extraídos: 27

Distribuição por tipo:
JURO REAL - INFLAÇÃO    11
PRÉ-FIXADO              10
PÓS-FIXADO               5
MULTIMERCADOS            1

Valor total (Valor Bruto Atual):
R$ 3.190.888,05
```

## ⚙️ Funcionamento Técnico

1. **Leitura do PDF**: Usa `pdfplumber` para extrair texto com coordenadas
2. **Agrupamento por Linhas**: Agrupa palavras que estão na mesma altura (linha)
3. **Identificação de Seções**: Detecta mudanças de seção (PÓS-FIXADO, PRÉ-FIXADO, etc.)
4. **Parsing de Dados**: Extrai datas, valores e informações usando regex
5. **Estruturação**: Organiza dados em formato tabular
6. **Exportação**: Salva em CSV com encoding UTF-8 com BOM

## 🐛 Troubleshooting

### Avisos de "Cannot set gray non-stroke color"
São avisos do pdfplumber relacionados ao formato do PDF. Não afetam a extração dos dados.

### Nenhum investimento extraído
Verifique se:
- O PDF está na pasta `input/`
- O PDF segue o formato padrão do Bradesco
- As páginas 6 e 7 contêm a tabela "Posição Detalhada dos Investimentos"

### Dados incompletos
Algumas linhas podem ter campos vazios se o PDF não contém todas as informações ou se o formato difere do esperado.

## 📝 Notas

- O script foi testado com relatórios do Bradesco de Agosto/2025
- Extrai apenas as páginas 6 e 7 onde está a tabela detalhada
- Valores monetários mantêm formato brasileiro (vírgula decimal)
- Encoding UTF-8 com BOM para compatibilidade com Excel

## 🔄 Versões Anteriores

- `extract_investment_table.py` - Primeira versão usando tabelas
- `extract_investment_table_v2.py` - Versão com extração alternativa
- `extract_investment_table_final.py` - **Versão recomendada** (atual)

## 📄 Licença

Código de uso livre para fins pessoais e comerciais.
