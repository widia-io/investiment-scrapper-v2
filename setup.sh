#!/bin/bash

# Script de setup do Investment Scrapper v2

set -e

echo "🚀 Investment Scrapper v2 - Setup"
echo "=================================="
echo ""

# Verificar se Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "❌ Docker não encontrado. Por favor, instale o Docker primeiro."
    echo "   https://docs.docker.com/get-docker/"
    exit 1
fi

# Verificar se Docker Compose está instalado
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose não encontrado. Por favor, instale o Docker Compose primeiro."
    exit 1
fi

echo "✅ Docker encontrado"
echo "✅ Docker Compose encontrado"
echo ""

# Verificar se o arquivo .env existe
if [ ! -f .env ]; then
    echo "❌ Arquivo .env não encontrado!"
    echo "   Por favor, copie .env.example para .env e configure suas variáveis."
    exit 1
fi

# Verificar se a chave da OpenRouter está configurada
if grep -q "your_openrouter_api_key_here" .env; then
    echo "⚠️  ATENÇÃO: Configure sua chave da OpenRouter no arquivo .env"
    echo "   Obtenha em: https://openrouter.ai/keys"
    echo ""
    read -p "Deseja continuar mesmo assim? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "📁 Criando diretórios necessários..."
mkdir -p input output n8n-data workflows

echo "🐳 Iniciando n8n..."
docker-compose up -d

echo ""
echo "⏳ Aguardando n8n inicializar (30 segundos)..."
sleep 30

echo ""
echo "✅ Setup completo!"
echo ""
echo "📝 Próximos passos:"
echo ""
echo "1. Acesse o n8n em: http://localhost:5678"
echo "2. Faça login com as credenciais do arquivo .env"
echo "3. Importe o workflow em: workflows/pdf-extractor-workflow.json"
echo "   - Clique em 'Workflows' > 'Import from File'"
echo "   - Selecione o arquivo workflow"
echo "4. Configure a credencial da OpenRouter:"
echo "   - No workflow, clique no nó 'Call OpenRouter API'"
echo "   - Em 'Credentials', crie uma nova 'Header Auth'"
echo "   - Name: Authorization"
echo "   - Value: Bearer \${OPENROUTER_API_KEY}"
echo "5. Execute o workflow clicando em 'Execute Workflow'"
echo ""
echo "📖 Para mais informações, consulte o README.md"
echo ""
echo "🔍 Ver logs: docker-compose logs -f"
echo "🛑 Parar n8n: docker-compose down"
echo ""
