#!/usr/bin/env python3
"""
Biblioteca de funções para busca de CNPJ de empresas.
Implementa busca híbrida: Cache → LLM (normalização) → API Receita Federal
"""

import json
import os
import time
import requests
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Cache file path
CACHE_FILE = 'cnpj_cache.json'

# API endpoints
RECEITA_WS_URL = "https://www.receitaws.com.br/v1/cnpj/{cnpj}"
BRASIL_API_URL = "https://brasilapi.com.br/api/cnpj/v1/{cnpj}"

# Rate limiting
RECEITA_WS_DELAY = 20  # 3 req/min = 20s delay


def load_cache():
    """Carrega cache de CNPJs do arquivo JSON"""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("⚠️  Cache corrompido, criando novo...")
            return {}
    return {}


def save_cache(cache):
    """Salva cache de CNPJs no arquivo JSON"""
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def get_cached_cnpj(nome_ativo, cache):
    """Busca CNPJ no cache local"""
    entry = cache.get(nome_ativo)
    if entry:
        return {
            'cnpj': entry.get('cnpj'),
            'empresa': entry.get('empresa'),
            'source': 'cache'
        }
    return None


def extract_company_name_with_llm(nome_ativo):
    """
    Usa LLM para extrair e normalizar o nome da empresa do ativo.

    Exemplo:
    Input: "CRI - BROOKFIELD, VIA PORTFÓLIO GLP"
    Output: "BROOKFIELD INCORPORACOES BRASIL S.A."
    """

    # Casos especiais que não têm empresa específica
    if not nome_ativo or nome_ativo.strip() == '' or nome_ativo.lower() == 'sem nome':
        return None

    prompt = f"""Extraia o nome completo e oficial da empresa deste ativo financeiro.

ATIVO: "{nome_ativo}"

INSTRUÇÕES:
1. Identifique a empresa emissora do ativo
2. Retorne o nome OFICIAL completo (razão social)
3. Inclua sufixos como S.A., LTDA, etc.
4. Remova prefixos como "CRI -", "CRA -", "DEB -", "LCI -", etc.
5. Se o nome tiver abreviações, tente expandir para o nome completo
6. Se não conseguir identificar a empresa, retorne "NÃO IDENTIFICADO"

EXEMPLOS:
- "CRI - BROOKFIELD, VIA PORTFÓLIO GLP" → "BROOKFIELD INCORPORACOES BRASIL S.A."
- "LCI - BANCO BRADESCO S.A." → "BANCO BRADESCO S.A."
- "DEB INCENTIVADA - ENAUTA PARTICIPACOES S.A." → "ENAUTA PARTICIPACOES S.A."
- "KAPITALO LONG BIASED FIM" → "KAPITALO INVESTIMENTOS LTDA"

Retorne APENAS o nome da empresa, sem texto adicional."""

    try:
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY")
        )

        response = client.chat.completions.create(
            model="anthropic/claude-3.5-sonnet",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=150
        )

        empresa = response.choices[0].message.content.strip()

        # Remove aspas se presentes
        empresa = empresa.strip('"\'')

        if empresa.upper() == "NÃO IDENTIFICADO":
            return None

        return empresa

    except Exception as e:
        print(f"❌ Erro ao extrair nome com LLM: {e}")
        return None


def clean_cnpj(cnpj_str):
    """Remove formatação do CNPJ, mantendo apenas dígitos"""
    if not cnpj_str:
        return None
    return ''.join(filter(str.isdigit, str(cnpj_str)))


def format_cnpj(cnpj_str):
    """Formata CNPJ para padrão XX.XXX.XXX/XXXX-XX"""
    cnpj = clean_cnpj(cnpj_str)
    if not cnpj or len(cnpj) != 14:
        return cnpj
    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"


def search_cnpj_by_name_llm(empresa_nome):
    """
    Usa LLM para buscar o CNPJ mais provável baseado no nome da empresa.
    Retorna uma lista de CNPJs candidatos para tentar.
    """

    if not empresa_nome:
        return []

    prompt = f"""Você é um especialista em empresas brasileiras.

Baseado no nome da empresa abaixo, me forneça o CNPJ (ou os CNPJs mais prováveis se houver múltiplas filiais/holdings).

EMPRESA: "{empresa_nome}"

IMPORTANTE:
- Retorne APENAS os números do CNPJ (14 dígitos)
- Se houver múltiplas empresas com nomes similares, liste até 3 CNPJs
- Se não souber com certeza, retorne "DESCONHECIDO"
- Formato: um CNPJ por linha

Exemplos:
BANCO BRADESCO S.A. → 60746948000112
BROOKFIELD INCORPORACOES BRASIL S.A. → 07114232000119

Retorne apenas os CNPJs (14 dígitos), um por linha, sem texto adicional."""

    try:
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY")
        )

        response = client.chat.completions.create(
            model="anthropic/claude-3.5-sonnet",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=200
        )

        result = response.choices[0].message.content.strip()

        if "DESCONHECIDO" in result.upper():
            return []

        # Extrai CNPJs (14 dígitos)
        cnpjs = []
        for line in result.split('\n'):
            cnpj = clean_cnpj(line.strip())
            if cnpj and len(cnpj) == 14:
                cnpjs.append(cnpj)

        return cnpjs[:3]  # Máximo 3 candidatos

    except Exception as e:
        print(f"❌ Erro ao buscar CNPJ com LLM: {e}")
        return []


def validate_cnpj_receita_ws(cnpj, delay=True):
    """
    Valida e busca dados do CNPJ na API ReceitaWS.

    Args:
        cnpj: CNPJ (apenas dígitos ou formatado)
        delay: Se True, aguarda RECEITA_WS_DELAY segundos (rate limit)

    Returns:
        dict com dados da empresa ou None se não encontrado
    """

    cnpj_limpo = clean_cnpj(cnpj)

    if not cnpj_limpo or len(cnpj_limpo) != 14:
        return None

    try:
        url = RECEITA_WS_URL.format(cnpj=cnpj_limpo)
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()

            # Verifica se não retornou erro
            if data.get('status') == 'ERROR':
                return None

            # Sucesso
            if delay:
                time.sleep(RECEITA_WS_DELAY)

            return {
                'cnpj': format_cnpj(cnpj_limpo),
                'razao_social': data.get('nome'),
                'nome_fantasia': data.get('fantasia'),
                'situacao': data.get('situacao'),
                'source': 'receita_ws'
            }

        elif response.status_code == 429:
            # Rate limit
            print("⏳ Rate limit ReceitaWS - aguardando 60s...")
            time.sleep(60)
            return validate_cnpj_receita_ws(cnpj, delay=False)  # Retry sem delay extra

        return None

    except requests.RequestException as e:
        print(f"⚠️  Erro ReceitaWS: {e}")
        return None


def validate_cnpj_brasil_api(cnpj):
    """
    Valida e busca dados do CNPJ na API BrasilAPI (fallback).

    Args:
        cnpj: CNPJ (apenas dígitos ou formatado)

    Returns:
        dict com dados da empresa ou None se não encontrado
    """

    cnpj_limpo = clean_cnpj(cnpj)

    if not cnpj_limpo or len(cnpj_limpo) != 14:
        return None

    try:
        url = BRASIL_API_URL.format(cnpj=cnpj_limpo)
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()

            return {
                'cnpj': format_cnpj(cnpj_limpo),
                'razao_social': data.get('razao_social'),
                'nome_fantasia': data.get('nome_fantasia'),
                'situacao': data.get('descricao_situacao_cadastral'),
                'source': 'brasil_api'
            }

        return None

    except requests.RequestException as e:
        print(f"⚠️  Erro BrasilAPI: {e}")
        return None


def search_cnpj_complete(nome_ativo, cache, verbose=True):
    """
    Busca completa de CNPJ com estratégia híbrida:
    1. Verifica cache
    2. Usa LLM para extrair nome da empresa
    3. Usa LLM para sugerir CNPJs candidatos
    4. Valida CNPJs nas APIs (ReceitaWS → BrasilAPI)
    5. Salva no cache

    Args:
        nome_ativo: Nome do ativo (ex: "CRI - BROOKFIELD, VIA PORTFÓLIO GLP")
        cache: Dicionário de cache
        verbose: Se True, imprime progresso

    Returns:
        dict com 'cnpj', 'empresa', 'razao_social', 'source' ou None
    """

    if verbose:
        print(f"\n🔍 Buscando CNPJ para: {nome_ativo}")

    # 1. Verifica cache
    cached = get_cached_cnpj(nome_ativo, cache)
    if cached and cached['cnpj']:
        if verbose:
            print(f"   ✓ Cache: {cached['cnpj']}")
        return cached

    # 2. Extrai nome da empresa com LLM
    if verbose:
        print(f"   🤖 Extraindo nome da empresa com LLM...")

    empresa_nome = extract_company_name_with_llm(nome_ativo)

    if not empresa_nome:
        if verbose:
            print(f"   ❌ Não foi possível identificar a empresa")
        return None

    if verbose:
        print(f"   ✓ Empresa identificada: {empresa_nome}")

    # 3. Busca CNPJs candidatos com LLM
    if verbose:
        print(f"   🤖 Buscando CNPJ com LLM...")

    cnpj_candidatos = search_cnpj_by_name_llm(empresa_nome)

    if not cnpj_candidatos:
        if verbose:
            print(f"   ⚠️  LLM não encontrou CNPJ")
        # Tenta buscar por nome na API (não implementado aqui)
        return None

    if verbose:
        print(f"   ✓ {len(cnpj_candidatos)} CNPJ(s) candidato(s) encontrado(s)")

    # 4. Valida cada candidato nas APIs
    for i, cnpj_candidato in enumerate(cnpj_candidatos, 1):
        if verbose:
            print(f"   🌐 Validando candidato {i}/{len(cnpj_candidatos)}: {format_cnpj(cnpj_candidato)}...")

        # Tenta ReceitaWS
        resultado = validate_cnpj_receita_ws(cnpj_candidato)

        # Se falhar, tenta BrasilAPI
        if not resultado:
            resultado = validate_cnpj_brasil_api(cnpj_candidato)

        if resultado:
            # Encontrou e validou!
            if verbose:
                print(f"   ✅ CNPJ validado: {resultado['cnpj']}")
                print(f"   📋 Razão Social: {resultado['razao_social']}")
                print(f"   📍 Situação: {resultado['situacao']}")

            # Salva no cache
            cache[nome_ativo] = {
                'empresa': empresa_nome,
                'cnpj': resultado['cnpj'],
                'razao_social': resultado['razao_social'],
                'situacao': resultado['situacao'],
                'timestamp': datetime.now().isoformat(),
                'source': resultado['source']
            }
            save_cache(cache)

            return {
                'cnpj': resultado['cnpj'],
                'empresa': empresa_nome,
                'razao_social': resultado['razao_social'],
                'situacao': resultado['situacao'],
                'source': resultado['source']
            }

    # Nenhum candidato validado
    if verbose:
        print(f"   ❌ Nenhum CNPJ validado nas APIs")

    return None


def test_cnpj_lookup():
    """Função de teste para validar a biblioteca"""
    print("=" * 80)
    print("TESTE DE BUSCA DE CNPJ")
    print("=" * 80)

    # Carrega cache
    cache = load_cache()

    # Testes
    testes = [
        "CRI - BROOKFIELD, VIA PORTFÓLIO GLP",
        "LCI - BANCO BRADESCO S.A.",
        "KAPITALO LONG BIASED FIM"
    ]

    for teste in testes:
        resultado = search_cnpj_complete(teste, cache, verbose=True)
        print(f"\n{'='*80}")

    print("\n✅ Teste concluído!")
    print(f"📁 Cache salvo em: {CACHE_FILE}")


if __name__ == '__main__':
    test_cnpj_lookup()
