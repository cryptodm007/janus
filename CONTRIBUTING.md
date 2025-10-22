# Contribuindo com o Janus Protocol

## Como participar
1. Fork e crie sua branch (`feature/<nome>`).
2. Faça commits claros e curtos.
3. Rode `pnpm lint` e `pnpm test` antes do PR.
4. Abra um Pull Request para `main`.

## Áreas principais
| Área | Responsável | Descrição |
|------|--------------|-----------|
| Core | Equipe Infra | Motor de execução e fila de tarefas. |
| Bridge | Equipe Blockchain | Comunicação Base↔Solana. |
| AI Layer | Equipe Inteligência | MCP Server, Agentes, Connectores. |
| Contracts | Equipe On-Chain | Smart Contracts (JNS). |
| Docs | Equipe Comunidade | Documentação e exemplos. |

## Padrões de Código
- TypeScript ES2022, Python 3.11+ ou Solidity 0.8.24+.  
- Commits seguem Conventional Commits.  
- Pull Requests devem ter descrição clara e tests verdes.  

## Segurança
- Nunca exponha chaves ou segredos nos PRs.  
- Use variáveis de ambiente (`.env`).  
- Falhas críticas devem ser reportadas em modo privado.

## Créditos
Janus é um projeto coletivo. Toda contribuição relevante é reconhecida no arquivo `AUTHORS.md`.
