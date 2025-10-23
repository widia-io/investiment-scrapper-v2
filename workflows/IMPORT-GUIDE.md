# Guia de Importação do Workflow n8n

Este guia mostra como importar e configurar o workflow de extração de PDF no n8n.

## Passo 1: Acessar o n8n

1. Certifique-se que o n8n está rodando:
   ```bash
   docker-compose up -d
   ```

2. Acesse: http://localhost:5678

3. Faça login com as credenciais do arquivo `.env`:
   - Usuário: valor de `N8N_USER` (padrão: `admin`)
   - Senha: valor de `N8N_PASSWORD`

## Passo 2: Importar o Workflow

### Método 1: Importação via Interface

1. No menu lateral, clique em **"Workflows"**
2. Clique no botão **"Import from File"** (ícone de upload)
3. Selecione o arquivo: `workflows/pdf-extractor-workflow.json`
4. Clique em **"Import"**

### Método 2: Copiar e Colar JSON

1. Abra o arquivo `workflows/pdf-extractor-workflow.json` em um editor de texto
2. Copie todo o conteúdo (Ctrl+A, Ctrl+C)
3. No n8n, clique em **"Add Workflow"** > **"Import from URL/JSON"**
4. Cole o JSON (Ctrl+V)
5. Clique em **"Import"**

## Passo 3: Configurar Credenciais da OpenRouter

O workflow precisa de uma credencial para acessar a API da OpenRouter.

### 3.1: Criar a Credencial

1. No workflow importado, clique no nó **"Call OpenRouter API"**
2. Na seção **"Credentials"**, você verá um erro (credencial não encontrada)
3. Clique em **"Create New"**
4. Selecione **"Header Auth"** na lista
5. Preencha:
   - **Credential Name**: `OpenRouter Auth`
   - **Name**: `Authorization`
   - **Value**: `Bearer sk-or-v1-SEU_TOKEN_AQUI`
     - Substitua `SEU_TOKEN_AQUI` pela sua chave real da OpenRouter
     - Ou use: `Bearer {{$env.OPENROUTER_API_KEY}}` para ler do .env (requer restart do container)
6. Clique em **"Save"**

### 3.2: Alternativa - Usar Variável de Ambiente

Para que o n8n leia a chave do arquivo `.env`:

1. Certifique-se que `OPENROUTER_API_KEY` está configurado no `.env`
2. Reinicie o container:
   ```bash
   docker-compose restart
   ```
3. No n8n, use `{{$env.OPENROUTER_API_KEY}}` no valor da credencial

## Passo 4: Verificar o Workflow

O workflow possui os seguintes nós:

```
Manual Trigger → Read PDF File → Prepare Data → Call OpenRouter API → Parse Response → Convert to Binary → Write JSON File
```

### Nós e suas funções:

1. **Manual Trigger**: Permite executar o workflow manualmente
2. **Read PDF File**: Lê o PDF do diretório `/data/input/`
3. **Prepare Data**: Prepara os dados para envio à API
4. **Call OpenRouter API**: Chama o modelo Mistral via OpenRouter
5. **Parse Response**: Extrai e valida o JSON retornado
6. **Convert to Binary**: Converte para arquivo binário
7. **Write JSON File**: Salva o JSON em `/data/output/`

## Passo 5: Executar o Workflow

1. Certifique-se que o arquivo `input/bradesco-ativos.pdf` existe
2. No workflow, clique no botão **"Execute Workflow"** (ou pressione Ctrl+Enter)
3. Aguarde a execução (pode levar 30-60 segundos)
4. Verifique:
   - Todos os nós devem ficar verdes ✅
   - O arquivo JSON será salvo em `output/bradesco-investimentos-YYYY-MM-DD_HH-mm-ss.json`

## Passo 6: Verificar o Resultado

```bash
# Ver o arquivo gerado
ls -lh output/

# Ver o conteúdo
cat output/bradesco-investimentos-*.json | jq .
```

## Troubleshooting

### Erro: "File not found"
- Verifique se o PDF está em `input/bradesco-ativos.pdf`
- Verifique permissões do arquivo: `ls -l input/`

### Erro: "Authentication failed"
- Verifique se a chave da OpenRouter está correta
- Teste a chave manualmente:
  ```bash
  curl https://openrouter.ai/api/v1/auth/key \
    -H "Authorization: Bearer SEU_TOKEN"
  ```

### Erro: "Invalid JSON"
- O modelo pode ter retornado texto ao invés de JSON puro
- Ajuste a temperatura para 0.0 no nó "Call OpenRouter API"
- Melhore o prompt no campo `jsonBody`

### Workflow não executa
- Verifique se há erros nos nós (ícone vermelho ❌)
- Veja os logs do Docker: `docker-compose logs -f n8n`
- Reinicie o n8n: `docker-compose restart`

## Customizações

### Processar múltiplos PDFs

Substitua o nó **"Manual Trigger"** por:
- **"Schedule Trigger"**: Para executar automaticamente (ex: todo dia às 8h)
- **"Webhook"**: Para executar via HTTP request
- **"Watch Folder"**: Para processar novos PDFs automaticamente

### Mudar o modelo de IA

No nó **"Call OpenRouter API"**, altere o campo `model`:
- `mistralai/mistral-large-latest` - Melhor qualidade (mais caro)
- `mistralai/mistral-medium-latest` - Balanceado
- `google/gemini-pro-1.5` - Alternativa com visão
- `anthropic/claude-3-opus` - Melhor precisão (mais caro)

### Adicionar validação de schema

Adicione um nó **"Code"** após **"Parse Response"**:

```javascript
const Ajv = require('ajv');
const ajv = new Ajv();

const schema = {
  type: 'object',
  required: ['extracted_data', 'metadata'],
  properties: {
    extracted_data: {
      type: 'object',
      required: ['posicao_detalhada']
    }
  }
};

const valid = ajv.validate(schema, $input.item.json);
if (!valid) {
  throw new Error('Invalid JSON schema: ' + ajv.errorsText());
}

return $input.item;
```

## Próximos Passos

1. Adicionar notificações (Email, Slack, Discord)
2. Criar dashboard para visualizar investimentos
3. Integrar com Google Sheets ou Excel
4. Adicionar comparação entre extrações diferentes
5. Criar API REST para acesso aos dados
