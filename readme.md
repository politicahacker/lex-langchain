# Projeto de Conversação com Lex - Assistente Legislativa

Este projeto utiliza a Langchain e a OpenAI para criar Lex, uma assistente legislativa. Lex é projetada para auxiliar em uma ampla variedade de tarefas legislativas e políticas, e este sistema inclui suporte para carregar e indexar documentos em Weaviate, além de responder perguntas com base nos documentos indexados.

## Dependências

As seguintes dependências são necessárias para executar o projeto:

- langchain
- openai
- google-search-results (opcional)
- unstructured
- tiktoken
- weaviate-client
- pdf2image
- pdfminer.six
- python-dotenv
- twilio
- firebase_admin
- langchain-community

Instale as dependências usando:

```bash
pip install -r requirements.txt
```

## Configuração

Certifique-se de configurar as variáveis de ambiente necessárias:

- `OPENAI_API_KEY`: Sua chave de API OpenAI.
- `WEAVIATE_URL`: A URL para a instância Weaviate.
- `WEAVIATE_API_KEY`: A chave de API para Weaviate.
- `LIBRARY_DIR`: (Opcional) Caminho para a pasta da biblioteca.

## Como Usar

1. **Indexar Documentos**: Utilize a classe `Library` no arquivo `library.py` para indexar documentos em Weaviate.
2. **Iniciar Conversação**: Execute o arquivo principal para iniciar o loop de conversação. Responda às perguntas e digite "Exit" para sair.

## Arquivos Principais

### Código Principal (lex.py)

O código principal configura um agente de conversação, define a memória e as ferramentas, e entra em um loop para processar a entrada do usuário.

### Biblioteca (tools/library.py)

O arquivo `library.py` contém classes e métodos para trabalhar com documentos, incluindo a indexação em Weaviate e a construção de ferramentas para o sistema de conversação.

### Prompts (agents/prompts.py)

Este arquivo define os prompts usados pela assistente Lex, incluindo um PREFIX descritivo sobre a assistente, instruções de FORMAT_INSTRUCTIONS para interação com as ferramentas, e um SUFFIX para controlar a saída.

## Contribuições

Este projeto está aberto a contribuições. Sinta-se à vontade para abrir issues ou pull requests.

## Licença

Ainda não definida.