#!/usr/bin/env python3
"""
Converte o CSV estruturado para JSON hierárquico
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime


def clean_float(value):
    """Converte valor brasileiro para float"""
    if pd.isna(value) or value == '':
        return None
    try:
        if isinstance(value, str):
            return float(value.replace('.', '').replace(',', '.'))
        return float(value)
    except:
        return None


def parse_date_iso(date_str):
    """Converte data dd/mm/aa para ISO"""
    if pd.isna(date_str) or date_str == '':
        return None
    try:
        parts = str(date_str).split('/')
        day, month, year = parts
        if len(year) == 2:
            year = '20' + year
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    except:
        return str(date_str)


def csv_row_to_json(row):
    """Converte uma linha do CSV para objeto JSON"""

    # Determina se tem indexador explícito
    has_indexador = not pd.isna(row.get('Indexador'))

    obj = {
        'nome': row.get('Nome') if not pd.isna(row.get('Nome')) else None,
        'tipo': 'TITULO',  # Pode ser adaptado depois
        'datas': {
            'emissao': parse_date_iso(row.get('Data_Emissao')),
            'aplicacao': parse_date_iso(row.get('Data_Aplicacao')),
            'vencimento': parse_date_iso(row.get('Data_Vencimento')),
        },
        'valores': {
            'aplicacao_inicial': clean_float(row.get('Aplicacao_Inicial_R$')),
            'quantidade': clean_float(row.get('Quantidade')),
            'preco_atual': clean_float(row.get('Preco_Atual')),
            'valor_bruto_atual': clean_float(row.get('Valor_Bruto_Atual')),
            'impostos': clean_float(row.get('Impostos')),
            'valor_liquido_atual': clean_float(row.get('Valor_Liquido_Atual')),
        },
        'rentabilidade': {
            'aliquota_atual_pct': clean_float(row.get('Aliq_Atual')),
            'participacao_portfolio_pct': clean_float(row.get('Part_Prflo_%')),
            'mes_pct': clean_float(row.get('Rent_Mes_%')),
            'desde_inicio_pct': clean_float(row.get('Rent_Inicio_%')),
        }
    }

    # Adiciona indexador se existir
    if has_indexador:
        obj['indexador'] = {
            'tipo': row.get('Indexador'),
            'taxa_emissao_pct': clean_float(row.get('TX_Emis')),
            'taxa_aa_pct': clean_float(row.get('TX_aa')),
        }
    else:
        obj['indexador'] = None

    return obj


def convert_csv_to_hierarchical_json(csv_path, output_json_path):
    """
    Converte CSV para JSON hierárquico

    Args:
        csv_path: Caminho do CSV
        output_json_path: Caminho do JSON de saída
    """

    print("=" * 80)
    print("CONVERSÃO CSV → JSON HIERÁRQUICO")
    print("=" * 80)

    # Lê CSV
    print(f"\n📄 Lendo CSV: {csv_path}")
    df = pd.read_csv(csv_path, encoding='utf-8-sig')

    print(f"✓ {len(df)} registros carregados")

    # Estrutura hierárquica
    estrutura = {
        'metadata': {
            'data_extracao': datetime.now().isoformat(),
            'fonte': str(csv_path),
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

    # Mapeamento de tipos
    tipo_map = {
        'PÓS-FIXADO': ('renda_fixa', 'pos_fixado'),
        'PRÉ-FIXADO': ('renda_fixa', 'pre_fixado'),
        'JURO REAL - INFLAÇÃO': ('renda_fixa', 'juro_real_inflacao'),
        'MULTIMERCADOS': ('alternativos', 'multimercados'),
    }

    # Converte cada linha
    print("\n📊 Convertendo registros...")
    for idx, row in df.iterrows():
        tipo = row.get('Tipo')

        if tipo in tipo_map:
            section, subsection = tipo_map[tipo]
            obj = csv_row_to_json(row)
            estrutura[section][subsection].append(obj)

            nome = obj.get('nome') or 'Sem nome'
            nome_display = nome[:40] if isinstance(nome, str) else nome
            print(f"  [{tipo}] {nome_display}")

    # Calcula totais
    print("\n💰 Calculando totais...")
    estrutura = add_totals_to_structure(estrutura)

    # Salva JSON
    output_path = Path(output_json_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(estrutura, f, ensure_ascii=False, indent=2)

    print(f"\n✓ JSON salvo em: {output_path}")

    return estrutura


def add_totals_to_structure(estrutura):
    """Adiciona totais calculados à estrutura"""

    total_geral_inv = 0
    total_geral_bruto = 0
    total_geral_liquido = 0

    for section in ['renda_fixa', 'alternativos']:
        for subsection, investments in list(estrutura[section].items()):
            if isinstance(investments, list):
                total_bruto = sum(
                    inv['valores'].get('valor_bruto_atual') or 0
                    for inv in investments
                )
                total_liquido = sum(
                    inv['valores'].get('valor_liquido_atual') or 0
                    for inv in investments
                )
                total_impostos = sum(
                    inv['valores'].get('impostos') or 0
                    for inv in investments
                )

                estrutura[section][f'{subsection}_summary'] = {
                    'quantidade': len(investments),
                    'total_bruto': round(total_bruto, 2),
                    'total_liquido': round(total_liquido, 2),
                    'total_impostos': round(total_impostos, 2),
                }

                total_geral_inv += len(investments)
                total_geral_bruto += total_bruto
                total_geral_liquido += total_liquido

    estrutura['totais'] = {
        'quantidade_investimentos': total_geral_inv,
        'valor_bruto_total': round(total_geral_bruto, 2),
        'valor_liquido_total': round(total_geral_liquido, 2),
    }

    return estrutura


def main():
    csv_path = 'output/investimentos_bradesco_estruturado.csv'
    json_path = 'output/investimentos_bradesco_final.json'

    if not Path(csv_path).exists():
        print(f"\n❌ CSV não encontrado: {csv_path}")
        print("Execute primeiro: python extract_investment_table_final.py")
        return

    # Converte
    estrutura = convert_csv_to_hierarchical_json(csv_path, json_path)

    # Mostra resumo
    print("\n" + "=" * 80)
    print("RESUMO DA ESTRUTURA JSON")
    print("=" * 80)

    print(f"\n📊 Renda Fixa:")
    print(f"  • Pós-Fixado: {len(estrutura['renda_fixa']['pos_fixado'])} investimentos")
    print(f"  • Pré-Fixado: {len(estrutura['renda_fixa']['pre_fixado'])} investimentos")
    print(f"  • Juro Real (IPCA): {len(estrutura['renda_fixa']['juro_real_inflacao'])} investimentos")

    print(f"\n📊 Alternativos:")
    print(f"  • Multimercados: {len(estrutura['alternativos']['multimercados'])} investimentos")

    print(f"\n💰 Totais Gerais:")
    totals = estrutura['totais']
    print(f"  • Quantidade: {totals['quantidade_investimentos']} investimentos")
    print(f"  • Valor Bruto Total: R$ {totals['valor_bruto_total']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    print(f"  • Valor Líquido Total: R$ {totals['valor_liquido_total']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

    # Exemplo de estrutura
    if estrutura['renda_fixa']['pos_fixado']:
        print("\n" + "=" * 80)
        print("EXEMPLO - Primeiro Investimento Pós-Fixado:")
        print("=" * 80)
        print(json.dumps(estrutura['renda_fixa']['pos_fixado'][0], ensure_ascii=False, indent=2))

    print("\n" + "=" * 80)
    print("✅ CONVERSÃO CONCLUÍDA COM SUCESSO!")
    print("=" * 80)


if __name__ == '__main__':
    main()
