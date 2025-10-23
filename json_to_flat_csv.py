#!/usr/bin/env python3
"""
Converte JSON hierárquico para CSV flat no formato:
Banco | Ativo | Preço | Valor | Tipo de Ativo | Categoria | Indexador | Taxa % | Vencimento
"""

import json
import pandas as pd
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


def map_tipo_categoria_with_llm(investments):
    """Usa LLM para mapear Tipo de Ativo e Categoria de forma inteligente"""

    # Prepara lista de investimentos para o LLM analisar
    investment_list = []
    for inv in investments:
        investment_list.append({
            'nome': inv['nome'],
            'tipo_original': inv['tipo_original'],
            'indexador': inv.get('indexador')
        })

    prompt = f"""Analise esta lista de investimentos e categorize cada um.

Para cada investimento, determine:
1. **Tipo de Ativo**: Categoria geral (ex: CRI, CRA, LCI, LCA, Debênture, LIG, Título Público, Fundo)
2. **Categoria**: Sub-categoria mais específica (ex: Crédito Imobiliário, Agronegócio, Bancário, Infraestrutura, Tesouro, Multimercado)

INVESTIMENTOS:
{json.dumps(investment_list, indent=2, ensure_ascii=False)}

REGRAS:
- CRI (Certificado de Recebíveis Imobiliários) → Tipo: CRI, Categoria: Crédito Imobiliário
- CRA (Certificado de Recebíveis do Agronegócio) → Tipo: CRA, Categoria: Agronegócio
- LCI (Letra de Crédito Imobiliário) → Tipo: LCI, Categoria: Crédito Imobiliário
- LCA (Letra de Crédito do Agronegócio) → Tipo: LCA, Categoria: Agronegócio
- DEB INCENTIVADA → Tipo: Debênture, Categoria: Infraestrutura
- LIG (Letra Imobiliária Garantida) → Tipo: LIG, Categoria: Crédito Imobiliário
- NTN-B → Tipo: Título Público, Categoria: Tesouro IPCA+
- KAPITALO/Fundos → Tipo: Fundo, Categoria: Multimercado

Retorne JSON array no formato:
[
  {{
    "nome": "CRI - BROOKFIELD, VIA PORTFÓLIO GLP",
    "tipo_ativo": "CRI",
    "categoria": "Crédito Imobiliário"
  }},
  ...
]

RETORNE APENAS O JSON, SEM TEXTO ADICIONAL."""

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY")
    )

    print("🤖 Usando LLM para mapear tipos e categorias...")

    response = client.chat.completions.create(
        model="anthropic/claude-3.5-sonnet",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=2000
    )

    response_text = response.choices[0].message.content.strip()

    # Remove markdown
    if response_text.startswith('```json'):
        response_text = response_text[7:]
    if response_text.startswith('```'):
        response_text = response_text[3:]
    if response_text.endswith('```'):
        response_text = response_text[:-3]

    response_text = response_text.strip()

    try:
        mappings = json.loads(response_text)
        print(f"✓ {len(mappings)} investimentos categorizados")
        return mappings
    except json.JSONDecodeError as e:
        print(f"❌ Erro ao parsear resposta do LLM: {e}")
        return None


def json_to_flat_csv(json_path, output_csv):
    """Converte JSON hierárquico para CSV flat"""

    print("=" * 80)
    print("CONVERSÃO JSON → CSV FLAT")
    print("=" * 80)

    # Lê JSON
    print(f"\n📄 Lendo JSON: {json_path}")
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Coleta todos os investimentos
    investments = []

    # Renda Fixa
    for secao in ['pos_fixado', 'pre_fixado', 'juro_real_inflacao']:
        if secao in data['renda_fixa']:
            for inv in data['renda_fixa'][secao]:
                inv['tipo_original'] = {
                    'pos_fixado': 'PÓS-FIXADO',
                    'pre_fixado': 'PRÉ-FIXADO',
                    'juro_real_inflacao': 'JURO REAL - INFLAÇÃO'
                }[secao]
                investments.append(inv)

    # Alternativos
    if 'multimercados' in data['alternativos']:
        for inv in data['alternativos']['multimercados']:
            inv['tipo_original'] = 'MULTIMERCADOS'
            investments.append(inv)

    print(f"✓ {len(investments)} investimentos encontrados")

    # Usa LLM para mapear tipos e categorias
    mappings = map_tipo_categoria_with_llm(investments)

    if not mappings or len(mappings) != len(investments):
        print("⚠️  Falha no mapeamento LLM, usando fallback")
        mappings = [{'tipo_ativo': 'N/A', 'categoria': 'N/A'} for _ in investments]

    # Cria mapa nome → categorização
    mapping_dict = {m['nome']: m for m in mappings}

    # Converte para formato flat
    rows = []

    for inv in investments:
        nome = inv.get('nome') or 'Sem nome'

        # Busca categorização do LLM
        cat = mapping_dict.get(nome, {'tipo_ativo': 'N/A', 'categoria': 'N/A'})

        # Extrai dados
        preco = inv['valores'].get('preco_atual')
        valor_bruto = inv['valores'].get('valor_bruto_atual')

        # Indexador e taxa
        indexador = None
        taxa = None

        if inv.get('indexador') and inv['indexador'].get('tipo'):
            idx_obj = inv['indexador']
            indexador = idx_obj.get('tipo')

            # Prioriza taxa_aa, senão usa taxa_emissao
            if idx_obj.get('taxa_aa_pct'):
                taxa = idx_obj['taxa_aa_pct']
            elif idx_obj.get('taxa_emissao_pct'):
                taxa = idx_obj['taxa_emissao_pct']

        # Vencimento
        vencimento = inv['datas'].get('vencimento')

        row = {
            'Banco': 'Bradesco',
            'Ativo': nome,
            'Preço': preco if preco else '',
            'Valor': valor_bruto if valor_bruto else '',
            'Tipo de Ativo': cat['tipo_ativo'],
            'Categoria': cat['categoria'],
            'Indexador': indexador if indexador else '',
            'Taxa %': taxa if taxa else '',
            'Vencimento': vencimento if vencimento else ''
        }

        rows.append(row)

    # Cria DataFrame
    df = pd.DataFrame(rows)

    # Formata valores monetários para formato brasileiro
    def format_valor(v):
        if v == '' or v is None:
            return ''
        try:
            return f"{float(v):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        except:
            return v

    df['Valor'] = df['Valor'].apply(format_valor)

    # Salva CSV
    df.to_csv(output_csv, index=False, encoding='utf-8-sig')

    print(f"\n✓ CSV salvo: {output_csv}")

    # Mostra resumo
    print("\n" + "=" * 80)
    print("RESUMO")
    print("=" * 80)

    print(f"\n📊 Total de investimentos: {len(df)}")

    print(f"\n📋 Por Tipo de Ativo:")
    tipo_counts = df['Tipo de Ativo'].value_counts()
    for tipo, count in tipo_counts.items():
        print(f"   • {tipo}: {count}")

    print(f"\n📋 Por Categoria:")
    cat_counts = df['Categoria'].value_counts()
    for cat, count in cat_counts.items():
        print(f"   • {cat}: {count}")

    print(f"\n💰 Valor Total:")
    total = df['Valor'].str.replace('.', '').str.replace(',', '.').astype(float).sum()
    print(f"   R$ {total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

    print(f"\n📋 Primeiras 5 linhas:")
    print("-" * 80)
    print(df.head().to_string(index=False))

    print("\n" + "=" * 80)
    print("✅ CONVERSÃO CONCLUÍDA!")
    print("=" * 80)

    return df


def main():
    json_path = 'output/investimentos_bradesco_llm.json'
    output_csv = 'output/investimentos_bradesco_flat.csv'

    if not os.path.exists(json_path):
        print(f"❌ Arquivo JSON não encontrado: {json_path}")
        print("Execute primeiro: python3 extract_with_llm_complete.py")
        return

    json_to_flat_csv(json_path, output_csv)


if __name__ == '__main__':
    main()
