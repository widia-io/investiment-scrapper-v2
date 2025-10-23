#!/usr/bin/env python3
"""
Extrai nomes dos investimentos usando LLM (via OpenRouter)
"""

import pandas as pd
import pdfplumber
import json
import os
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

def extract_pdf_text(pdf_path):
    """Extrai texto completo das páginas 6-7 do PDF"""

    with pdfplumber.open(pdf_path) as pdf:
        text_pages = []

        for page_num in [5, 6]:  # Páginas 6-7 (índice 5-6)
            page = pdf.pages[page_num]
            text = page.extract_text()
            text_pages.append(f"\n=== PÁGINA {page_num + 1} ===\n{text}")

        return '\n'.join(text_pages)


def extract_names_with_llm(pdf_text, csv_path):
    """Usa LLM para extrair os nomes dos 27 investimentos"""

    # Lê o CSV para pegar as primeiras datas de cada investimento
    df = pd.read_csv(csv_path, encoding='utf-8-sig')

    datas_aplicacao = []
    for idx, row in df.iterrows():
        data = row['Data_Aplicacao'] if pd.notna(row['Data_Aplicacao']) else row['Data_Emissao']
        tipo = row['Tipo']
        datas_aplicacao.append(f"{idx+1}. [{tipo}] {data}")

    datas_str = '\n'.join(datas_aplicacao)

    prompt = f"""Você é um especialista em extração de dados financeiros de PDFs.

Analise o texto do relatório de investimentos Bradesco abaixo e extraia o NOME de cada um dos 27 investimentos.

IMPORTANTE:
- Existem exatamente 27 investimentos divididos em seções: PÓS-FIXADO, PRÉ-FIXADO, JURO REAL - INFLAÇÃO, MULTIMERCADOS
- Os nomes podem estar em linhas SEPARADAS dos dados numéricos
- Alguns nomes têm 2 partes (ex: "CRI - BROOKFIELD, VIA PORTFÓLIO" + "GLP" = "CRI - BROOKFIELD, VIA PORTFÓLIO GLP")
- Alguns investimentos NÃO têm nome específico (apenas datas/códigos) - nesses casos retorne null
- Ignore indexadores como "CDI_3 -", "PRE", "IPCA M D" do final dos nomes

ORDEM DOS INVESTIMENTOS (use as datas de aplicação como referência):
{datas_str}

TEXTO DO PDF:
{pdf_text}

Retorne um JSON array com exatamente 27 elementos, na ordem correta:
[
  {{"numero": 1, "tipo": "PÓS-FIXADO", "data_aplicacao": "02/02/24", "nome": "CRI - BROOKFIELD, VIA PORTFÓLIO GLP"}},
  {{"numero": 2, "tipo": "PÓS-FIXADO", "data_aplicacao": "13/06/23", "nome": "CRI - KALLAS INCORPORAÇÕES E CONSTRUÇÕES S.A."}},
  ...
]

RETORNE APENAS O JSON, SEM TEXTO ADICIONAL."""

    # Configura cliente OpenRouter
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY")
    )

    # Modelos disponíveis no OpenRouter (escolha o melhor disponível)
    model = "anthropic/claude-3.5-sonnet"  # Claude Sonnet é excelente para extração estruturada

    print("🤖 Enviando para LLM...")
    print(f"   Modelo: {model}")

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,  # Baixa temperatura para mais precisão
        max_tokens=4000
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
        print(f"Resposta recebida:\n{response_text[:500]}...")
        return None


def main():
    pdf_path = 'input/bradesco-ativos.pdf'
    csv_path = 'output/investimentos_bradesco_estruturado.csv'
    output_csv = 'output/investimentos_bradesco_completo.csv'

    print("=" * 80)
    print("EXTRAÇÃO DE NOMES COM LLM")
    print("=" * 80)

    # Extrai texto do PDF
    print(f"\n📄 Extraindo texto do PDF...")
    pdf_text = extract_pdf_text(pdf_path)
    print(f"✓ {len(pdf_text)} caracteres extraídos")

    # Extrai nomes com LLM
    print(f"\n🤖 Usando LLM para extrair nomes...")
    investments = extract_names_with_llm(pdf_text, csv_path)

    if not investments:
        print("❌ Falha ao extrair nomes com LLM")
        return

    if len(investments) != 27:
        print(f"⚠️  LLM retornou {len(investments)} investimentos, esperado 27")

    print(f"✓ {len(investments)} nomes extraídos pelo LLM")

    # Lê CSV
    df = pd.read_csv(csv_path, encoding='utf-8-sig')

    # Adiciona nomes
    names = [inv.get('nome') for inv in investments]

    if len(names) == len(df):
        df['Nome'] = names
        print("✓ Nomes adicionados com sucesso!")
    else:
        print(f"⚠️  Quantidade diferente: {len(names)} nomes vs {len(df)} registros")
        for i in range(len(df)):
            df.at[i, 'Nome'] = names[i] if i < len(names) else None

    # Reordena colunas
    cols = list(df.columns)
    if 'Nome' in cols:
        cols.remove('Nome')
    cols.insert(1, 'Nome')
    df = df[cols]

    # Salva
    output_path = Path(output_csv)
    df.to_csv(output_path, index=False, encoding='utf-8-sig')

    print(f"\n✓ CSV salvo: {output_path}")

    # Mostra resumo
    print("\n" + "=" * 80)
    print("RESUMO")
    print("=" * 80)

    print(f"\nInvestimentos com nome: {df['Nome'].notna().sum()}/{len(df)}")

    print(f"\n📋 Todos os nomes extraídos pelo LLM:")
    print("-" * 80)
    for idx, row in df.iterrows():
        nome = row['Nome'] if pd.notna(row['Nome']) else "[SEM NOME]"
        print(f"{idx+1:2}. {row['Tipo']:22} | {nome}")

    print("\n" + "=" * 80)
    print("✅ CONCLUÍDO!")
    print("=" * 80)


if __name__ == '__main__':
    main()
