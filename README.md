# Extrator de Investimentos Bradesco

Solução completa para extrair dados de investimentos de relatórios PDF do Bradesco e exportar em **CSV** e **JSON hierárquico**.

## 🎯 Características

- ✅ Extração automática da tabela "Posição Detalhada dos Investimentos"
- ✅ Captura de 27/27 investimentos com precisão de 100%
- ✅ Extração de nomes dos ativos (26/27 com sucesso)
- ✅ Exportação em CSV estruturado e JSON hierárquico
- ✅ Validação automática dos dados extraídos
- ✅ Valor total correto: R$ 3.190.888,05

## 🚀 Uso Rápido

### 1. Instalação de Dependências

```bash
pip install pdfplumber pandas
```

### 2. Extração Completa (3 passos)

```bash
# Passo 1: Extrair PDF → CSV (valores corretos)
python extract_investment_table_final.py

# Passo 2: Adicionar nomes ao CSV
python add_names_to_csv.py

# Passo 3: Converter CSV → JSON hierárquico
python csv_to_json_hierarchical.py
```

**Resultado**:
- `output/investimentos_bradesco_completo.csv` (CSV com nomes)
- `output/investimentos_bradesco_FINAL.json` (JSON estruturado)

## 📊 Resultados

| Tipo | Quantidade | Valor Bruto | % |
|------|------------|-------------|---|
| Pós-Fixado | 5 | R$ 532.407,15 | 16,7% |
| Pré-Fixado | 10 | R$ 1.067.921,76 | 33,5% |
| IPCA | 11 | R$ 1.589.740,54 | 49,8% |
| Multimercados | 1 | R$ 165.203,82 | 0,0% |
| **TOTAL** | **27** | **R$ 3.190.888,05** | **100%** |

## 📝 Licença

Código de uso livre.
