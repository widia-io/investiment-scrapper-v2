#!/bin/bash
# Wrapper script para extração de investimentos com LLM

set -e

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║       Extrator de Investimentos Bradesco - Solução LLM          ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Verifica Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 não encontrado${NC}"
    exit 1
fi

# Cria e ativa virtual environment
VENV_DIR="venv"
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${BLUE}📦 Criando virtual environment...${NC}"
    python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
echo -e "${GREEN}✓ Virtual environment ativado${NC}"
echo ""

# Verifica .env
if [ ! -f .env ]; then
    echo -e "${RED}❌ Arquivo .env não encontrado${NC}"
    echo ""
    echo "Crie um arquivo .env com:"
    echo "OPENROUTER_API_KEY=sk-or-v1-sua-chave-aqui"
    echo ""
    echo "Obtenha sua chave em: https://openrouter.ai/keys"
    exit 1
fi

# Verifica dependências
echo -e "${BLUE}🔍 Verificando dependências...${NC}"

for package in pdfplumber pandas openai python-dotenv requests; do
    python3 -c "import ${package//-/_}" 2>/dev/null || {
        echo -e "${YELLOW}⚠️  Instalando $package...${NC}"
        pip install -q $package
    }
done

echo -e "${GREEN}✓ Dependências OK${NC}"
echo ""

# Verifica PDF
PDF_FILE="${1:-input/bradesco-ativos.pdf}"

if [ ! -f "$PDF_FILE" ]; then
    echo -e "${RED}❌ PDF não encontrado: $PDF_FILE${NC}"
    echo ""
    echo "Uso: $0 [caminho_para_pdf]"
    exit 1
fi

echo -e "${BLUE}📄 PDF: $PDF_FILE${NC}"
echo ""

# Cria diretório de saída
mkdir -p output

# Executa extração
echo -e "${BLUE}🤖 Iniciando extração com LLM...${NC}"
echo ""

python3 extract_with_llm_complete.py

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ Extração LLM concluída${NC}"
    echo ""

    # Conversão para CSV flat
    echo -e "${BLUE}📊 Convertendo para CSV flat...${NC}"
    echo ""
    python3 json_to_flat_csv.py

    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✓ Conversão concluída${NC}"
        echo ""

        # Aplicação de regras de negócio
        echo -e "${BLUE}📋 Aplicando regras de negócio...${NC}"
        echo ""
        python3 apply_business_rules.py

        if [ $? -eq 0 ]; then
            echo ""
            echo -e "${GREEN}✓ Regras de negócio aplicadas${NC}"
            echo ""

            # Enriquecimento com CNPJ
            echo -e "${BLUE}🏢 Enriquecendo com CNPJs...${NC}"
            echo ""
            python3 enrich_with_cnpj.py

            if [ $? -eq 0 ]; then
                echo ""
                echo "╔══════════════════════════════════════════════════════════════════╗"
                echo -e "║  ${GREEN}✅ Processo completo concluído com sucesso!${NC}                 ║"
                echo "╚══════════════════════════════════════════════════════════════════╝"
                echo ""
                echo -e "${GREEN}📁 Arquivos gerados:${NC}"
                echo "   • output/investimentos_bradesco_llm.csv       (CSV detalhado)"
                echo "   • output/investimentos_bradesco_llm.json      (JSON hierárquico)"
                echo "   • output/investimentos_bradesco_flat.csv      (CSV flat + CNPJ)"
                echo "   • cnpj_cache.json                             (Cache de CNPJs)"
                echo ""
            else
                echo -e "${YELLOW}⚠️  Enriquecimento com CNPJ falhou (CSV flat ainda disponível)${NC}"
            fi
        else
            echo -e "${YELLOW}⚠️  Regras de negócio falharam${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  Conversão para CSV flat falhou${NC}"
    fi
else
    echo ""
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo -e "║  ${RED}❌ Erro na extração${NC}                                          ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    exit 1
fi
