#!/usr/bin/env python3
"""
Script melhorado para extrair investimentos do PDF em formato JSON
Usa a extração por palavras (similar ao CSV final) mas exporta em JSON hierárquico
"""

import pdfplumber
import json
import re
from pathlib import Path
from datetime import datetime


def clean_float(value_str):
    """Converte string brasileira para float"""
    if not value_str or value_str.strip() == '':
        return None
    try:
        return float(value_str.replace('.', '').replace(',', '.'))
    except:
        return None


def parse_date_iso(date_str):
    """Converte data dd/mm/aa para ISO"""
    if not date_str:
        return None
    try:
        if len(date_str.split('/')[-1]) == 2:
            date_obj = datetime.strptime(date_str, '%d/%m/%y')
        else:
            date_obj = datetime.strptime(date_str, '%d/%m/%Y')
        return date_obj.strftime('%Y-%m-%d')
    except:
        return date_str


def extract_investments_structured(pdf_path):
    """Extrai investimentos e organiza em JSON hierárquico"""

    estrutura = {
        'metadata': {
            'data_extracao': datetime.now().isoformat(),
            'arquivo_origem': str(pdf_path),
            'banco': 'Bradesco',
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

    section_map = {
        'PÓS-FIXADO': ('renda_fixa', 'pos_fixado'),
        'PRÉ-FIXADO': ('renda_fixa', 'pre_fixado'),
        'JURO REAL - INFLAÇÃO': ('renda_fixa', 'juro_real_inflacao'),
        'MULTIMERCADOS': ('alternativos', 'multimercados'),
    }

    current_section = None
    current_subsection = None

    with pdfplumber.open(pdf_path) as pdf:
        for page_num in [5, 6]:  # Páginas 6 e 7
            page = pdf.pages[page_num]
            words = page.extract_words()

            print(f"\n=== Página {page_num + 1} ===")

            # Agrupa palavras por linha
            lines_dict = {}
            for word in words:
                y = round(word['top'], 1)
                if y not in lines_dict:
                    lines_dict[y] = []
                lines_dict[y].append(word)

            sorted_lines = sorted(lines_dict.items())

            for y, words_in_line in sorted_lines:
                words_in_line.sort(key=lambda w: w['x0'])
                line_text = ' '.join([w['text'] for w in words_in_line]).strip()

                # Identifica seção
                if line_text in section_map:
                    section_info = section_map[line_text]
                    current_section = section_info[0]
                    current_subsection = section_info[1]
                    print(f"\n▶ {line_text}")
                    continue

                # Ignora headers
                if not line_text or 'RENDA FIXA' in line_text or 'Data de' in line_text:
                    continue

                # Ignora totais
                if line_text.startswith('Total') or line_text == 'ALTERNATIVOS':
                    continue

                # Processa linha de investimento
                if current_section and current_subsection and re.search(r'\d{2}/\d{2}/\d{2}', line_text):
                    investment = parse_investment_line(line_text)

                    if investment:
                        estrutura[current_section][current_subsection].append(investment)
                        nome = investment.get('nome', line_text[:40])
                        print(f"  ✓ {nome}")

    # Adiciona totais
    estrutura = add_totals(estrutura)

    return estrutura


def parse_investment_line(line_text):
    """Parse completo de uma linha de investimento"""

    # Extrai nome (antes da primeira data)
    nome_match = re.match(r'^([A-Z][^0-9]+?)(?=\d{2}/\d{2}/)', line_text)
    nome = nome_match.group(1).strip() if nome_match else None

    # Extrai todas as datas
    dates = re.findall(r'\d{2}/\d{2}/\d{2,4}', line_text)

    # Extrai todos os valores
    valores_str = re.findall(r'[\d.]+,\d{2}', line_text)
    valores = [clean_float(v) for v in valores_str]

    # Identifica indexador
    indexador = None
    tx_emis_str = None

    if 'CDI' in line_text:
        indexador = 'CDI'
        match = re.search(r'CDI\s*-\s*([\d,]+)', line_text)
        if match:
            tx_emis_str = match.group(1)
    elif 'PRE' in line_text:
        indexador = 'PRE'
        match = re.search(r'PRE\s+([\d,]+)', line_text)
        if match:
            tx_emis_str = match.group(1)
    elif 'IPCA' in line_text:
        if 'M D' in line_text or 'M\s+D' in line_text:
            indexador = 'IPCA_MD'
        else:
            indexador = 'IPCA'
        match = re.search(r'IPCA(?:\s+M\s+D)?\s+([\d,]+)', line_text)
        if match:
            tx_emis_str = match.group(1)

    # Monta estrutura baseada no número de datas
    is_fund = len(dates) < 3

    if is_fund:
        # Fundo: apenas 1 ou 2 datas
        # Estrutura: Nome, Data, Aplicação, Quantidade, Preço, Valor Bruto, Impostos, Aliq, Valor Líq, Part%, Rent Mês, Rent Início
        return {
            'nome': nome,
            'tipo': 'FUNDO',
            'datas': {
                'aplicacao': parse_date_iso(dates[0]) if len(dates) > 0 else None,
            },
            'valores': {
                'aplicacao_inicial': valores[0] if len(valores) > 0 else None,
                'quantidade': valores[1] if len(valores) > 1 else None,
                'preco_atual': valores[2] if len(valores) > 2 else None,
                'valor_bruto_atual': valores[3] if len(valores) > 3 else None,
                'impostos': valores[4] if len(valores) > 4 else None,
                'valor_liquido_atual': valores[6] if len(valores) > 6 else None,
            },
            'rentabilidade': {
                'aliquota_atual': valores[5] if len(valores) > 5 else None,
                'participacao_portfolio_pct': valores[7] if len(valores) > 7 else None,
                'mes_pct': valores[8] if len(valores) > 8 else None,
                'desde_inicio_pct': valores[9] if len(valores) > 9 else None,
            }
        }
    else:
        # Título: 3 datas
        # Olhando a tabela da imagem:
        # Colunas: Nome, Data Emis, Data Aplic, Data Venc, Aplic Inicial, TX% Emis, TX% a.a., Quant, Preço, Valor Bruto, Impostos, Aliq, Valor Líq, Part%, Rent Mês, Rent Início

        # Se tem indexador explícito (CDI/PRE/IPCA), a TX% vem separada no texto
        # Se não tem, os valores seguem direto

        if indexador:
            # Com indexador: Aplic Inicial, [TX no texto], Quantidade, Preço, Valor Bruto, Impostos, Aliq, Valor Líq, Part%, Rent Mês, Rent Início
            return {
                'nome': nome,
                'tipo': 'TITULO',
                'indexador': {
                    'tipo': indexador,
                    'taxa_emissao_pct': clean_float(tx_emis_str) if tx_emis_str else None,
                    'taxa_aa_pct': clean_float(tx_emis_str) if tx_emis_str else None,
                },
                'datas': {
                    'emissao': parse_date_iso(dates[0]),
                    'aplicacao': parse_date_iso(dates[1]),
                    'vencimento': parse_date_iso(dates[2]),
                },
                'valores': {
                    'aplicacao_inicial': valores[0] if len(valores) > 0 else None,
                    'quantidade': valores[1] if len(valores) > 1 else None,
                    'preco_atual': valores[2] if len(valores) > 2 else None,
                    'valor_bruto_atual': valores[3] if len(valores) > 3 else None,
                    'impostos': valores[4] if len(valores) > 4 else None,
                    'valor_liquido_atual': valores[6] if len(valores) > 6 else None,
                },
                'rentabilidade': {
                    'aliquota_atual_pct': valores[5] if len(valores) > 5 else None,
                    'participacao_portfolio_pct': valores[7] if len(valores) > 7 else None,
                    'mes_pct': valores[8] if len(valores) > 8 else None,
                    'desde_inicio_pct': valores[9] if len(valores) > 9 else None,
                }
            }
        else:
            # Sem indexador: Aplic Inicial, TX%, TX% a.a., Quantidade, Preço, Valor Bruto, Impostos, Aliq, Valor Líq, Part%, Rent Mês, Rent Início
            return {
                'nome': nome,
                'tipo': 'TITULO',
                'indexador': None,
                'datas': {
                    'emissao': parse_date_iso(dates[0]),
                    'aplicacao': parse_date_iso(dates[1]),
                    'vencimento': parse_date_iso(dates[2]),
                },
                'valores': {
                    'aplicacao_inicial': valores[0] if len(valores) > 0 else None,
                    'taxa_emissao_pct': valores[1] if len(valores) > 1 else None,
                    'taxa_aa_pct': valores[2] if len(valores) > 2 else None,
                    'quantidade': valores[3] if len(valores) > 3 else None,
                    'preco_atual': valores[4] if len(valores) > 4 else None,
                    'valor_bruto_atual': valores[5] if len(valores) > 5 else None,
                    'impostos': valores[6] if len(valores) > 6 else None,
                    'valor_liquido_atual': valores[8] if len(valores) > 8 else None,
                },
                'rentabilidade': {
                    'aliquota_atual_pct': valores[7] if len(valores) > 7 else None,
                    'participacao_portfolio_pct': valores[9] if len(valores) > 9 else None,
                    'mes_pct': valores[10] if len(valores) > 10 else None,
                    'desde_inicio_pct': valores[11] if len(valores) > 11 else None,
                }
            }


def add_totals(estrutura):
    """Adiciona totais calculados"""

    for section in ['renda_fixa', 'alternativos']:
        for subsection, investments in list(estrutura[section].items()):
            if isinstance(investments, list):
                total_bruto = sum(
                    inv['valores'].get('valor_bruto_atual', 0) or 0
                    for inv in investments
                )
                total_liquido = sum(
                    inv['valores'].get('valor_liquido_atual', 0) or 0
                    for inv in investments
                )

                estrutura[section][f'{subsection}_summary'] = {
                    'quantidade': len(investments),
                    'total_bruto': round(total_bruto, 2),
                    'total_liquido': round(total_liquido, 2),
                }

    # Total geral
    total_inv = 0
    total_bruto = 0
    total_liquido = 0

    for section in ['renda_fixa', 'alternativos']:
        for subsection, investments in estrutura[section].items():
            if isinstance(investments, list):
                total_inv += len(investments)
                for inv in investments:
                    total_bruto += inv['valores'].get('valor_bruto_atual', 0) or 0
                    total_liquido += inv['valores'].get('valor_liquido_atual', 0) or 0

    estrutura['totais'] = {
        'quantidade_total': total_inv,
        'valor_bruto_total': round(total_bruto, 2),
        'valor_liquido_total': round(total_liquido, 2),
    }

    return estrutura


def main():
    pdf_path = 'input/bradesco-ativos.pdf'
    output_json = 'output/investimentos_bradesco_estruturado.json'

    print("=" * 80)
    print("EXTRAÇÃO JSON ESTRUTURADO - BRADESCO")
    print("=" * 80)

    if not Path(pdf_path).exists():
        print(f"\n❌ Arquivo não encontrado: {pdf_path}")
        return

    # Extrai
    print("\n📄 Extraindo investimentos...")
    data = extract_investments_structured(pdf_path)

    # Salva
    output_path = Path(output_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n\n✓ JSON salvo em: {output_path}")

    # Resumo
    print("\n" + "=" * 80)
    print("RESUMO")
    print("=" * 80)

    print(f"\n📊 Renda Fixa:")
    print(f"  • Pós-Fixado: {len(data['renda_fixa']['pos_fixado'])}")
    print(f"  • Pré-Fixado: {len(data['renda_fixa']['pre_fixado'])}")
    print(f"  • IPCA: {len(data['renda_fixa']['juro_real_inflacao'])}")

    print(f"\n📊 Alternativos:")
    print(f"  • Multimercados: {len(data['alternativos']['multimercados'])}")

    print(f"\n💰 Totais:")
    print(f"  • Total: {data['totais']['quantidade_total']} investimentos")
    print(f"  • Valor Bruto: R$ {data['totais']['valor_bruto_total']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

    # Exemplo
    if data['renda_fixa']['pos_fixado']:
        print("\n" + "=" * 80)
        print("EXEMPLO - Primeiro Pós-Fixado:")
        print("=" * 80)
        print(json.dumps(data['renda_fixa']['pos_fixado'][0], ensure_ascii=False, indent=2))

    print("\n" + "=" * 80)
    print("✅ CONCLUÍDO!")
    print("=" * 80)


if __name__ == '__main__':
    main()
