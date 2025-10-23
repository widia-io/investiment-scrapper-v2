#!/usr/bin/env python3
"""
Enriquece o CSV flat com a coluna CNPJ das empresas emissoras dos ativos.

Estratégia híbrida:
1. Verifica cache local (cnpj_cache.json)
2. Se não encontrar, usa LLM para normalizar nome da empresa
3. Valida CNPJ nas APIs públicas (ReceitaWS → BrasilAPI)
4. Salva no cache para próximas execuções

Uso:
    python3 enrich_with_cnpj.py                # Processa todos os ativos
    python3 enrich_with_cnpj.py --test         # Processa apenas 5 ativos (teste)
    python3 enrich_with_cnpj.py --dry-run      # Simula sem salvar
"""

import pandas as pd
import os
import sys
import argparse
from cnpj_lookup import (
    load_cache,
    save_cache,
    search_cnpj_complete
)


def enrich_csv_with_cnpj(csv_path, test_mode=False, dry_run=False, use_web_search=True):
    """
    Adiciona coluna CNPJ ao CSV flat.

    Args:
        csv_path: Caminho do CSV a ser enriquecido
        test_mode: Se True, processa apenas 5 linhas
        dry_run: Se True, não salva o CSV (apenas mostra resultado)
        use_web_search: Se True, usa GPT-4o com web search como fallback
    """

    print("=" * 80)
    print("ENRIQUECIMENTO DE CSV COM CNPJ")
    print("=" * 80)

    # Verifica se arquivo existe
    if not os.path.exists(csv_path):
        print(f"❌ Arquivo não encontrado: {csv_path}")
        return None

    # Lê CSV
    print(f"\n📄 Lendo CSV: {csv_path}")
    df = pd.read_csv(csv_path, encoding='utf-8-sig')
    print(f"✓ {len(df)} linhas encontradas")

    # Modo de teste: processa apenas 5 linhas
    if test_mode:
        print("\n⚠️  MODO DE TESTE: Processando apenas 5 linhas")
        df = df.head(5)

    # Carrega cache
    print(f"\n📦 Carregando cache...")
    cache = load_cache()
    cache_entries = len(cache)
    print(f"✓ {cache_entries} entradas no cache")

    # Coleta CNPJs
    print(f"\n🔍 Buscando CNPJs...")
    print("=" * 80)

    cnpjs = []
    empresas = []
    situacoes = []
    sources = []

    total = len(df)
    cached_count = 0
    found_count = 0
    not_found_count = 0

    for idx, row in df.iterrows():
        nome_ativo = row['Ativo']
        print(f"\n[{idx + 1}/{total}] {nome_ativo}")

        resultado = search_cnpj_complete(nome_ativo, cache, verbose=True, use_web_search=use_web_search)

        if resultado:
            cnpjs.append(resultado['cnpj'])
            empresas.append(resultado['empresa'])
            situacoes.append(resultado.get('situacao', ''))
            sources.append(resultado['source'])

            if resultado['source'] == 'cache':
                cached_count += 1
            else:
                found_count += 1
        else:
            cnpjs.append('N/A')
            empresas.append('')
            situacoes.append('')
            sources.append('not_found')
            not_found_count += 1

    # Adiciona colunas ao DataFrame
    df['CNPJ'] = cnpjs
    df['Razao_Social'] = empresas
    df['Situacao_Cadastral'] = situacoes

    # Reordena colunas para ter CNPJ após Ativo
    cols = df.columns.tolist()
    # Remove as colunas novas
    cols = [c for c in cols if c not in ['CNPJ', 'Razao_Social', 'Situacao_Cadastral']]
    # Encontra índice de 'Ativo'
    ativo_idx = cols.index('Ativo')
    # Insere as novas colunas após 'Ativo'
    cols = cols[:ativo_idx + 1] + ['CNPJ', 'Razao_Social', 'Situacao_Cadastral'] + cols[ativo_idx + 1:]
    df = df[cols]

    # Salva CSV (se não for dry-run)
    if not dry_run:
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"\n✓ CSV atualizado: {csv_path}")
    else:
        print(f"\n⚠️  DRY-RUN: CSV NÃO foi salvo")

    # Resumo
    print("\n" + "=" * 80)
    print("RESUMO")
    print("=" * 80)

    print(f"\n📊 Estatísticas:")
    print(f"   • Total de ativos processados: {total}")
    print(f"   • CNPJs encontrados no cache: {cached_count}")
    print(f"   • CNPJs encontrados via API: {found_count}")
    print(f"   • CNPJs não encontrados: {not_found_count}")
    print(f"   • Taxa de sucesso: {((cached_count + found_count) / total * 100):.1f}%")

    new_cache_entries = len(cache) - cache_entries
    if new_cache_entries > 0:
        print(f"\n📦 Cache atualizado:")
        print(f"   • {new_cache_entries} novas entradas adicionadas")
        print(f"   • Total de entradas: {len(cache)}")

    if not_found_count > 0:
        print(f"\n⚠️  Ativos sem CNPJ encontrado:")
        not_found_df = df[df['CNPJ'] == 'N/A']
        for idx, row in not_found_df.iterrows():
            print(f"   • {row['Ativo']}")

    print(f"\n📋 Primeiras 5 linhas com CNPJ:")
    print("-" * 80)
    display_cols = ['Banco', 'Ativo', 'CNPJ', 'Razao_Social', 'Valor']
    print(df[display_cols].head().to_string(index=False))

    # Estimativa de tempo para próximas execuções
    if found_count > 0 and not test_mode:
        avg_time_per_api_call = 22  # 20s delay + ~2s API
        estimated_time = (total - cached_count - found_count) * avg_time_per_api_call
        estimated_minutes = estimated_time / 60

        print(f"\n⏱️  Estimativa para novos ativos:")
        print(f"   • Ativos já em cache: {len(cache)}")
        print(f"   • Tempo estimado para novos: ~{estimated_minutes:.1f} minutos")
        print(f"   • Próximas execuções serão instantâneas para ativos já processados!")

    print("\n" + "=" * 80)
    print("✅ ENRIQUECIMENTO CONCLUÍDO!")
    print("=" * 80)

    return df


def main():
    """Função principal com argumentos CLI"""

    parser = argparse.ArgumentParser(
        description='Enriquece CSV flat com coluna CNPJ',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python3 enrich_with_cnpj.py                          # Processa todos os ativos
  python3 enrich_with_cnpj.py --test                   # Processa apenas 5 ativos (teste)
  python3 enrich_with_cnpj.py --dry-run                # Simula sem salvar
  python3 enrich_with_cnpj.py --csv custom_file.csv    # Processa arquivo customizado
        """
    )

    parser.add_argument(
        '--csv',
        default='output/investimentos_bradesco_flat.csv',
        help='Caminho do CSV a ser enriquecido (padrão: output/investimentos_bradesco_flat.csv)'
    )

    parser.add_argument(
        '--test',
        action='store_true',
        help='Modo de teste: processa apenas 5 linhas'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simula o processo sem salvar o CSV'
    )

    parser.add_argument(
        '--no-web-search',
        action='store_true',
        help='Desabilita busca web com GPT-4o (mais rápido, mas menos preciso)'
    )

    args = parser.parse_args()

    # Executa enriquecimento
    enrich_csv_with_cnpj(
        csv_path=args.csv,
        test_mode=args.test,
        dry_run=args.dry_run,
        use_web_search=not args.no_web_search
    )


if __name__ == '__main__':
    main()
