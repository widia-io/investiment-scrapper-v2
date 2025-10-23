#!/bin/bash
# Script wrapper para extrair investimentos de PDFs do Bradesco

set -e  # Exit on error

echo "=========================================="
echo "  Extrator de Investimentos - Bradesco   "
echo "=========================================="
echo ""

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verifica se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 não encontrado. Por favor, instale Python 3.${NC}"
    exit 1
fi

# Verifica se as dependências estão instaladas
echo "🔍 Verificando dependências..."
python3 -c "import pdfplumber" 2>/dev/null || {
    echo -e "${YELLOW}⚠️  pdfplumber não encontrado. Instalando...${NC}"
    pip3 install pdfplumber
}

python3 -c "import pandas" 2>/dev/null || {
    echo -e "${YELLOW}⚠️  pandas não encontrado. Instalando...${NC}"
    pip3 install pandas
}

echo -e "${GREEN}✓ Dependências OK${NC}"
echo ""

# Verifica se o arquivo PDF existe
PDF_FILE="${1:-input/bradesco-ativos.pdf}"

if [ ! -f "$PDF_FILE" ]; then
    echo -e "${RED}❌ Arquivo PDF não encontrado: $PDF_FILE${NC}"
    echo ""
    echo "Uso: $0 [caminho_para_pdf]"
    echo "Exemplo: $0 input/bradesco-ativos.pdf"
    exit 1
fi

echo "📄 PDF: $PDF_FILE"
echo ""

# Cria diretório de saída se não existir
mkdir -p output

# Executa a extração
echo "🚀 Iniciando extração..."
echo ""

python3 extract_investment_table_final.py

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo -e "${GREEN}✅ Extração concluída com sucesso!${NC}"
    echo "=========================================="
    echo ""

    # Pergunta se quer validar
    read -p "Deseja validar os dados extraídos? (s/n) " -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[Ss]$ ]]; then
        echo ""
        python3 validate_extraction.py
    fi

    echo ""
    echo "📁 Arquivo gerado:"
    echo "   output/investimentos_bradesco_estruturado.csv"
    echo ""
else
    echo ""
    echo "=========================================="
    echo -e "${RED}❌ Erro na extração${NC}"
    echo "=========================================="
    exit $EXIT_CODE
fi
