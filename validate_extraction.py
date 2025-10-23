#!/usr/bin/env python3
"""
Script para validar os dados extraídos do PDF do Bradesco
"""

import pandas as pd
from pathlib import Path


def validate_csv(csv_path):
    """
    Valida o CSV extraído

    Args:
        csv_path: Caminho para o arquivo CSV
    """

    print("=" * 80)
    print("VALIDAÇÃO DOS DADOS EXTRAÍDOS")
    print("=" * 80)

    # Verifica se o arquivo existe
    if not Path(csv_path).exists():
        print(f"\n❌ Arquivo não encontrado: {csv_path}")
        return False

    # Lê o CSV
    df = pd.read_csv(csv_path, encoding='utf-8-sig')

    print(f"\n📊 Total de registros: {len(df)}")
    print(f"📋 Total de colunas: {len(df.columns)}")

    # Validações básicas
    validations = []

    # 1. Verifica se há registros
    if len(df) > 0:
        validations.append(("✓", "Arquivo contém dados"))
    else:
        validations.append(("✗", "Arquivo está vazio"))

    # 2. Verifica colunas obrigatórias
    required_columns = ['Tipo', 'Data_Vencimento', 'Valor_Bruto_Atual']
    missing_columns = [col for col in required_columns if col not in df.columns]

    if not missing_columns:
        validations.append(("✓", "Todas as colunas obrigatórias presentes"))
    else:
        validations.append(("✗", f"Colunas faltando: {', '.join(missing_columns)}"))

    # 3. Verifica se há datas válidas
    date_columns = ['Data_Emissao', 'Data_Aplicacao', 'Data_Vencimento']
    has_dates = False
    for col in date_columns:
        if col in df.columns and not df[col].isna().all():
            has_dates = True
            break

    if has_dates:
        validations.append(("✓", "Datas extraídas corretamente"))
    else:
        validations.append(("✗", "Nenhuma data foi extraída"))

    # 4. Verifica valores numéricos
    if 'Valor_Bruto_Atual' in df.columns:
        valores = df['Valor_Bruto_Atual'].dropna()
        if len(valores) > 0:
            validations.append(("✓", f"Valores extraídos: {len(valores)} registros"))
        else:
            validations.append(("✗", "Nenhum valor foi extraído"))

    # 5. Verifica distribuição por tipo
    if 'Tipo' in df.columns:
        tipos = df['Tipo'].value_counts()
        if len(tipos) > 0:
            validations.append(("✓", f"Tipos identificados: {len(tipos)}"))
        else:
            validations.append(("✗", "Nenhum tipo foi identificado"))

    # Mostra resultados
    print("\n" + "=" * 80)
    print("RESULTADOS DA VALIDAÇÃO")
    print("=" * 80)

    all_passed = True
    for status, message in validations:
        print(f"{status} {message}")
        if status == "✗":
            all_passed = False

    # Estatísticas detalhadas
    if all_passed:
        print("\n" + "=" * 80)
        print("ESTATÍSTICAS DETALHADAS")
        print("=" * 80)

        # Por tipo
        print("\n📊 Distribuição por Tipo:")
        tipo_dist = df['Tipo'].value_counts()
        for tipo, count in tipo_dist.items():
            pct = (count / len(df)) * 100
            print(f"  • {tipo}: {count} ({pct:.1f}%)")

        # Valores totais
        print("\n💰 Valores:")
        try:
            df_temp = df.copy()
            df_temp['Valor_Numerico'] = df_temp['Valor_Bruto_Atual'].str.replace('.', '').str.replace(',', '.').astype(float, errors='ignore')
            total = df_temp['Valor_Numerico'].sum()
            media = df_temp['Valor_Numerico'].mean()
            minimo = df_temp['Valor_Numerico'].min()
            maximo = df_temp['Valor_Numerico'].max()

            print(f"  • Total: R$ {total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
            print(f"  • Média: R$ {media:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
            print(f"  • Mínimo: R$ {minimo:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
            print(f"  • Máximo: R$ {maximo:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        except Exception as e:
            print(f"  ⚠ Erro ao calcular valores: {e}")

        # Rentabilidades
        print("\n📈 Rentabilidades:")
        try:
            if 'Rent_Mes_%' in df.columns:
                df_temp = df.copy()
                df_temp['Rent_Mes_Num'] = df_temp['Rent_Mes_%'].str.replace(',', '.').astype(float, errors='ignore')
                media_mes = df_temp['Rent_Mes_Num'].mean()
                print(f"  • Rentabilidade Média do Mês: {media_mes:.2f}%")

            if 'Rent_Inicio_%' in df.columns:
                df_temp['Rent_Inicio_Num'] = df_temp['Rent_Inicio_%'].str.replace(',', '.').astype(float, errors='ignore')
                media_inicio = df_temp['Rent_Inicio_Num'].mean()
                print(f"  • Rentabilidade Média desde Início: {media_inicio:.2f}%")
        except Exception as e:
            print(f"  ⚠ Erro ao calcular rentabilidades: {e}")

        # Indexadores
        print("\n🔍 Indexadores:")
        if 'Indexador' in df.columns:
            indexadores = df['Indexador'].value_counts()
            for idx, count in indexadores.items():
                if pd.notna(idx):
                    print(f"  • {idx}: {count}")

        # Campos com dados faltantes
        print("\n⚠️  Completude dos Dados:")
        for col in df.columns:
            missing = df[col].isna().sum()
            if missing > 0:
                pct = (missing / len(df)) * 100
                print(f"  • {col}: {missing} campos vazios ({pct:.1f}%)")

    # Resultado final
    print("\n" + "=" * 80)
    if all_passed:
        print("✅ VALIDAÇÃO PASSOU - Dados extraídos com sucesso!")
    else:
        print("⚠️  VALIDAÇÃO FALHOU - Verifique os erros acima")
    print("=" * 80)

    return all_passed


def compare_with_expected():
    """
    Compara com valores esperados conhecidos do PDF
    """

    print("\n" + "=" * 80)
    print("COMPARAÇÃO COM VALORES ESPERADOS")
    print("=" * 80)

    expected_values = {
        'total_investments': 27,  # Baseado na imagem fornecida
        'pos_fixado': 5,
        'pre_fixado': 10,
        'juro_real': 11,
        'multimercados': 1,
        'total_valor': 3190069.45,  # Valor aproximado do total
    }

    csv_path = 'output/investimentos_bradesco_estruturado.csv'
    df = pd.read_csv(csv_path, encoding='utf-8-sig')

    comparisons = []

    # Total de investimentos
    actual_total = len(df)
    expected_total = expected_values['total_investments']
    match = actual_total == expected_total
    comparisons.append((
        "✓" if match else "⚠",
        f"Total de investimentos: {actual_total} (esperado: {expected_total})"
    ))

    # Distribuição por tipo
    tipo_counts = df['Tipo'].value_counts()

    for tipo, expected_count in [
        ('PÓS-FIXADO', expected_values['pos_fixado']),
        ('PRÉ-FIXADO', expected_values['pre_fixado']),
        ('JURO REAL - INFLAÇÃO', expected_values['juro_real']),
        ('MULTIMERCADOS', expected_values['multimercados']),
    ]:
        actual_count = tipo_counts.get(tipo, 0)
        match = actual_count == expected_count
        comparisons.append((
            "✓" if match else "⚠",
            f"{tipo}: {actual_count} (esperado: {expected_count})"
        ))

    # Valor total
    try:
        df_temp = df.copy()
        df_temp['Valor_Numerico'] = df_temp['Valor_Bruto_Atual'].str.replace('.', '').str.replace(',', '.').astype(float, errors='ignore')
        actual_valor = df_temp['Valor_Numerico'].sum()
        expected_valor = expected_values['total_valor']
        diff = abs(actual_valor - expected_valor)
        match = diff < 1000  # Diferença aceitável de R$ 1.000
        comparisons.append((
            "✓" if match else "⚠",
            f"Valor total: R$ {actual_valor:,.2f} (esperado: R$ {expected_valor:,.2f})".replace(',', 'X').replace('.', ',').replace('X', '.')
        ))
    except Exception as e:
        comparisons.append(("✗", f"Erro ao calcular valor total: {e}"))

    # Mostra comparações
    print()
    for status, message in comparisons:
        print(f"{status} {message}")

    print("=" * 80)


def main():
    """Função principal"""

    csv_path = 'output/investimentos_bradesco_estruturado.csv'

    # Valida o CSV
    success = validate_csv(csv_path)

    # Compara com valores esperados
    if success:
        compare_with_expected()


if __name__ == '__main__':
    main()
