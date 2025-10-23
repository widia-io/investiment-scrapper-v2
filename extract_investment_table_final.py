#!/usr/bin/env python3
"""
Script final para extrair a tabela "Posição Detalhada dos Investimentos"
do PDF do Bradesco e estruturar em CSV com colunas bem definidas
"""

import pdfplumber
import pandas as pd
import re
from pathlib import Path


def parse_investment_line(line_text, section):
    """
    Parse uma linha de investimento e extrai todos os campos

    Args:
        line_text: Texto completo da linha
        section: Seção (PÓS-FIXADO, PRÉ-FIXADO, etc)

    Returns:
        Dict com os campos extraídos
    """

    # Extrai nome do ativo (primeira parte antes das datas)
    nome_match = re.match(r'^([A-Z][^0-9]+?)(?=\d{2}/\d{2}/)', line_text)
    nome = nome_match.group(1).strip() if nome_match else ''

    # Extrai todas as datas (formato dd/mm/aa ou dd/mm/aaaa)
    dates = re.findall(r'(\d{2}/\d{2}/\d{2,4})', line_text)

    # Extrai todos os valores numéricos (formato brasileiro com vírgula)
    valores = re.findall(r'([\d.]+,\d{2})', line_text)

    # Extrai tipo de indexador
    indexador_match = re.search(r'(CDI|PRE|IPCA)[\s\-]+[\w\s]*?([\d,]+)', line_text)
    indexador = ''
    taxa_emis = ''
    if indexador_match:
        indexador = indexador_match.group(1)
        taxa_emis = indexador_match.group(2) if indexador_match.group(2) else ''

    # Monta o dicionário de dados
    data = {
        'Tipo': section,
        'Nome': nome,
        'Data_Emissao': dates[0] if len(dates) > 0 else '',
        'Data_Aplicacao': dates[1] if len(dates) > 1 else '',
        'Data_Vencimento': dates[2] if len(dates) > 2 else '',
        'Aplicacao_Inicial_R$': valores[0] if len(valores) > 0 else '',
        'TX_Emis': taxa_emis,
        'TX_aa': valores[1] if len(valores) > 1 and indexador else '',
        'Quantidade': valores[2] if len(valores) > 2 else '',
        'Preco_Atual': valores[3] if len(valores) > 3 else '',
        'Valor_Bruto_Atual': valores[4] if len(valores) > 4 else '',
        'Impostos': valores[5] if len(valores) > 5 else '',
        'Aliq_Atual': valores[6] if len(valores) > 6 else '',
        'Valor_Liquido_Atual': valores[7] if len(valores) > 7 else '',
        'Part_Prflo_%': valores[8] if len(valores) > 8 else '',
        'Rent_Mes_%': valores[9] if len(valores) > 9 else '',
        'Rent_Inicio_%': valores[10] if len(valores) > 10 else '',
        'Indexador': indexador,
    }

    return data


def extract_table_from_pdf(pdf_path):
    """
    Extrai a tabela de investimentos do PDF

    Args:
        pdf_path: Caminho para o arquivo PDF

    Returns:
        Lista de dicionários com os dados extraídos
    """

    all_investments = []

    with pdfplumber.open(pdf_path) as pdf:
        # Páginas 6 e 7 (índices 5 e 6) contêm a tabela
        for page_num in [5, 6]:
            page = pdf.pages[page_num]

            print(f"\n=== Processando Página {page_num + 1} ===")

            # Extrai palavras com posições
            words = page.extract_words()

            # Agrupa palavras por linha (mesma coordenada y aproximada)
            lines_dict = {}
            for word in words:
                y = round(word['top'], 1)  # Arredonda para agrupar melhor
                if y not in lines_dict:
                    lines_dict[y] = []
                lines_dict[y].append(word)

            # Ordena linhas por posição vertical
            sorted_lines = sorted(lines_dict.items())

            current_section = None

            for y, words_in_line in sorted_lines:
                # Ordena palavras na linha por posição horizontal
                words_in_line.sort(key=lambda w: w['x0'])

                # Reconstrói a linha
                line_text = ' '.join([w['text'] for w in words_in_line])
                line_text = line_text.strip()

                # Identifica mudança de seção
                if line_text in ['PÓS-FIXADO', 'PRÉ-FIXADO', 'JURO REAL - INFLAÇÃO']:
                    current_section = line_text
                    print(f"\n▶ Seção: {current_section}")
                    continue

                if line_text == 'MULTIMERCADOS':
                    current_section = 'MULTIMERCADOS'
                    print(f"\n▶ Seção: {current_section}")
                    continue

                # Ignora cabeçalhos e linhas vazias
                if not line_text or 'RENDA FIXA' in line_text or 'Data de' in line_text:
                    continue

                # Ignora linhas de total
                if line_text.startswith('Total') or 'ALTERNATIVOS' in line_text:
                    continue

                # Verifica se é uma linha com dados (tem datas ou é fundo)
                has_dates = re.search(r'\d{2}/\d{2}/\d{2}', line_text)
                has_values = re.search(r'[\d.]+,\d{2}', line_text)

                if current_section and (has_dates or (has_values and 'FIC MM' in line_text)):
                    try:
                        investment_data = parse_investment_line(line_text, current_section)

                        # Valida que tem pelo menos alguns campos preenchidos
                        if investment_data['Data_Vencimento'] or investment_data['Valor_Bruto_Atual']:
                            all_investments.append(investment_data)
                            print(f"  ✓ {investment_data['Nome'][:60] if investment_data['Nome'] else line_text[:60]}")
                    except Exception as e:
                        print(f"  ⚠ Erro ao processar linha: {line_text[:60]}")
                        print(f"    Erro: {e}")

    return all_investments


def save_to_csv(investments, output_path):
    """
    Salva os investimentos em CSV

    Args:
        investments: Lista de dicionários com dados dos investimentos
        output_path: Caminho do arquivo CSV de saída
    """

    if not investments:
        print("\n❌ Nenhum investimento foi extraído!")
        return None

    # Cria DataFrame
    df = pd.DataFrame(investments)

    # Reordena colunas
    column_order = [
        'Tipo',
        'Nome',
        'Data_Emissao',
        'Data_Aplicacao',
        'Data_Vencimento',
        'Aplicacao_Inicial_R$',
        'Indexador',
        'TX_Emis',
        'TX_aa',
        'Quantidade',
        'Preco_Atual',
        'Valor_Bruto_Atual',
        'Impostos',
        'Aliq_Atual',
        'Valor_Liquido_Atual',
        'Part_Prflo_%',
        'Rent_Mes_%',
        'Rent_Inicio_%'
    ]

    # Reordena apenas as colunas que existem
    available_columns = [col for col in column_order if col in df.columns]
    df = df[available_columns]

    # Cria diretório se não existir
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Salva CSV
    df.to_csv(output_path, index=False, encoding='utf-8-sig')

    return df


def main():
    """Função principal"""

    pdf_path = 'input/bradesco-ativos.pdf'
    output_csv = 'output/investimentos_bradesco_estruturado.csv'

    print("=" * 80)
    print("EXTRAÇÃO DE INVESTIMENTOS - BRADESCO")
    print("=" * 80)

    # Verifica se o PDF existe
    if not Path(pdf_path).exists():
        print(f"\n❌ ERRO: Arquivo não encontrado: {pdf_path}")
        return

    # Extrai dados
    print("\n📄 Lendo PDF e extraindo dados...")
    investments = extract_table_from_pdf(pdf_path)

    print(f"\n\n📊 Total de investimentos extraídos: {len(investments)}")

    # Salva em CSV
    if investments:
        print(f"\n💾 Salvando dados em CSV...")
        df = save_to_csv(investments, output_csv)

        if df is not None:
            print(f"✓ Arquivo salvo: {output_csv}")
            print(f"✓ Total de registros: {len(df)}")

            # Mostra resumo
            print("\n" + "=" * 80)
            print("RESUMO DOS DADOS EXTRAÍDOS")
            print("=" * 80)

            print(f"\nDistribuição por tipo:")
            print(df['Tipo'].value_counts())

            print(f"\nValor total (Valor Bruto Atual):")
            # Converte valores para numérico
            df_temp = df.copy()
            df_temp['Valor_Bruto_Numerico'] = df_temp['Valor_Bruto_Atual'].str.replace('.', '').str.replace(',', '.').astype(float, errors='ignore')
            total = df_temp['Valor_Bruto_Numerico'].sum()
            print(f"R$ {total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

            print("\n\n📋 Primeiras linhas do CSV:")
            print(df.head(10).to_string(index=False))

            print("\n" + "=" * 80)
            print("✅ EXTRAÇÃO CONCLUÍDA COM SUCESSO!")
            print("=" * 80)

    else:
        print("\n❌ Nenhum dado foi extraído.")


if __name__ == '__main__':
    main()
