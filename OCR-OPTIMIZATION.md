# Otimização de OCR para Extração de Dados

Este documento apresenta estratégias para melhorar a precisão da extração de dados de PDFs financeiros.

## Problema: PDFs Complexos

PDFs de instituições financeiras geralmente têm:
- Tabelas com múltiplas páginas
- Formatação complexa (linhas, cores, logos)
- Números com formatação específica (R$, %, datas)
- Textos pequenos e densos

## Estratégia 1: Converter PDF para Texto + IA

### Vantagens
- Mais rápido e barato
- Funciona bem com PDFs que têm texto selecionável
- Preserva a estrutura de dados

### Implementação

Adicione um nó **"Execute Command"** antes do **"Call OpenRouter API"**:

```bash
# Extrair texto do PDF usando pdftotext (preserva layout)
pdftotext -layout /data/input/bradesco-ativos.pdf /data/input/bradesco-ativos.txt
```

Depois, modifique o prompt para trabalhar com texto ao invés de PDF:

```json
{
  "model": "mistralai/mistral-large-latest",
  "messages": [
    {
      "role": "user",
      "content": "Extraia os dados desta tabela de investimentos:\n\n{{$node['Read Text File'].json.data}}"
    }
  ]
}
```

## Estratégia 2: Converter PDF para Imagens de Alta Qualidade

### Vantagens
- Modelos de visão funcionam melhor com imagens
- Permite processar cada página separadamente
- Melhor para PDFs escaneados

### Implementação

1. Adicione um nó **"Execute Command"** para converter PDF em imagens:

```bash
# Instalar dependências no container (adicione ao Dockerfile ou execute uma vez)
apk add poppler-utils

# Converter PDF para imagens PNG (300 DPI)
pdftoppm -png -r 300 /data/input/bradesco-ativos.pdf /data/input/page
```

Isso gera: `page-1.png`, `page-2.png`, etc.

2. Adicione um loop para processar cada imagem separadamente

3. Use um modelo com suporte a visão:
   - `mistralai/pixtral-12b-2409`
   - `google/gemini-pro-1.5`
   - `anthropic/claude-3-opus`

## Estratégia 3: OCR Especializado + IA

### Vantagens
- Melhor precisão para tabelas
- Preserva estrutura de células
- Funciona com PDFs escaneados

### Opção A: Google Cloud Vision API

```javascript
// No nó Code, adicione:
const vision = require('@google-cloud/vision');
const client = new vision.ImageAnnotatorClient();

const [result] = await client.documentTextDetection('/data/input/bradesco-ativos.pdf');
const fullTextAnnotation = result.fullTextAnnotation;

return {
  json: {
    text: fullTextAnnotation.text
  }
};
```

### Opção B: AWS Textract

Textract é especializado em documentos financeiros e tabelas.

1. Adicione um nó **"HTTP Request"**:
   - URL: AWS Textract endpoint
   - Envie o PDF
   - Receba JSON estruturado

2. Envie o resultado para Mistral para refinamento

### Opção C: Tesseract OCR

Gratuito e open-source:

```bash
# No container, instale Tesseract
apk add tesseract-ocr tesseract-ocr-data-por

# Converta PDF para imagem e faça OCR
pdftoppm -png -r 300 /data/input/bradesco-ativos.pdf /tmp/page
tesseract /tmp/page-1.png /tmp/output -l por
```

## Estratégia 4: Abordagem Híbrida (Recomendada)

Combine múltiplas técnicas para melhor resultado:

```
1. Extrair texto nativo do PDF (pdftotext)
   ↓
2. Se o texto for ruim, converter para imagens (pdftoppm)
   ↓
3. Fazer OCR das imagens (Tesseract ou Vision API)
   ↓
4. Enviar texto + imagem para modelo de IA
   ↓
5. Modelo de IA extrai e estrutura os dados
   ↓
6. Validar JSON com schema
```

### Implementação no n8n

```javascript
// Nó: Intelligent OCR Strategy
const fs = require('fs');

// Passo 1: Tentar extrair texto nativo
const { exec } = require('child_process');
const pdfText = await new Promise((resolve) => {
  exec('pdftotext -layout /data/input/bradesco-ativos.pdf -', (err, stdout) => {
    resolve(stdout);
  });
});

// Passo 2: Avaliar qualidade do texto
const hasEnoughNumbers = (pdfText.match(/\d+/g) || []).length > 50;
const hasTableStructure = pdfText.includes('|') || pdfText.match(/\s{3,}/g);

let extractionMethod = 'text';
let dataToSend = pdfText;

// Passo 3: Se texto for insuficiente, usar imagem
if (!hasEnoughNumbers || !hasTableStructure) {
  extractionMethod = 'vision';
  // Converter para imagem e codificar em base64
  exec('pdftoppm -png -r 300 /data/input/bradesco-ativos.pdf /tmp/page');
  const imageBuffer = fs.readFileSync('/tmp/page-1.png');
  dataToSend = imageBuffer.toString('base64');
}

return {
  json: {
    method: extractionMethod,
    data: dataToSend
  }
};
```

## Estratégia 5: Prompt Engineering Avançado

### Técnicas de Prompt

#### 1. Few-Shot Learning

Forneça exemplos ao modelo:

```json
{
  "messages": [
    {
      "role": "system",
      "content": "Você é um extrator de dados financeiros. Retorne apenas JSON."
    },
    {
      "role": "user",
      "content": "Exemplo 1: [texto do PDF] -> [JSON esperado]"
    },
    {
      "role": "assistant",
      "content": "[JSON de exemplo]"
    },
    {
      "role": "user",
      "content": "Agora extraia deste PDF: [PDF real]"
    }
  ]
}
```

#### 2. Chain of Thought

Peça ao modelo para pensar em etapas:

```
"Primeiro, identifique as colunas da tabela.
Depois, para cada linha, extraia os valores correspondentes.
Por fim, formate tudo como JSON seguindo este schema: [...]"
```

#### 3. Validação Iterativa

```javascript
// Primeiro passe: Extração
const extraction = await callOpenRouter({
  prompt: "Extraia os dados da tabela..."
});

// Segundo passe: Validação e correção
const validation = await callOpenRouter({
  prompt: `Valide este JSON e corrija erros: ${extraction}

  Verifique:
  1. Todas as datas estão no formato DD/MM/AA?
  2. Todos os números usam ponto como decimal?
  3. Não há campos vazios onde deveria haver dados?
  `
});
```

## Estratégia 6: Modelos Especializados

### Comparação de Modelos

| Modelo | Precisão | Custo | Velocidade | Suporte PDF |
|--------|----------|-------|------------|-------------|
| GPT-4 Vision | ⭐⭐⭐⭐⭐ | 💰💰💰 | 🐢 | ✅ |
| Claude 3 Opus | ⭐⭐⭐⭐⭐ | 💰💰💰 | 🐢 | ✅ |
| Gemini Pro 1.5 | ⭐⭐⭐⭐ | 💰💰 | 🐇 | ✅ |
| Mistral Large | ⭐⭐⭐⭐ | 💰💰 | 🐇 | ⚠️ |
| Pixtral 12B | ⭐⭐⭐ | 💰 | 🐇🐇 | ⚠️ |
| LLaVA (local) | ⭐⭐ | Grátis | 🐢🐢 | ❌ |

### Recomendações

**Para máxima precisão:**
- Claude 3 Opus via OpenRouter
- GPT-4 Vision via OpenAI

**Para balanceado:**
- Gemini Pro 1.5 (melhor custo/benefício)
- Mistral Large

**Para economia:**
- Pixtral 12B
- Gemini Flash 1.5

## Estratégia 7: Pós-Processamento

Adicione validação e limpeza após extração:

```javascript
// Nó: Post-Process JSON
const data = $input.item.json;

// 1. Padronizar datas
data.posicao_detalhada = data.posicao_detalhada.map(item => {
  // Converter DD/MM/AA para YYYY-MM-DD
  if (item.data_vencimento) {
    const [day, month, year] = item.data_vencimento.split('/');
    item.data_vencimento = `20${year}-${month}-${day}`;
  }
  return item;
});

// 2. Limpar valores monetários
data.posicao_detalhada = data.posicao_detalhada.map(item => {
  Object.keys(item).forEach(key => {
    if (typeof item[key] === 'string' && item[key].includes('R$')) {
      item[key] = parseFloat(item[key].replace(/[R$\s.]/g, '').replace(',', '.'));
    }
  });
  return item;
});

// 3. Validar campos obrigatórios
const requiredFields = ['produto', 'valor_liquido_atual', 'data_vencimento'];
data.posicao_detalhada = data.posicao_detalhada.filter(item => {
  return requiredFields.every(field => item[field] != null);
});

return { json: data };
```

## Testes e Benchmarking

Crie um conjunto de testes para avaliar precisão:

```javascript
// test-accuracy.js
const expected = require('./expected-output.json');
const actual = require('./output/latest-extraction.json');

function calculateAccuracy(expected, actual) {
  let correct = 0;
  let total = 0;

  // Comparar cada campo
  expected.posicao_detalhada.forEach((expectedItem, i) => {
    const actualItem = actual.posicao_detalhada[i];

    Object.keys(expectedItem).forEach(key => {
      total++;
      if (String(expectedItem[key]) === String(actualItem[key])) {
        correct++;
      }
    });
  });

  return (correct / total) * 100;
}

const accuracy = calculateAccuracy(expected, actual);
console.log(`Precisão: ${accuracy.toFixed(2)}%`);
```

## Recomendação Final

Para o seu caso (tabelas financeiras do Bradesco):

1. **Primeira tentativa**: Estratégia 4 (Híbrida)
   - Extrair texto nativo
   - Se insuficiente, converter para imagem
   - Usar Gemini Pro 1.5 (bom custo/benefício)

2. **Se precisar de mais precisão**: Estratégia 3 com AWS Textract
   - Especializado em documentos financeiros
   - Detecta tabelas automaticamente

3. **Otimizar custos**: Use caching
   - Salve PDFs já processados
   - Evite reprocessar o mesmo documento

4. **Validação**: Sempre valide o JSON gerado
   - Use schema validation
   - Compare com valores esperados
   - Alerte em caso de anomalias
