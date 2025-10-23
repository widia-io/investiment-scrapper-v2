#!/usr/bin/env python3
"""
Script para extrair a tabela "Posição Detalhada dos Investimentos"
do PDF do Bradesco e salvar em CSV
"""

import pdfplumber
import pandas as pd
import re
from pathlib import Path


def clean_value(value):
    """Limpa valores monetários e numéricos"""
    if value is None or value == '':
        return ''

    # Remove espaços extras
    value = str(value).strip()

    # Se for um número com vírgula decimal brasileira
    if re.match(r'^[\d.]+,\d+$', value):
        value = value.replace('.', '').replace(',', '.')

    return value


def extract_investment_table(pdf_path, output_csv):
    """
    Extrai a tabela de investimentos do PDF

    Args:
        pdf_path: Caminho para o arquivo PDF
        output_csv: Caminho para salvar o CSV
    """

    # Colunas esperadas da tabela
    expected_columns = [
        'RENDA FIXA',
        'Data de Emissão',
        'Data da Aplicação',
        'Data de Vencimento',
        'Aplicação Inicial R$',
        'TX % Emis.',
        'TX % a.a.',
        'Quantidade',
        'Preço Atual',
        'Valor Bruto Atual',
        'Impostos',
        'Aliq. Atual',
        'Valor Líquido Atual',
        'Part % Prflo',
        'Rentabilidade Mês',
        'Rentabilidade Início'
    ]

    all_rows = []

    with pdfplumber.open(pdf_path) as pdf:
        # A tabela está nas páginas 6 e 7 (índices 5 e 6)
        for page_num in [5, 6]:
            page = pdf.pages[page_num]

            # Configurações para extração de tabela
            table_settings = {
                "vertical_strategy": "lines",
                "horizontal_strategy": "lines",
                "intersection_tolerance": 5,
            }

            # Extrai todas as tabelas da página
            tables = page.extract_tables(table_settings)

            print(f"\n=== Página {page_num + 1} ===")
            print(f"Número de tabelas encontradas: {len(tables)}")

            for table_idx, table in enumerate(tables):
                if not table:
                    continue

                print(f"\nTabela {table_idx + 1}:")
                print(f"Número de linhas: {len(table)}")

                # Processa cada linha da tabela
                for row_idx, row in enumerate(table):
                    # Ignora linhas vazias
                    if not any(row):
                        continue

                    # Limpa valores
                    cleaned_row = [clean_value(cell) for cell in row]

                    # Debug: imprime as primeiras linhas
                    if row_idx < 5:
                        print(f"Linha {row_idx}: {cleaned_row[:5]}")

                    # Pula cabeçalhos
                    first_cell = cleaned_row[0] if cleaned_row else ''

                    # Identifica seções
                    if any(keyword in first_cell.upper() for keyword in
                           ['RENDA FIXA', 'PÓS-FIXADO', 'PRÉ-FIXADO',
                            'JURO REAL', 'INFLAÇÃO', 'ALTERNATIVOS',
                            'MULTIMERCADOS', 'DATA DE']):
                        # Se for cabeçalho de seção, adiciona mas marca como seção
                        if 'DATA DE' not in first_cell.upper():
                            all_rows.append(['SEÇÃO'] + cleaned_row)
                        continue

                    # Ignora linhas de total
                    if 'TOTAL' in first_cell.upper():
                        continue

                    # Adiciona linhas de dados
                    if len(cleaned_row) > 5:  # Garante que tem dados suficientes
                        all_rows.append(cleaned_row)

    print(f"\n\nTotal de linhas extraídas: {len(all_rows)}")

    # Cria DataFrame
    if not all_rows:
        print("Nenhuma linha foi extraída!")
        return

    # Encontra o número máximo de colunas
    max_cols = max(len(row) for row in all_rows)
    print(f"Número máximo de colunas: {max_cols}")

    # Padroniza o número de colunas
    normalized_rows = []
    for row in all_rows:
        if len(row) < max_cols:
            row.extend([''] * (max_cols - len(row)))
        normalized_rows.append(row[:max_cols])

    # Cria DataFrame
    df = pd.DataFrame(normalized_rows)

    # Define nomes das colunas baseado no esperado
    if len(df.columns) >= len(expected_columns):
        df.columns = expected_columns + [f'Extra_{i}' for i in range(len(df.columns) - len(expected_columns))]
    else:
        df.columns = [f'Col_{i}' for i in range(len(df.columns))]

    # Remove linhas completamente vazias
    df = df.dropna(how='all')

    # Salva em CSV
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(output_csv, index=False, encoding='utf-8-sig')
    print(f"\n✓ Tabela extraída e salva em: {output_csv}")
    print(f"✓ Total de registros: {len(df)}")
    print(f"\nPrimeiras linhas:")
    print(df.head(10))

    return df


def main():
    # Caminhos dos arquivos
    pdf_path = 'input/bradesco-ativos.pdf'
    output_csv = 'output/investimentos_bradesco.csv'

    print("=" * 80)
    print("Extração de Tabela de Investimentos - Bradesco")
    print("=" * 80)

    # Verifica se o PDF existe
    if not Path(pdf_path).exists():
        print(f"ERRO: Arquivo não encontrado: {pdf_path}")
        return

    # Extrai a tabela
    df = extract_investment_table(pdf_path, output_csv)

    if df is not None:
        print("\n" + "=" * 80)
        print("Extração concluída com sucesso!")
        print("=" * 80)


if __name__ == '__main__':
    main()
