#!/usr/bin/env python3
"""
Script final para extrair investimentos com NOMES corretos
Captura o nome que aparece na linha anterior aos dados numéricos
"""

import pdfplumber
import pandas as pd
import re
from pathlib import Path


def extract_table_from_pdf(pdf_path):
    """Extrai investimentos do PDF capturando nomes corretamente"""

    all_investments = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num in [5, 6]:  # Páginas 6 e 7
            page = pdf.pages[page_num]

            print(f"\n=== Página {page_num + 1} ===")

            # Extrai palavras com posições
            words = page.extract_words()

            # Agrupa por linha
            lines_dict = {}
            for word in words:
                y = round(word['top'], 1)
                if y not in lines_dict:
                    lines_dict[y] = []
                lines_dict[y].append(word)

            # Ordena linhas
            sorted_lines = sorted(lines_dict.items())

            current_section = None
            previous_line_text = None

            for y, words_in_line in sorted_lines:
                words_in_line.sort(key=lambda w: w['x0'])
                line_text = ' '.join([w['text'] for w in words_in_line]).strip()

                # Identifica mudança de seção
                if line_text in ['PÓS-FIXADO', 'PRÉ-FIXADO', 'JURO REAL - INFLAÇÃO', 'MULTIMERCADOS']:
                    current_section = line_text
                    previous_line_text = None
                    print(f"\n▶ {line_text}")
                    continue

                # Ignora headers e linhas vazias
                if not line_text or 'RENDA FIXA' in line_text or 'Data de' in line_text:
                    previous_line_text = None
                    continue

                # Ignora totais
                if line_text.startswith('Total') or line_text == 'ALTERNATIVOS':
                    previous_line_text = None
                    continue

                # Processa linha de dados (tem datas)
                if current_section and re.search(r'\d{2}/\d{2}/\d{2}', line_text):
                    # Tenta extrair nome da própria linha primeiro
                    nome_match = re.match(r'^([A-Z][^\d]+?)(?=\d{2}/\d{2}/)', line_text)

                    if nome_match:
                        # Nome está na mesma linha
                        nome = nome_match.group(1).strip()
                    elif previous_line_text:
                        # Nome estava na linha anterior
                        # Remove espaços e verifica se não é uma palavra-chave
                        if previous_line_text not in ['Total', 'ALTERNATIVOS']:
                            # Limpa nome removendo indexadores e códigos que podem ter ficado
                            nome = previous_line_text
                            # Remove CDI_X, PRE, IPCA etc do final
                            nome = re.sub(r'\s+(CDI|PRE|IPCA)[\s_\d\-]*$', '', nome).strip()
                        else:
                            nome = None
                    else:
                        nome = None

                    # Parse da linha
                    investment = parse_line_data(line_text, current_section, nome)

                    if investment:
                        all_investments.append(investment)
                        display_name = nome if nome else line_text[:50]
                        print(f"  ✓ {display_name}")

                    previous_line_text = None  # Reset após processar dados
                else:
                    # Linha sem datas - pode ser um nome
                    # Guarda para próxima iteração
                    if line_text and line_text not in ['Total', 'ALTERNATIVOS']:
                        previous_line_text = line_text

    return all_investments


def parse_line_data(line_text, section, nome):
    """Parse completo de uma linha com dados"""

    # Extrai datas
    dates = re.findall(r'\d{2}/\d{2}/\d{2,4}', line_text)

    # Extrai valores
    valores = re.findall(r'[\d.]+,\d{2}', line_text)

    # Identifica indexador
    indexador = None
    tx_emis = None
    tx_aa = None

    if 'CDI' in line_text:
        indexador = 'CDI'
        match = re.search(r'CDI\s*-\s*([\d,]+)', line_text)
        if match:
            tx_emis = match.group(1)
            tx_aa = '0,00'  # CDI geralmente tem taxa aa separada
    elif 'PRE' in line_text:
        indexador = 'PRE'
        match = re.search(r'PRE\s+([\d,]+)', line_text)
        if match:
            tx_emis = match.group(1)
            tx_aa = tx_emis
    elif 'IPCA' in line_text:
        if 'M D' in line_text or 'M  D' in line_text:
            indexador = 'IPCA_MD'
        else:
            indexador = 'IPCA'
        match = re.search(r'IPCA(?:\s+M\s+D)?\s+([\d,]+)', line_text)
        if match:
            tx_emis = match.group(1)
            tx_aa = tx_emis

    # Se não tem 3 datas, pode ser fundo
    if len(dates) < 3:
        # Fundo
        return {
            'Tipo': section,
            'Nome': nome,
            'Data_Emissao': None,
            'Data_Aplicacao': dates[0] if len(dates) > 0 else None,
            'Data_Vencimento': None,
            'Aplicacao_Inicial_R$': valores[0] if len(valores) > 0 else None,
            'Indexador': indexador,
            'TX_Emis': tx_emis,
            'TX_aa': tx_aa,
            'Quantidade': valores[1] if len(valores) > 1 else None,
            'Preco_Atual': valores[2] if len(valores) > 2 else None,
            'Valor_Bruto_Atual': valores[3] if len(valores) > 3 else None,
            'Impostos': valores[4] if len(valores) > 4 else None,
            'Aliq_Atual': valores[5] if len(valores) > 5 else None,
            'Valor_Liquido_Atual': valores[6] if len(valores) > 6 else None,
            'Part_Prflo_%': valores[7] if len(valores) > 7 else None,
            'Rent_Mes_%': valores[8] if len(valores) > 8 else None,
            'Rent_Inicio_%': valores[9] if len(valores) > 9 else None,
        }

    # Título com 3 datas
    # Olhando a tabela, após as 3 datas vem:
    # Aplicação Inicial, [indexador e taxa no texto], Quantidade, Preço, Valor Bruto, Impostos, Aliq, Valor Líq, Part%, Rent Mês, Rent Início

    return {
        'Tipo': section,
        'Nome': nome,
        'Data_Emissao': dates[0],
        'Data_Aplicacao': dates[1],
        'Data_Vencimento': dates[2],
        'Aplicacao_Inicial_R$': valores[0] if len(valores) > 0 else None,
        'Indexador': indexador,
        'TX_Emis': tx_emis,
        'TX_aa': tx_aa,
        'Quantidade': valores[1] if len(valores) > 1 else None,
        'Preco_Atual': valores[2] if len(valores) > 2 else None,
        'Valor_Bruto_Atual': valores[3] if len(valores) > 3 else None,
        'Impostos': valores[4] if len(valores) > 4 else None,
        'Aliq_Atual': valores[5] if len(valores) > 5 else None,
        'Valor_Liquido_Atual': valores[6] if len(valores) > 6 else None,
        'Part_Prflo_%': valores[7] if len(valores) > 7 else None,
        'Rent_Mes_%': valores[8] if len(valores) > 8 else None,
        'Rent_Inicio_%': valores[9] if len(valores) > 9 else None,
    }


def main():
    pdf_path = 'input/bradesco-ativos.pdf'
    output_csv = 'output/investimentos_bradesco_com_nomes.csv'

    print("=" * 80)
    print("EXTRAÇÃO COM NOMES CORRETOS")
    print("=" * 80)

    if not Path(pdf_path).exists():
        print(f"\n❌ PDF não encontrado: {pdf_path}")
        return

    # Extrai
    print("\n📄 Extraindo investimentos...")
    investments = extract_table_from_pdf(pdf_path)

    print(f"\n\n📊 Total extraído: {len(investments)}")

    # Cria DataFrame
    df = pd.DataFrame(investments)

    # Salva CSV
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding='utf-8-sig')

    print(f"✓ CSV salvo: {output_path}")

    # Mostra resumo
    print("\n" + "=" * 80)
    print("RESUMO")
    print("=" * 80)

    print(f"\nPor tipo:")
    print(df['Tipo'].value_counts())

    print(f"\nInvestimentos com nome:")
    with_name = df['Nome'].notna().sum()
    print(f"  • Com nome: {with_name}/{len(df)}")
    print(f"  • Sem nome: {len(df) - with_name}/{len(df)}")

    print(f"\n📋 Primeiros 10 registros:")
    print(df[['Tipo', 'Nome', 'Valor_Bruto_Atual']].head(10).to_string(index=False))

    print("\n" + "=" * 80)
    print("✅ CONCLUÍDO!")
    print("=" * 80)


if __name__ == '__main__':
    main()
