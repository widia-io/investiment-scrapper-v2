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

for package in pdfplumber pandas openai python-dotenv; do
    python3 -c "import ${package//-/_}" 2>/dev/null || {
        echo -e "${YELLOW}⚠️  Instalando $package...${NC}"
        pip3 install -q $package
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
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo -e "║  ${GREEN}✅ Extração concluída com sucesso!${NC}                          ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    echo ""
    echo -e "${GREEN}📁 Arquivos gerados:${NC}"
    echo "   • output/investimentos_bradesco_llm.csv"
    echo "   • output/investimentos_bradesco_llm.json"
    echo ""
else
    echo ""
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo -e "║  ${RED}❌ Erro na extração${NC}                                          ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    exit 1
fi
