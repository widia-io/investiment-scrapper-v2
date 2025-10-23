#!/usr/bin/env python3
"""
Aplica regras de negócio no CSV flat gerado, ajustando as colunas:
- Categoria: recebe o valor atual de "Tipo de Ativo"
- Tipo de Ativo: recebe classificação baseada em regras (Renda Fixa ou Fundo de Investimento)
"""

import pandas as pd
import os
import sys


def classify_asset_type(tipo_ativo_original):
    """
    Classifica o tipo de ativo baseado nas regras de negócio:
    - CRI/CRA/DEB/CDB/LCI/LCA/LIG/NTN-B/NTN-F/LTN/LFT → Renda Fixa
    - Fundo → Fundo de Investimento
    """
    # Lista de tipos que são Renda Fixa
    renda_fixa_types = [
        'CRI', 'CRA', 'DEB', 'DEBENTURE', 'DEBÊNTURE',
        'CDB', 'LCI', 'LCA', 'LIG',
        'NTN-B', 'NTN-F', 'LTN', 'LFT',
        'TÍTULO PÚBLICO', 'TESOURO'
    ]

    # Converte para uppercase para comparação case-insensitive
    tipo_upper = str(tipo_ativo_original).upper().strip()

    # Verifica se é Fundo
    if 'FUNDO' in tipo_upper:
        return 'Fundo de Investimento'

    # Verifica se é algum tipo de Renda Fixa
    for rf_type in renda_fixa_types:
        if rf_type in tipo_upper:
            return 'Renda Fixa'

    # Se não encontrou, mantém o valor original
    return tipo_ativo_original


def apply_business_rules(input_csv, output_csv=None):
    """
    Aplica regras de negócio no CSV:
    1. Move "Tipo de Ativo" atual para "Categoria"
    2. Aplica nova classificação em "Tipo de Ativo"
    """

    print("=" * 80)
    print("APLICANDO REGRAS DE NEGÓCIO")
    print("=" * 80)

    # Verifica se arquivo existe
    if not os.path.exists(input_csv):
        print(f"❌ Arquivo não encontrado: {input_csv}")
        return None

    # Lê CSV
    print(f"\n📄 Lendo CSV: {input_csv}")
    df = pd.read_csv(input_csv, encoding='utf-8-sig')

    print(f"✓ {len(df)} linhas encontradas")

    # Mostra estrutura atual
    print(f"\n📊 Colunas atuais: {', '.join(df.columns.tolist())}")

    # Aplica regras de negócio
    print("\n🔄 Aplicando transformações...")

    # 1. Salva o "Tipo de Ativo" atual na coluna "Categoria"
    df['Categoria'] = df['Tipo de Ativo']

    # 2. Aplica nova classificação em "Tipo de Ativo"
    df['Tipo de Ativo'] = df['Categoria'].apply(classify_asset_type)

    print("✓ Regras aplicadas")

    # Define nome do arquivo de saída
    if output_csv is None:
        # Usa o mesmo nome, sobrescrevendo o original
        output_csv = input_csv

    # Salva CSV com regras aplicadas
    df.to_csv(output_csv, index=False, encoding='utf-8-sig')

    print(f"\n✓ CSV atualizado salvo: {output_csv}")

    # Mostra resumo das mudanças
    print("\n" + "=" * 80)
    print("RESUMO DAS MUDANÇAS")
    print("=" * 80)

    print(f"\n📋 Distribuição por Tipo de Ativo (nova classificação):")
    tipo_counts = df['Tipo de Ativo'].value_counts()
    for tipo, count in tipo_counts.items():
        print(f"   • {tipo}: {count}")

    print(f"\n📋 Distribuição por Categoria (classificação detalhada):")
    cat_counts = df['Categoria'].value_counts()
    for cat, count in cat_counts.items():
        print(f"   • {cat}: {count}")

    print(f"\n📋 Primeiras 5 linhas após aplicação das regras:")
    print("-" * 80)
    # Mostra apenas colunas relevantes para visualização
    display_cols = ['Banco', 'Ativo', 'Tipo de Ativo', 'Categoria', 'Valor']
    print(df[display_cols].head().to_string(index=False))

    print("\n" + "=" * 80)
    print("✅ REGRAS APLICADAS COM SUCESSO!")
    print("=" * 80)

    return df


def main():
    """Função principal"""

    # Define caminho padrão
    default_csv = 'output/investimentos_bradesco_flat.csv'

    # Permite passar arquivo como argumento
    if len(sys.argv) > 1:
        input_csv = sys.argv[1]
    else:
        input_csv = default_csv

    # Permite especificar arquivo de saída
    output_csv = sys.argv[2] if len(sys.argv) > 2 else None

    apply_business_rules(input_csv, output_csv)


if __name__ == '__main__':
    main()
