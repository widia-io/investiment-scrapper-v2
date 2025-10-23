#!/usr/bin/env python3
"""
Script para extrair a tabela "Posição Detalhada dos Investimentos"
do PDF do Bradesco usando extração de texto
"""

import pdfplumber
import pandas as pd
import re
from pathlib import Path


def extract_investment_data(pdf_path, output_csv):
    """
    Extrai dados de investimentos do PDF

    Args:
        pdf_path: Caminho para o arquivo PDF
        output_csv: Caminho para salvar o CSV
    """

    all_investments = []

    with pdfplumber.open(pdf_path) as pdf:
        # Páginas 6 e 7 (índices 5 e 6) contêm a tabela
        for page_num in [5, 6]:
            page = pdf.pages[page_num]
            text = page.extract_text()

            print(f"\n=== Processando Página {page_num + 1} ===\n")

            # Divide o texto em linhas
            lines = text.split('\n')

            current_section = None
            current_subsection = None

            for i, line in enumerate(lines):
                line = line.strip()

                # Identifica seções principais
                if line in ['PÓS-FIXADO', 'PRÉ-FIXADO', 'JURO REAL - INFLAÇÃO']:
                    current_section = line
                    continue

                if line == 'ALTERNATIVOS':
                    current_section = 'ALTERNATIVOS'
                    continue

                if line == 'MULTIMERCADOS':
                    current_subsection = 'MULTIMERCADOS'
                    continue

                # Pula cabeçalhos e linhas vazias
                if not line or 'RENDA FIXA' in line or 'Data de' in line or 'Total' in line:
                    continue

                # Identifica linhas de investimentos (começam com nome do ativo)
                # Padrão: Nome seguido de datas e valores
                if current_section and re.search(r'\d{2}/\d{2}/\d{2}', line):
                    # Extrai componentes da linha usando regex
                    parts = re.split(r'\s{2,}', line)

                    if len(parts) >= 10:
                        investment = {
                            'Tipo': current_section,
                            'Subtipo': current_subsection,
                            'Nome': parts[0],
                            'Data_Emissao': extract_date(parts, 0),
                            'Data_Aplicacao': extract_date(parts, 1),
                            'Data_Vencimento': extract_date(parts, 2),
                            'Aplicacao_Inicial': extract_value(parts, 3),
                            'TX_Emis': extract_value(parts, 4),
                            'TX_aa': extract_value(parts, 5),
                            'Quantidade': extract_value(parts, 6),
                            'Preco_Atual': extract_value(parts, 7),
                            'Valor_Bruto_Atual': extract_value(parts, 8),
                            'Impostos': extract_value(parts, 9),
                            'Aliq_Atual': extract_value(parts, 10) if len(parts) > 10 else '',
                            'Valor_Liquido_Atual': extract_value(parts, 11) if len(parts) > 11 else '',
                            'Part_Prflo': extract_value(parts, 12) if len(parts) > 12 else '',
                            'Rent_Mes': extract_value(parts, 13) if len(parts) > 13 else '',
                            'Rent_Inicio': extract_value(parts, 14) if len(parts) > 14 else '',
                        }

                        all_investments.append(investment)
                        print(f"✓ Extraído: {investment['Nome'][:50]}")

    print(f"\n\nTotal de investimentos extraídos: {len(all_investments)}")

    if not all_investments:
        print("AVISO: Nenhum investimento foi extraído!")
        print("\nTentando extração alternativa...")
        return extract_with_alternative_method(pdf_path, output_csv)

    # Cria DataFrame
    df = pd.DataFrame(all_investments)

    # Salva em CSV
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(output_csv, index=False, encoding='utf-8-sig')
    print(f"\n✓ Tabela salva em: {output_csv}")
    print(f"\nPrimeiras linhas do CSV:")
    print(df.head())

    return df


def extract_date(parts, offset):
    """Extrai data dos componentes"""
    for i in range(len(parts)):
        if re.match(r'\d{2}/\d{2}/\d{2,4}', parts[i]):
            if offset == 0:
                return parts[i]
            offset -= 1
    return ''


def extract_value(parts, index):
    """Extrai valor numérico de índice específico"""
    if index < len(parts):
        val = parts[index].replace('.', '').replace(',', '.')
        # Remove caracteres não numéricos exceto ponto e hífen
        val = re.sub(r'[^\d.-]', '', val)
        return val
    return ''


def extract_with_alternative_method(pdf_path, output_csv):
    """
    Método alternativo: extrai usando coordenadas e bounding boxes
    """

    all_data = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num in [5, 6]:
            page = pdf.pages[page_num]

            # Extrai palavras com posições
            words = page.extract_words()

            print(f"\n=== Página {page_num + 1} - Método Alternativo ===")
            print(f"Total de palavras: {len(words)}")

            # Agrupa palavras por linha (mesma coordenada y aproximada)
            lines_dict = {}
            for word in words:
                y = round(word['top'])
                if y not in lines_dict:
                    lines_dict[y] = []
                lines_dict[y].append(word)

            # Ordena linhas por posição vertical
            sorted_lines = sorted(lines_dict.items())

            current_row = []
            current_section = None

            for y, words_in_line in sorted_lines:
                # Ordena palavras na linha por posição horizontal
                words_in_line.sort(key=lambda w: w['x0'])

                # Reconstrói a linha
                line_text = ' '.join([w['text'] for w in words_in_line])

                # Identifica seções
                if line_text.strip() in ['PÓS-FIXADO', 'PRÉ-FIXADO', 'JURO REAL - INFLAÇÃO', 'MULTIMERCADOS']:
                    current_section = line_text.strip()
                    continue

                # Ignora cabeçalhos
                if 'RENDA FIXA' in line_text or 'Data de' in line_text or not line_text.strip():
                    continue

                # Verifica se é uma linha com dados (tem datas)
                if re.search(r'\d{2}/\d{2}/\d{2}', line_text):
                    row_data = {
                        'Secao': current_section,
                        'Linha': line_text
                    }

                    # Extrai todas as datas
                    dates = re.findall(r'\d{2}/\d{2}/\d{2,4}', line_text)
                    if len(dates) >= 3:
                        row_data['Data_Emissao'] = dates[0]
                        row_data['Data_Aplicacao'] = dates[1]
                        row_data['Data_Vencimento'] = dates[2]

                    # Extrai valores monetários
                    values = re.findall(r'[\d.]+,\d{2}', line_text)
                    row_data['Valores'] = '|'.join(values)

                    all_data.append(row_data)
                    print(f"✓ {line_text[:80]}")

    print(f"\n\nTotal de linhas extraídas: {len(all_data)}")

    if not all_data:
        print("ERRO: Não foi possível extrair dados com nenhum método.")
        return None

    # Cria DataFrame
    df = pd.DataFrame(all_data)

    # Salva em CSV
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(output_csv, index=False, encoding='utf-8-sig')
    print(f"\n✓ Dados salvos em: {output_csv}")
    print(f"\nPrimeiras linhas:")
    print(df.head(10))

    return df


def main():
    pdf_path = 'input/bradesco-ativos.pdf'
    output_csv = 'output/investimentos_bradesco.csv'

    print("=" * 80)
    print("Extração de Investimentos - Bradesco PDF")
    print("=" * 80)

    if not Path(pdf_path).exists():
        print(f"ERRO: Arquivo não encontrado: {pdf_path}")
        return

    df = extract_investment_data(pdf_path, output_csv)

    if df is not None:
        print("\n" + "=" * 80)
        print("✓ Extração concluída com sucesso!")
        print("=" * 80)


if __name__ == '__main__':
    main()
