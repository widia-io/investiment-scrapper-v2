#!/usr/bin/env python3
"""
Extrai TODOS os dados da tabela de investimentos usando LLM
Abordagem completa: extrai valores, nomes, datas, tudo em um único passo
"""

import json
import os
import pandas as pd
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
import pdfplumber

# Carrega variáveis de ambiente
load_dotenv()


def extract_pdf_text(pdf_path):
    """Extrai texto completo das páginas 6-7 do PDF"""

    with pdfplumber.open(pdf_path) as pdf:
        text_pages = []

        for page_num in [5, 6]:  # Páginas 6-7 (índice 5-6)
            page = pdf.pages[page_num]
            text = page.extract_text()
            text_pages.append(f"\n{'='*80}\n=== PÁGINA {page_num + 1} ===\n{'='*80}\n{text}")

        return '\n'.join(text_pages)


def extract_investments_with_llm(pdf_text):
    """Usa LLM para extrair TODOS os dados dos 27 investimentos"""

    prompt = f"""Você é um especialista em extração de dados financeiros de relatórios PDF.

Analise o texto do relatório de investimentos Bradesco abaixo e extraia TODOS OS DADOS de cada um dos 27 investimentos da tabela "Posição Detalhada dos Investimentos".

ESTRUTURA DA TABELA:

Para RENDA FIXA (PÓS-FIXADO, PRÉ-FIXADO, JURO REAL - INFLAÇÃO):
1. Data de Emissão (dd/mm/aa)
2. Data de Aplicação (dd/mm/aa)
3. Data de Vencimento (dd/mm/aa)
4. Aplicação Inicial R$ (formato: 100.000,00)
5. TX % Emis. (indexador: "CDI -", "PRE", "IPCA", ou vazio)
6. TX % a.a. (número ou vazio)
7. Quantidade (formato: 100,00)
8. Preço Atual (formato: 1.020,84)
9. Valor Bruto Atual (formato: 102.084,44)
10. Impostos (formato: 0,00)
11. Aliq. Atual (formato: 0,00)
12. Valor Líquido Atual (formato: 102.084,44)
13. Part % Prflo (formato: 3,04)
14. Rentabilidade Mês % (formato: 1,45)
15. Rentabilidade Início % (formato: 20,89)

Para MULTIMERCADOS (estrutura DIFERENTE - menos colunas):
1. Data de Emissão (dd/mm/aa) - APENAS UMA DATA
2. Aplicação Inicial R$ (formato: 90.042,67)
3. Quantidade (formato: 84.919,90)
4. Preço Atual (formato: 1,95)
5. Valor Bruto Atual (formato: 165.203,82)
6. Impostos (formato: 818,60)
7. Aliq. Atual (formato: 15,00)
8. Valor Líquido Atual (formato: 164.385,22)
9. Part % Prflo (formato: 4,92)
10. Rentabilidade Mês % (formato: 3,31)
11. Rentabilidade Início % (formato: 83,47)

ATENÇÃO: MULTIMERCADOS NÃO TEM Data de Aplicação, Data de Vencimento, TX % Emis., TX % a.a.!

SEÇÕES:
- PÓS-FIXADO (5 investimentos)
- PRÉ-FIXADO (10 investimentos)
- JURO REAL - INFLAÇÃO (11 investimentos)
- MULTIMERCADOS (1 investimento)

IMPORTANTE:
- NOME pode estar em linha SEPARADA antes ou depois dos dados
- Alguns nomes são multi-linha (ex: "CRI - BROOKFIELD" + "GLP")
- Alguns investimentos NÃO têm nome específico (retorne null)
- Indexador pode ser: CDI, PRE, IPCA, IPCA M D, ou vazio
- Valores em formato brasileiro: use ponto como separador de milhares e vírgula como decimal
- Datas em formato dd/mm/aa (ano com 2 dígitos)

VALIDAÇÃO:
- EXATAMENTE 27 investimentos
- Valor Bruto Total deve ser próximo de R$ 3.190.888,05
- Valor Líquido Total deve ser próximo de R$ 3.189.895,52

TEXTO DO PDF:
{pdf_text}

Retorne um JSON array com EXATAMENTE 27 objetos, um para cada investimento, NA ORDEM que aparecem no PDF:

[
  {{
    "tipo": "PÓS-FIXADO",
    "nome": "CRI - BROOKFIELD, VIA PORTFÓLIO GLP",
    "data_emissao": "02/02/24",
    "data_aplicacao": "02/02/24",
    "data_vencimento": "22/01/29",
    "aplicacao_inicial": "100.000,00",
    "tx_emis": "1,50",
    "indexador": "CDI",
    "tx_aa": null,
    "quantidade": "100,00",
    "preco_atual": "1.020,84",
    "valor_bruto_atual": "102.084,44",
    "impostos": "0,00",
    "aliq_atual": "0,00",
    "valor_liquido_atual": "102.084,44",
    "part_prflo": "3,04",
    "rent_mes": "1,45",
    "rent_inicio": "20,89"
  }},
  ...
]

REGRAS:
- Use null para valores vazios/ausentes
- Mantenha formato brasileiro nos valores (vírgula decimal)
- Retorne APENAS o JSON, sem texto adicional
- Garanta que são exatamente 27 elementos"""

    # Configura cliente OpenRouter
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY")
    )

    model = "anthropic/claude-3.5-sonnet"

    print("🤖 Enviando para LLM...")
    print(f"   Modelo: {model}")
    print(f"   Texto: {len(pdf_text):,} caracteres")

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,
        max_tokens=8000
    )

    response_text = response.choices[0].message.content.strip()

    # Remove markdown code blocks se presentes
    if response_text.startswith('```json'):
        response_text = response_text[7:]
    if response_text.startswith('```'):
        response_text = response_text[3:]
    if response_text.endswith('```'):
        response_text = response_text[:-3]

    response_text = response_text.strip()

    # Parse JSON
    try:
        investments = json.loads(response_text)
        return investments
    except json.JSONDecodeError as e:
        print(f"❌ Erro ao parsear JSON do LLM: {e}")
        print(f"Resposta recebida (primeiros 1000 chars):\n{response_text[:1000]}...")
        return None


def clean_brazilian_number(value):
    """Converte número brasileiro para float"""
    if value is None or value == '':
        return None
    try:
        if isinstance(value, str):
            # Remove pontos (separador de milhares) e troca vírgula por ponto
            return float(value.replace('.', '').replace(',', '.'))
        return float(value)
    except:
        return None


def investments_to_csv(investments, output_path):
    """Converte lista de investimentos para CSV"""

    rows = []
    for inv in investments:
        row = {
            'Tipo': inv['tipo'],
            'Nome': inv.get('nome'),
            'Data_Emissao': inv.get('data_emissao'),
            'Data_Aplicacao': inv.get('data_aplicacao'),
            'Data_Vencimento': inv.get('data_vencimento'),
            'Aplicacao_Inicial_R$': inv.get('aplicacao_inicial'),
            'Indexador': inv.get('indexador'),
            'TX_Emis': inv.get('tx_emis'),
            'TX_aa': inv.get('tx_aa'),
            'Quantidade': inv.get('quantidade'),
            'Preco_Atual': inv.get('preco_atual'),
            'Valor_Bruto_Atual': inv.get('valor_bruto_atual'),
            'Impostos': inv.get('impostos'),
            'Aliq_Atual': inv.get('aliq_atual'),
            'Valor_Liquido_Atual': inv.get('valor_liquido_atual'),
            'Part_Prflo_%': inv.get('part_prflo'),
            'Rent_Mes_%': inv.get('rent_mes'),
            'Rent_Inicio_%': inv.get('rent_inicio'),
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False, encoding='utf-8-sig')

    return df


def investments_to_json(investments, output_path):
    """Converte para JSON hierárquico"""
    from datetime import datetime

    estrutura = {
        'metadata': {
            'data_extracao': datetime.now().isoformat(),
            'fonte': 'LLM Claude 3.5 Sonnet',
            'banco': 'Bradesco',
            'total_investimentos': len(investments)
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

    # Mapeia tipos para seções
    tipo_map = {
        'PÓS-FIXADO': 'pos_fixado',
        'PRÉ-FIXADO': 'pre_fixado',
        'JURO REAL - INFLAÇÃO': 'juro_real_inflacao',
        'MULTIMERCADOS': 'multimercados'
    }

    for inv in investments:
        # Converte data dd/mm/aa para ISO
        def parse_date(date_str):
            if not date_str:
                return None
            try:
                parts = date_str.split('/')
                day, month, year = parts
                if len(year) == 2:
                    year = '20' + year
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            except:
                return None

        obj = {
            'nome': inv.get('nome'),
            'tipo': 'TITULO',
            'datas': {
                'emissao': parse_date(inv.get('data_emissao')),
                'aplicacao': parse_date(inv.get('data_aplicacao')),
                'vencimento': parse_date(inv.get('data_vencimento'))
            },
            'valores': {
                'aplicacao_inicial': clean_brazilian_number(inv.get('aplicacao_inicial')),
                'quantidade': clean_brazilian_number(inv.get('quantidade')),
                'preco_atual': clean_brazilian_number(inv.get('preco_atual')),
                'valor_bruto_atual': clean_brazilian_number(inv.get('valor_bruto_atual')),
                'impostos': clean_brazilian_number(inv.get('impostos')),
                'valor_liquido_atual': clean_brazilian_number(inv.get('valor_liquido_atual'))
            },
            'rentabilidade': {
                'aliquota_atual_pct': clean_brazilian_number(inv.get('aliq_atual')),
                'participacao_portfolio_pct': clean_brazilian_number(inv.get('part_prflo')),
                'mes_pct': clean_brazilian_number(inv.get('rent_mes')),
                'desde_inicio_pct': clean_brazilian_number(inv.get('rent_inicio'))
            }
        }

        # Adiciona indexador se presente
        if inv.get('indexador'):
            obj['indexador'] = {
                'tipo': inv.get('indexador'),
                'taxa_emissao_pct': clean_brazilian_number(inv.get('tx_emis')),
                'taxa_aa_pct': clean_brazilian_number(inv.get('tx_aa'))
            }
        else:
            obj['indexador'] = None

        # Adiciona na seção correta
        tipo = inv['tipo']
        if tipo in tipo_map:
            secao_key = tipo_map[tipo]
            if tipo == 'MULTIMERCADOS':
                estrutura['alternativos'][secao_key].append(obj)
            else:
                estrutura['renda_fixa'][secao_key].append(obj)

    # Calcula totais
    total_bruto = 0
    total_liquido = 0

    for section in ['renda_fixa', 'alternativos']:
        for subsection, investments_list in estrutura[section].items():
            if isinstance(investments_list, list):
                for inv in investments_list:
                    if inv['valores']['valor_bruto_atual']:
                        total_bruto += inv['valores']['valor_bruto_atual']
                    if inv['valores']['valor_liquido_atual']:
                        total_liquido += inv['valores']['valor_liquido_atual']

    estrutura['totais'] = {
        'quantidade_investimentos': len(investments),
        'valor_bruto_total': round(total_bruto, 2),
        'valor_liquido_total': round(total_liquido, 2)
    }

    # Salva JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(estrutura, f, ensure_ascii=False, indent=2)

    return estrutura


def main():
    pdf_path = 'input/bradesco-ativos.pdf'
    output_csv = 'output/investimentos_bradesco_llm.csv'
    output_json = 'output/investimentos_bradesco_llm.json'

    print("=" * 80)
    print("EXTRAÇÃO COMPLETA COM LLM")
    print("=" * 80)

    # Extrai texto do PDF
    print(f"\n📄 Extraindo texto do PDF...")
    pdf_text = extract_pdf_text(pdf_path)
    print(f"✓ {len(pdf_text):,} caracteres extraídos")

    # Extrai com LLM
    print(f"\n🤖 Usando LLM para extrair TODOS os dados...")
    investments = extract_investments_with_llm(pdf_text)

    if not investments:
        print("❌ Falha ao extrair dados com LLM")
        return

    print(f"✓ {len(investments)} investimentos extraídos")

    if len(investments) != 27:
        print(f"⚠️  Atenção: LLM retornou {len(investments)} investimentos, esperado 27")

    # Valida totais
    total_bruto = sum(clean_brazilian_number(inv.get('valor_bruto_atual')) or 0 for inv in investments)
    total_liquido = sum(clean_brazilian_number(inv.get('valor_liquido_atual')) or 0 for inv in investments)

    print(f"\n💰 Validação:")
    print(f"   Valor Bruto Total: R$ {total_bruto:,.2f}")
    print(f"   Valor Líquido Total: R$ {total_liquido:,.2f}")
    print(f"   Esperado Bruto: R$ 3.190.888,05")
    print(f"   Diferença: R$ {abs(total_bruto - 3190888.05):,.2f}")

    # Exporta CSV
    print(f"\n📊 Exportando para CSV...")
    df = investments_to_csv(investments, output_csv)
    print(f"✓ CSV salvo: {output_csv}")

    # Exporta JSON
    print(f"\n📊 Exportando para JSON hierárquico...")
    estrutura = investments_to_json(investments, output_json)
    print(f"✓ JSON salvo: {output_json}")

    # Resumo
    print("\n" + "=" * 80)
    print("RESUMO")
    print("=" * 80)

    print(f"\n📋 Investimentos por tipo:")
    for tipo in ['PÓS-FIXADO', 'PRÉ-FIXADO', 'JURO REAL - INFLAÇÃO', 'MULTIMERCADOS']:
        count = len([inv for inv in investments if inv['tipo'] == tipo])
        print(f"   • {tipo}: {count}")

    print(f"\n📋 Primeiros 5 investimentos:")
    print("-" * 80)
    for i, inv in enumerate(investments[:5], 1):
        nome = inv.get('nome') or '[SEM NOME]'
        valor = inv.get('valor_bruto_atual', '0,00')
        print(f"{i}. [{inv['tipo']:22}] {nome[:50]:50} | R$ {valor}")

    print("\n" + "=" * 80)
    print("✅ EXTRAÇÃO COMPLETA CONCLUÍDA!")
    print("=" * 80)


if __name__ == '__main__':
    main()
