#!/usr/bin/env python3
"""
Adiciona nomes ao CSV correto extraindo do PDF
"""

import pandas as pd
import pdfplumber
import re
from pathlib import Path


def extract_names_from_pdf(pdf_path):
    """Extrai apenas os nomes dos investimentos mantendo a ordem"""

    names = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num in [5, 6]:
            page = pdf.pages[page_num]
            words = page.extract_words()

            lines_dict = {}
            for word in words:
                y = round(word['top'], 1)
                if y not in lines_dict:
                    lines_dict[y] = []
                lines_dict[y].append(word)

            sorted_lines = sorted(lines_dict.items())

            current_section = None
            lines_list = [(y, ' '.join([w['text'] for w in sorted(words_in_line, key=lambda w: w['x0'])]).strip())
                         for y, words_in_line in sorted_lines]

            i = 0
            while i < len(lines_list):
                y, line_text = lines_list[i]

                # Identifica seções
                if line_text in ['PÓS-FIXADO', 'PRÉ-FIXADO', 'JURO REAL - INFLAÇÃO', 'MULTIMERCADOS']:
                    current_section = line_text
                    i += 1
                    continue

                # Ignora linhas irrelevantes
                if not line_text or 'RENDA FIXA' in line_text or 'Data de' in line_text or line_text.startswith('Total') or line_text == 'ALTERNATIVOS' or 'Página' in line_text:
                    i += 1
                    continue

                # Linha com dados (tem data dd/mm/aa)
                if current_section and re.search(r'\d{2}/\d{2}/\d{2}', line_text):
                    # Tenta extrair nome da mesma linha primeiro
                    nome_match = re.match(r'^(.+?)\s+\d{2}/\d{2}/\d{2}', line_text)

                    if nome_match:
                        # Nome está na mesma linha
                        nome = nome_match.group(1).strip()
                    else:
                        # Nome está em linhas anteriores
                        nome_parts = []

                        # Olha linha anterior
                        if i > 0:
                            prev_line = lines_list[i-1][1]
                            if prev_line and prev_line not in ['PÓS-FIXADO', 'PRÉ-FIXADO', 'JURO REAL - INFLAÇÃO', 'MULTIMERCADOS', 'Total', 'ALTERNATIVOS', 'RENDA FIXA'] and 'Data de' not in prev_line and 'Página' not in prev_line:
                                # Limpa indexadores
                                prev_line_clean = re.sub(r'\s+(CDI|PRE|IPCA)[\s_\d\-]*$', '', prev_line).strip()
                                nome_parts.append(prev_line_clean)

                        # Olha linha seguinte (alguns nomes continuam após os dados)
                        if i + 1 < len(lines_list):
                            next_line = lines_list[i+1][1]
                            # Linha seguinte tem continuação do nome se NÃO for uma linha de dados nem cabeçalho
                            if next_line and not re.search(r'\d{2}/\d{2}/\d{2}', next_line) and next_line not in ['PÓS-FIXADO', 'PRÉ-FIXADO', 'JURO REAL - INFLAÇÃO', 'MULTIMERCADOS', 'Total', 'ALTERNATIVOS'] and 'Data de' not in next_line and 'Página' not in next_line:
                                # Extrai apenas texto antes de números (ex: "GLP 100.00" -> "GLP")
                                next_clean = re.sub(r'\s+[\d\.,]+$', '', next_line).strip()
                                if next_clean and not next_clean.replace('.', '').replace(',', '').isdigit():
                                    nome_parts.append(next_clean)

                        nome = ' '.join(nome_parts) if nome_parts else None

                    names.append(nome)

                i += 1

    return names


def main():
    pdf_path = 'input/bradesco-ativos.pdf'
    csv_correto = 'output/investimentos_bradesco_estruturado.csv'
    output_csv = 'output/investimentos_bradesco_completo.csv'

    print("=" * 80)
    print("ADICIONANDO NOMES AO CSV CORRETO")
    print("=" * 80)

    # Lê CSV correto
    print(f"\n📄 Lendo CSV correto...")
    df = pd.read_csv(csv_correto, encoding='utf-8-sig')
    print(f"✓ {len(df)} registros")

    # Extrai nomes do PDF
    print(f"\n📄 Extraindo nomes do PDF...")
    names = extract_names_from_pdf(pdf_path)
    print(f"✓ {len(names)} nomes extraídos")

    # Adiciona nomes
    if len(names) == len(df):
        df['Nome'] = names
        print("✓ Nomes adicionados com sucesso!")
    else:
        print(f"⚠️  Quantidade diferente: {len(names)} nomes vs {len(df)} registros")
        # Adiciona o que der, preenchendo com None o resto
        for i in range(len(df)):
            df.at[i, 'Nome'] = names[i] if i < len(names) else None

    # Reordena colunas para Nome ficar logo após Tipo
    cols = list(df.columns)
    if 'Nome' in cols:
        cols.remove('Nome')
    cols.insert(1, 'Nome')
    df = df[cols]

    # Salva
    output_path = Path(output_csv)
    df.to_csv(output_path, index=False, encoding='utf-8-sig')

    print(f"\n✓ CSV salvo: {output_path}")

    # Mostra resumo
    print("\n" + "=" * 80)
    print("RESUMO")
    print("=" * 80)

    print(f"\nInvestimentos com nome: {df['Nome'].notna().sum()}/{len(df)}")

    print(f"\n📋 Primeiros 5 registros:")
    print(df[['Tipo', 'Nome', 'Valor_Bruto_Atual']].head(5).to_string(index=False))

    print("\n" + "=" * 80)
    print("✅ CONCLUÍDO!")
    print("=" * 80)


if __name__ == '__main__':
    main()
