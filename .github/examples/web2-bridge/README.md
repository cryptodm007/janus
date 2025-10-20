# Web2 Bridge — n8n → Janus Gateway

Exemplo de **integração Web2** usando **n8n**:
1. Recebe uma requisição HTTP (Webhook) com parâmetros simples.
2. Monta o envelope MCP-Janus.
3. Envia para o Gateway (`POST /mcp/intent`).
4. Faz polling no `GET /mcp/status/:id` até finalizar.
5. Responde ao chamador com o status final.

## Como usar no n8n
1. Abra seu n8n → **Import** → selecione `n8n-workflow.json`.
2. Edite a variável `GATEWAY_BASE_URL` no *Set* node (ex.: `http://host:8080`).
3. Ative o Workflow.
4. Faça um POST para o webhook exibido pelo n8n com um corpo como:
```json
{
  "id": "demo-web2-123",
  "tokenIn": "USDC",
  "tokenOut": "SOL",
  "amount": "100"
}
