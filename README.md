# AXEworks Foundation Engine

**비파괴적 AI 실행(Non-destructive AI Execution) 아키텍처 기반 AI 운영 플랫폼**

기존 시스템(ERP, MES, CRM, SaaS, 프로덕트)을 수정하지 않고, 그 위에 AI가 데이터를 읽고 해석하고 판단하고 실행하고 학습하는 독립된 레이어를 구축합니다.

## Core Engines

| Engine | Description | Port |
|--------|-------------|------|
| **AXEngine** | 내부 업무 시스템 AI 실행 엔진 (Goal-based Orchestration) | 8001 |
| **AXE_POE** | 외부 프로덕트 AI 운영 엔진 (Analyze-Decide-Execute-Learn) | 8002 |
| **Policy Engine** | 정책, 권한, 승인 워크플로우 | 8003 |
| **poQat Monitor** | 시스템 및 에이전트 건강도 모니터링 | 8004 |
| **Data Foundation** | 표준 데이터 스키마 및 감사 로그 | 8005 |
| **Operator Cockpit** | React/Next.js 운영 대시보드 | 3000 |

## Quick Start

```bash
cp .env.example .env
# Edit .env with your API keys
docker-compose up --build
```

Open http://localhost:3000 for the Operator Cockpit dashboard.

## Documentation

전체 사용 매뉴얼은 [manual.md](./manual.md)를 참조하세요.

## Tech Stack

- **Backend**: Python 3.11, FastAPI, SQLAlchemy, LangChain
- **Frontend**: Next.js 14, React 18, TailwindCSS
- **Database**: PostgreSQL 16, Redis 7, Qdrant (Vector DB)
- **AI**: Ollama (Local), OpenAI, Anthropic
- **Infra**: Docker, Docker Compose

## Architecture

```
Layer 3: Operator Cockpit (Dashboard)
Layer 2: Domain Engines (HR, Marketing, Sales - extensible)
Layer 1: AXEngine + AXE_POE + Policy Engine + Data Foundation
```

## License

Proprietary - AXEworks (hello@axeworks.xyz)
