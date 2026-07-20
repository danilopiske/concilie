# Changelog

Todas as mudanças notáveis no projeto **Concilie** serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.8.0] - 2026-01-22

### Adicionado
- **Migração Next.js**: Frontend totalmente reescrito em React/Next.js para maior performance e modernidade UI.
- **Backend FastAPI**: API RESTful robusta substituindo o backend monolítico anterior.
- **Distribuição Standalone**: Novo script de build (`build_dist.py`) capaz de gerar um único executável `.exe` contendo Backend + Frontend + Banco de Dados.
- **Support Híbrido DB**: Suporte nativo tanto para SQLite (Portável) quanto MySQL (Servidor).
- **Legado Integration**: Integração do motor de processamento legado (`proc`) dentro da nova arquitetura API para garantir paridade na leitura de arquivos Excel complexos.

### Corrigido
- Correção na leitura de cabeçalhos de arquivos "Rede" (Multisheet) usando a engine legada.
- Resolução de conflitos de path no Windows durante a extração do executável.
- Correção de links quebrados no Dashboard principal.

### Alterado
- Interface de "De-Para" modernizada com validação em tempo real.
- Estrutura de pastas reorganizada para separação clara entre Frontend (`apps/web`) e Backend (`apps/api`).

---

## [1.7.0] - 2025-12-15
*Versão Legada (Python Panel)*

### Adicionado
- Módulo de conciliação bancária inicial.
- Suporte a arquivos OFX.

### Depreciado
- Interface baseada em Panel (substituída na v1.8).
