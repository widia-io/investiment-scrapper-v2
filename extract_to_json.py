#!/usr/bin/env python3
"""
Script para extrair a tabela "Posição Detalhada dos Investimentos"
do PDF do Bradesco e exportar para JSON estruturado
"""

import pdfplumber
import json
import re
from pathlib import Path
from datetime import datetime


def clean_monetary_value(value):
    """
    Limpa e converte valor monetário brasileiro para float

    Args:
        value: String no formato brasileiro (ex: 100.000,00)

    Returns:
        float ou None
    """
    if not value or value.strip() == '':
        return None

    try:
        # Remove pontos (separadores de milhar) e substitui vírgula por ponto
        cleaned = value.replace('.', '').replace(',', '.')
        return float(cleaned)
    except:
        return None


def clean_percentage(value):
    """
    Limpa e converte percentual para float

    Args:
        value: String no formato brasileiro (ex: 10,50)

    Returns:
        float ou None
    """
    if not value or value.strip() == '':
        return None

    try:
        # Substitui vírgula por ponto
        cleaned = value.replace(',', '.')
        # Remove possíveis parênteses negativos
        cleaned = cleaned.replace('(', '-').replace(')', '')
        return float(cleaned)
    except:
        return None


def parse_date(date_str):
    """
    Parse data no formato dd/mm/aa ou dd/mm/aaaa

    Args:
        date_str: String da data

    Returns:
        String no formato ISO (YYYY-MM-DD) ou None
    """
    if not date_str or date_str.strip() == '':
        return None

    try:
        # Tenta dd/mm/aa (2 dígitos de ano)
        if len(date_str.split('/')[-1]) == 2:
            date_obj = datetime.strptime(date_str, '%d/%m/%y')
        else:
            # dd/mm/aaaa (4 dígitos)
            date_obj = datetime.strptime(date_str, '%d/%m/%Y')

        return date_obj.strftime('%Y-%m-%d')
    except:
        return date_str  # Retorna original se falhar


def extract_investment_from_line(line_text, section, subsection=None):
    """
    Extrai dados de investimento de uma linha

    Args:
        line_text: Texto da linha
        section: Seção (RENDA_FIXA ou ALTERNATIVOS)
        subsection: Subseção (POS_FIXADO, PRE_FIXADO, etc.)

    Returns:
        Dict com dados do investimento ou None
    """

    # Extrai nome do ativo (tudo antes da primeira data)
    nome_match = re.match(r'^([A-Z][^0-9]+?)(?=\d{2}/\d{2}/)', line_text)
    nome = nome_match.group(1).strip() if nome_match else None

    # Extrai todas as datas
    dates = re.findall(r'(\d{2}/\d{2}/\d{2,4})', line_text)

    # Extrai todos os valores numéricos
    valores = re.findall(r'([\d.]+,\d{2})', line_text)

    # Extrai indexador e taxa
    indexador = None
    tx_percentual = None

    # Procura por CDI - XX.XX ou CDI - XX
    cdi_match = re.search(r'CDI\s*-\s*([\d,]+)', line_text)
    if cdi_match:
        indexador = 'CDI'
        tx_percentual = clean_percentage(cdi_match.group(1))

    # Procura por PRE seguido de percentual
    if not indexador:
        pre_match = re.search(r'PRE\s+([\d,]+)', line_text)
        if pre_match:
            indexador = 'PRE'
            tx_percentual = clean_percentage(pre_match.group(1))

    # Procura por IPCA
    if not indexador:
        ipca_match = re.search(r'IPCA(?:\s+M\s+D)?\s+([\d,]+)', line_text)
        if ipca_match:
            if 'M D' in line_text:
                indexador = 'IPCA_MD'
            else:
                indexador = 'IPCA'
            tx_percentual = clean_percentage(ipca_match.group(1))

    # Se não tem pelo menos 2 datas, não é uma linha válida
    if len(dates) < 2:
        return None

    # Para fundos (sem 3 datas), adapta extração
    is_fund = 'FIC MM' in line_text or len(dates) < 3

    if is_fund:
        # Fundos têm estrutura diferente
        investment = {
            'nome': nome,
            'data_emissao': None,
            'data_aplicacao': parse_date(dates[0]) if len(dates) > 0 else None,
            'data_vencimento': None,
            'aplicacao_inicial': clean_monetary_value(valores[0]) if len(valores) > 0 else None,
            'indexador': None,
            'tx_emissao': None,
            'tx_aa': None,
            'quantidade': clean_monetary_value(valores[1]) if len(valores) > 1 else None,
            'preco_atual': clean_monetary_value(valores[2]) if len(valores) > 2 else None,
            'valor_bruto_atual': clean_monetary_value(valores[3]) if len(valores) > 3 else None,
            'impostos': clean_monetary_value(valores[4]) if len(valores) > 4 else None,
            'aliquota_atual': clean_percentage(valores[5]) if len(valores) > 5 else None,
            'valor_liquido_atual': clean_monetary_value(valores[6]) if len(valores) > 6 else None,
            'participacao_portfolio': clean_percentage(valores[7]) if len(valores) > 7 else None,
            'rentabilidade_mes': clean_percentage(valores[8]) if len(valores) > 8 else None,
            'rentabilidade_inicio': clean_percentage(valores[9]) if len(valores) > 9 else None,
        }
    else:
        # Títulos têm 3 datas
        # Determina offset baseado se tem indexador explícito
        offset = 0 if indexador else 0

        investment = {
            'nome': nome,
            'data_emissao': parse_date(dates[0]) if len(dates) > 0 else None,
            'data_aplicacao': parse_date(dates[1]) if len(dates) > 1 else None,
            'data_vencimento': parse_date(dates[2]) if len(dates) > 2 else None,
            'aplicacao_inicial': clean_monetary_value(valores[0]) if len(valores) > 0 else None,
            'indexador': indexador,
            'tx_emissao': tx_percentual,
            'tx_aa': tx_percentual,
            'quantidade': clean_monetary_value(valores[1]) if len(valores) > 1 else None,
            'preco_atual': clean_monetary_value(valores[2]) if len(valores) > 2 else None,
            'valor_bruto_atual': clean_monetary_value(valores[3]) if len(valores) > 3 else None,
            'impostos': clean_monetary_value(valores[4]) if len(valores) > 4 else None,
            'aliquota_atual': clean_percentage(valores[5]) if len(valores) > 5 else None,
            'valor_liquido_atual': clean_monetary_value(valores[6]) if len(valores) > 6 else None,
            'participacao_portfolio': clean_percentage(valores[7]) if len(valores) > 7 else None,
            'rentabilidade_mes': clean_percentage(valores[8]) if len(valores) > 8 else None,
            'rentabilidade_inicio': clean_percentage(valores[9]) if len(valores) > 9 else None,
        }

    return investment


def extract_investments_from_pdf(pdf_path):
    """
    Extrai investimentos do PDF e organiza em estrutura hierárquica

    Args:
        pdf_path: Caminho para o PDF

    Returns:
        Dict com estrutura hierárquica
    """

    # Estrutura de dados
    data = {
        'metadata': {
            'data_extracao': datetime.now().isoformat(),
            'arquivo_origem': str(pdf_path),
        },
        'renda_fixa': {
            'pos_fixado': [],
            'pre_fixado': [],
            'juro_real_inflacao': []
        },
        'alternativos': {
            'multimercados': []
        }
    }

    # Mapeamento de seções
    section_map = {
        'PÓS-FIXADO': ('renda_fixa', 'pos_fixado'),
        'PRÉ-FIXADO': ('renda_fixa', 'pre_fixado'),
        'JURO REAL - INFLAÇÃO': ('renda_fixa', 'juro_real_inflacao'),
        'MULTIMERCADOS': ('alternativos', 'multimercados'),
    }

    current_section = None
    current_subsection = None

    with pdfplumber.open(pdf_path) as pdf:
        # Páginas 6 e 7
        for page_num in [5, 6]:
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

            for y, words_in_line in sorted_lines:
                # Ordena palavras na linha
                words_in_line.sort(key=lambda w: w['x0'])

                # Reconstrói linha
                line_text = ' '.join([w['text'] for w in words_in_line]).strip()

                # Verifica mudança de seção
                if line_text in section_map:
                    section_info = section_map[line_text]
                    current_section = section_info[0]
                    current_subsection = section_info[1]
                    print(f"\n▶ {line_text}")
                    continue

                # Ignora headers e linhas vazias
                if not line_text or 'RENDA FIXA' in line_text or 'Data de' in line_text:
                    continue

                # Ignora totais e seções
                if line_text.startswith('Total') or line_text == 'ALTERNATIVOS':
                    continue

                # Tenta extrair investimento
                if current_section and current_subsection:
                    # Verifica se tem datas (indicador de linha de dados)
                    if re.search(r'\d{2}/\d{2}/\d{2}', line_text):
                        investment = extract_investment_from_line(
                            line_text,
                            current_section,
                            current_subsection
                        )

                        if investment and investment['valor_bruto_atual']:
                            # Adiciona na estrutura
                            data[current_section][current_subsection].append(investment)

                            nome_display = investment['nome'][:50] if investment['nome'] else line_text[:50]
                            print(f"  ✓ {nome_display}")

    return data


def calculate_totals(data):
    """
    Calcula totais e adiciona na estrutura

    Args:
        data: Estrutura de dados

    Returns:
        Estrutura com totais
    """

    # Totais por subseção
    for section in ['renda_fixa', 'alternativos']:
        # Cria lista de subseções primeiro para não modificar dict durante iteração
        subsections = [(k, v) for k, v in data[section].items() if isinstance(v, list)]

        for subsection_key, investments in subsections:
            total_bruto = sum(inv['valor_bruto_atual'] or 0 for inv in investments)
            total_liquido = sum(inv['valor_liquido_atual'] or 0 for inv in investments)
            total_impostos = sum(inv['impostos'] or 0 for inv in investments)

            # Adiciona metadados da subseção
            data[section][f'{subsection_key}_total'] = {
                'quantidade': len(investments),
                'valor_bruto_total': round(total_bruto, 2),
                'valor_liquido_total': round(total_liquido, 2),
                'impostos_total': round(total_impostos, 2),
            }

    # Total geral
    total_geral_bruto = 0
    total_geral_liquido = 0
    total_geral_impostos = 0
    quantidade_total = 0

    for section in ['renda_fixa', 'alternativos']:
        for subsection_key, investments in data[section].items():
            if isinstance(investments, list):
                for inv in investments:
                    total_geral_bruto += inv['valor_bruto_atual'] or 0
                    total_geral_liquido += inv['valor_liquido_atual'] or 0
                    total_geral_impostos += inv['impostos'] or 0
                    quantidade_total += 1

    data['totais'] = {
        'quantidade_investimentos': quantidade_total,
        'valor_bruto_total': round(total_geral_bruto, 2),
        'valor_liquido_total': round(total_geral_liquido, 2),
        'impostos_total': round(total_geral_impostos, 2),
    }

    return data


def save_json(data, output_path, pretty=True):
    """
    Salva dados em JSON

    Args:
        data: Estrutura de dados
        output_path: Caminho do arquivo
        pretty: Se True, formata com indentação
    """

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        if pretty:
            json.dump(data, f, ensure_ascii=False, indent=2)
        else:
            json.dump(data, f, ensure_ascii=False)

    print(f"\n✓ JSON salvo em: {output_path}")


def main():
    """Função principal"""

    pdf_path = 'input/bradesco-ativos.pdf'
    output_json = 'output/investimentos_bradesco.json'

    print("=" * 80)
    print("EXTRAÇÃO DE INVESTIMENTOS - JSON ESTRUTURADO")
    print("=" * 80)

    if not Path(pdf_path).exists():
        print(f"\n❌ Arquivo não encontrado: {pdf_path}")
        return

    # Extrai dados
    print("\n📄 Extraindo dados do PDF...")
    data = extract_investments_from_pdf(pdf_path)

    # Calcula totais
    print("\n📊 Calculando totais...")
    data = calculate_totals(data)

    # Salva JSON
    print("\n💾 Salvando JSON...")
    save_json(data, output_json)

    # Mostra resumo
    print("\n" + "=" * 80)
    print("RESUMO DOS DADOS")
    print("=" * 80)

    print(f"\n📊 Renda Fixa:")
    print(f"  • Pós-Fixado: {len(data['renda_fixa']['pos_fixado'])} investimentos")
    print(f"  • Pré-Fixado: {len(data['renda_fixa']['pre_fixado'])} investimentos")
    print(f"  • Juro Real (IPCA): {len(data['renda_fixa']['juro_real_inflacao'])} investimentos")

    print(f"\n📊 Alternativos:")
    print(f"  • Multimercados: {len(data['alternativos']['multimercados'])} investimentos")

    print(f"\n💰 Totais:")
    print(f"  • Total de investimentos: {data['totais']['quantidade_investimentos']}")
    print(f"  • Valor bruto total: R$ {data['totais']['valor_bruto_total']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    print(f"  • Valor líquido total: R$ {data['totais']['valor_liquido_total']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

    # Exemplo de acesso aos dados
    print("\n" + "=" * 80)
    print("EXEMPLO DE ESTRUTURA JSON")
    print("=" * 80)
    print("\nPrimeiro investimento Pós-Fixado:")
    if data['renda_fixa']['pos_fixado']:
        primeiro = data['renda_fixa']['pos_fixado'][0]
        print(json.dumps(primeiro, ensure_ascii=False, indent=2))

    print("\n" + "=" * 80)
    print("✅ EXTRAÇÃO CONCLUÍDA!")
    print("=" * 80)


if __name__ == '__main__':
    main()
