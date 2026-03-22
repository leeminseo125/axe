# AXEworks Foundation Engine 사용 매뉴얼

**문서 버전**: v1.0
**최종 수정**: 2026-03-22
**개발사**: AXEworks (hello@axeworks.xyz)

---

## 목차

1. [프로젝트 개요](#1-프로젝트-개요)
2. [시스템 요구사항](#2-시스템-요구사항)
3. [설치 및 초기 설정](#3-설치-및-초기-설정)
4. [서비스 구동](#4-서비스-구동)
5. [시스템 아키텍처](#5-시스템-아키텍처)
6. [AXEngine 사용법 (내부 업무 엔진)](#6-axengine-사용법-내부-업무-엔진)
7. [AXE_POE 사용법 (외부 프로덕트 운영 엔진)](#7-axe_poe-사용법-외부-프로덕트-운영-엔진)
8. [Policy Engine 사용법 (정책 및 거버넌스)](#8-policy-engine-사용법-정책-및-거버넌스)
9. [poQat Monitor 사용법 (시스템 건강도 모니터링)](#9-poqat-monitor-사용법-시스템-건강도-모니터링)
10. [Operator Cockpit 대시보드](#10-operator-cockpit-대시보드)
11. [엔진 간 통신 (Inter-Engine Communication)](#11-엔진-간-통신-inter-engine-communication)
12. [Human-in-the-Loop (HITL) 운영 가이드](#12-human-in-the-loop-hitl-운영-가이드)
13. [외부 시스템 연동 가이드](#13-외부-시스템-연동-가이드)
14. [LLM 연동 설정](#14-llm-연동-설정)
15. [데이터베이스 스키마 참조](#15-데이터베이스-스키마-참조)
16. [트러블슈팅](#16-트러블슈팅)
17. [개발 가이드](#17-개발-가이드)

---

## 1. 프로젝트 개요

### AXEworks Foundation Engine이란?

AXEworks Foundation Engine은 **비파괴적 AI 실행(Non-destructive AI Execution)** 아키텍처를 기반으로 설계된 AI 운영 플랫폼입니다. 기존 시스템(ERP, MES, CRM, SaaS 등)을 **절대 수정하거나 교체하지 않고**, 그 위에 독립된 AI 레이어를 구축하여 데이터를 읽고, 해석하고, 판단하고, 실행하고, 학습합니다.

### 핵심 원칙

| 원칙 | 설명 |
|------|------|
| **비파괴적 실행** | 기존 시스템을 직접 수정하지 않음. AI 레이어는 독립적으로 동작 |
| **원상 복구 보장** | AI 레이어 장애 시 원래 시스템은 무영향 |
| **마이크로서비스** | 각 엔진은 독립 서비스로 배포. 장애 격리(Blast Radius) 보장 |
| **신뢰도 기반 실행** | Confidence Score에 따라 자동/수동 실행 분기 |

### 두 개의 핵심 엔진

- **AXEngine**: 내부 업무 시스템(ERP, MES, CRM 등)에 AI를 적용하는 실행 엔진
- **AXE_POE**: 외부 프로덕트(B2C/B2B 서비스)에 대한 AI 운영 엔진

---

## 2. 시스템 요구사항

### 필수 소프트웨어

| 소프트웨어 | 최소 버전 | 용도 |
|-----------|----------|------|
| Docker | 24.0+ | 컨테이너 런타임 |
| Docker Compose | 2.20+ | 멀티 컨테이너 오케스트레이션 |
| Git | 2.30+ | 버전 관리 |
| Node.js | 20.0+ | 프론트엔드 빌드 (로컬 개발 시) |
| Python | 3.10+ | 백엔드 로컬 개발 시 |

### 권장 하드웨어

| 환경 | CPU | RAM | 디스크 |
|------|-----|-----|--------|
| 개발 | 4코어 | 8GB | 20GB |
| 스테이징 | 8코어 | 16GB | 50GB |
| 프로덕션 | 16코어+ | 32GB+ | 100GB+ SSD |

### 선택 사항

| 소프트웨어 | 용도 |
|-----------|------|
| Ollama | 로컬 LLM 추론 (프라이버시 보장) |
| OpenClaw | 레거시 시스템 UI 자동화 |

---

## 3. 설치 및 초기 설정

### 3.1 저장소 클론

```bash
git clone https://github.com/<your-org>/axe.git
cd axe
```

### 3.2 환경 변수 설정

```bash
cp .env.example .env
```

`.env` 파일을 열어 아래 항목들을 실제 값으로 수정합니다:

```bash
# 최소 필수 설정 (LLM API 키 중 하나 이상)
OPENAI_API_KEY="sk-..."
ANTHROPIC_API_KEY="sk-ant-..."

# 또는 로컬 LLM 사용 시 Ollama 엔드포인트
LOCAL_LLM_ENDPOINT="http://host.docker.internal:11434/api/generate"

# 데이터베이스 비밀번호 (프로덕션에서는 반드시 변경)
POSTGRES_PASSWORD="강력한_비밀번호"
JWT_SECRET="랜덤_시크릿_키"
API_KEY_SALT="랜덤_솔트_값"
```

**주의**: `.env` 파일은 절대 Git에 커밋하지 마십시오. `.gitignore`에 이미 포함되어 있습니다.

### 3.3 외부 시스템 연동 (선택)

연동할 레거시 시스템이 있으면 해당 엔드포인트를 설정합니다:

```bash
# AXEngine 연동 대상
ERP_SYSTEM_ENDPOINT="https://your-erp.com/api"
ERP_API_KEY="erp-key"
MES_SYSTEM_ENDPOINT="https://your-mes.com/api"
CRM_SYSTEM_ENDPOINT="https://your-crm.com/api"

# AXE_POE 연동 대상
PRODUCT_DB_ENDPOINT="https://your-product-api.com"
CS_TICKET_SYSTEM_API="https://your-cs-system.com/api"
PAYMENT_GATEWAY_API="https://your-payment.com/api"
```

---

## 4. 서비스 구동

### 4.1 전체 서비스 시작

```bash
docker-compose up --build
```

백그라운드 실행:

```bash
docker-compose up --build -d
```

### 4.2 서비스별 포트 정보

| 서비스 | 포트 | URL |
|--------|------|-----|
| AXEngine | 8001 | http://localhost:8001 |
| AXE_POE | 8002 | http://localhost:8002 |
| Policy Engine | 8003 | http://localhost:8003 |
| poQat Monitor | 8004 | http://localhost:8004 |
| Data Foundation | 8005 | http://localhost:8005 |
| Operator Cockpit | 3000 | http://localhost:3000 |
| PostgreSQL | 5432 | localhost:5432 |
| Redis | 6379 | localhost:6379 |
| Qdrant (벡터 DB) | 6333 | http://localhost:6333 |

### 4.3 서비스 상태 확인

```bash
# 전체 서비스 상태
docker-compose ps

# 개별 서비스 헬스체크
curl http://localhost:8001/health  # AXEngine
curl http://localhost:8002/health  # AXE_POE
curl http://localhost:8003/health  # Policy Engine
curl http://localhost:8004/health  # poQat Monitor
curl http://localhost:8005/health  # Data Foundation
```

### 4.4 서비스 중지

```bash
docker-compose down          # 서비스 중지
docker-compose down -v       # 서비스 중지 + 볼륨(DB 데이터) 삭제
```

### 4.5 개별 서비스 재시작

```bash
docker-compose restart axengine
docker-compose restart axe-poe
```

---

## 5. 시스템 아키텍처

### 3-Layer 구조

```
Layer 3: Agents & Applications
  - Operator Cockpit (대시보드)
  - 채용 에이전트, 보고서 에이전트 등 (확장)

Layer 2: Domain Engine
  - HR, Marketing, Sales 등 도메인별 AI 판단/실행 (확장)

Layer 1: Foundation Engine
  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐
  │  AXEngine   │  │  AXE_POE    │  │ Policy Engine│  │Data Foundation│
  │ (내부 업무) │◄►│ (외부 운영) │  │ (거버넌스)   │  │ (데이터 표준)│
  └──────┬──────┘  └──────┬──────┘  └──────────────┘  └──────────────┘
         │                │              ▲                    ▲
         │                │              │                    │
    ┌────▼────┐     ┌─────▼─────┐       │                    │
    │ERP/MES/ │     │Product DB/│       │                    │
    │CRM 연동 │     │Analytics/ │    poQat Monitor ◄────────┘
    │(읽기전용)│     │CS/Payment │    (품질 검증)
    └─────────┘     └───────────┘
```

### 엔진 간 통신 흐름

1. AXE_POE가 외부 이상을 감지
2. AXEngine의 `/triggers/from-poe` 웹훅으로 점검 요청
3. AXEngine이 내부 시스템 점검 Goal을 자동 생성
4. 결과를 양쪽 대시보드에서 모니터링

---

## 6. AXEngine 사용법 (내부 업무 엔진)

### 6.1 API 기본 URL

```
http://localhost:8001
```

### 6.2 Goal 생성 (비즈니스 목표 입력)

AXEngine의 핵심은 **Goal 기반 오케스트레이션**입니다. 비즈니스 목표를 입력하면 AI가 자동으로 실행 계획을 수립하고 실행합니다.

```bash
# Goal 생성
curl -X POST http://localhost:8001/goals \
  -H "Content-Type: application/json" \
  -d '{
    "title": "월간 ERP 매출 리포트 생성",
    "description": "ERP에서 이번 달 매출 데이터를 수집하고 분석 리포트를 생성하여 경영진에게 배포",
    "priority": 80,
    "created_by": "operations_team"
  }'
```

응답:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "월간 ERP 매출 리포트 생성",
  "status": "pending",
  "priority": 80,
  "created_at": "2026-03-22T09:00:00Z"
}
```

### 6.3 실행 계획 수립 (Plan)

```bash
# Goal을 실행 가능한 단계로 분해
curl -X POST http://localhost:8001/goals/{goal_id}/plan
```

응답 예시:
```json
{
  "id": "plan-uuid",
  "goal_id": "goal-uuid",
  "steps": [
    {"step_index": 0, "group": 0, "action": "fetch_data", "agent": "data_connector", "status": "pending"},
    {"step_index": 1, "group": 1, "action": "analyze_data", "agent": "analytics_agent", "status": "pending"},
    {"step_index": 2, "group": 2, "action": "generate_report", "agent": "report_agent", "status": "pending"},
    {"step_index": 3, "group": 3, "action": "distribute_report", "agent": "notification_agent", "status": "pending"}
  ],
  "status": "planned"
}
```

**참고**: Goal Parser는 LLM을 활용하여 자연어 목표를 분해합니다. LLM이 사용 불가능한 경우 내장 템플릿(`report`, `monitor`, `sync` 패턴)으로 자동 대체됩니다.

### 6.4 계획 실행 (Execute)

```bash
curl -X POST http://localhost:8001/plans/{plan_id}/execute
```

실행 과정:
1. **Executor**가 각 단계를 순차/병렬로 실행
2. **Monitor**가 실시간으로 이상 징후 감지
3. 실패 발생 시 **Re-Planner**가 대안 경로 자동 생성
4. Confidence가 임계값 미만이면 **HITL** 대기 상태로 전환

### 6.5 계획 모니터링

```bash
curl http://localhost:8001/plans/{plan_id}/monitor
```

응답:
```json
{
  "plan_id": "plan-uuid",
  "plan_status": "completed",
  "alerts": [
    {
      "type": "low_confidence",
      "step_index": 1,
      "detail": {"confidence": 0.65, "threshold": 0.80, "action": "analyze_data"}
    }
  ]
}
```

### 6.6 Goal 목록 조회

```bash
# 전체 조회
curl http://localhost:8001/goals

# 상태별 필터
curl http://localhost:8001/goals?status=pending
curl http://localhost:8001/goals?status=planned
curl http://localhost:8001/goals?status=completed
```

### 6.7 커넥터 상태 조회

```bash
# 연동된 커넥터 목록
curl http://localhost:8001/connectors

# 커넥터 건강도
curl http://localhost:8001/connectors/health

# 특정 커넥터로 데이터 조회
curl http://localhost:8001/connectors/erp/fetch?resource=orders
curl http://localhost:8001/connectors/crm/fetch?resource=contacts
```

### 6.8 LLM 직접 호출

```bash
curl -X POST http://localhost:8001/llm/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "이 분기 매출 트렌드를 분석해줘",
    "system": "비즈니스 분석가 역할로 응답하세요",
    "prefer_local": true,
    "require_local": false
  }'
```

LLM 라우팅 우선순위: Ollama(로컬) -> OpenAI -> Anthropic

```bash
# 사용 가능한 LLM 제공자 확인
curl http://localhost:8001/llm/providers
```

---

## 7. AXE_POE 사용법 (외부 프로덕트 운영 엔진)

### 7.1 API 기본 URL

```
http://localhost:8002
```

### 7.2 파이프라인 개요

AXE_POE는 5단계 순환 파이프라인으로 동작합니다:

```
L1 Data Capture (데이터 수집)
  -> L2 Intelligence (해석/분석)
    -> L3 Decision (의사결정)
      -> L4 Execution (실행)
        -> L5 Learning (학습/피드백)
          -> L1으로 순환
```

### 7.3 L1: 데이터 수집 (Data Capture)

#### 웹훅으로 단건 이벤트 수집

```bash
curl -X POST http://localhost:8002/capture/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "source": "analytics",
    "event_type": "user_action",
    "payload": {
      "user_id": "user-123",
      "event_name": "cancel_subscription",
      "timestamp": "2026-03-22T10:00:00Z",
      "properties": {"plan": "pro", "reason": "too_expensive"}
    }
  }'
```

#### 배치 이벤트 수집

```bash
curl -X POST http://localhost:8002/capture/batch \
  -H "Content-Type: application/json" \
  -d '{
    "source": "payments",
    "event_type": "transaction",
    "events": [
      {"id": "tx-1", "user_id": "user-100", "amount": 29.99, "status": "completed"},
      {"id": "tx-2", "user_id": "user-200", "amount": 49.99, "status": "failed"},
      {"id": "tx-3", "user_id": "user-300", "amount": 99.99, "status": "refund"}
    ]
  }'
```

#### 지원하는 소스 유형

| source | 설명 | 주요 정규화 필드 |
|--------|------|-----------------|
| `analytics` | 사용자 행동 데이터 | action, properties |
| `cs_tickets` | 고객 지원 티켓 | subject, priority, status |
| `payments` | 결제 트랜잭션 | amount, currency, status |
| `product_db` | 프로덕트 메트릭 | product_id, metrics |

#### 수집된 이벤트 조회

```bash
# 전체 이벤트
curl http://localhost:8002/events

# 소스별 필터
curl http://localhost:8002/events?source=analytics&limit=20
```

### 7.4 L2: 인텔리전스 (분석/해석)

수집된 이벤트를 분석하여 비즈니스 인사이트를 생성합니다.

```bash
# 최근 60분 이벤트 분석
curl -X POST http://localhost:8002/analyze?window_minutes=60
```

감지하는 패턴:

| 인사이트 유형 | 감지 조건 | 심각도 |
|--------------|----------|--------|
| `volume_spike` | 이벤트 볼륨이 평균의 2배 이상 | warning |
| `volume_drop` | 이벤트 볼륨이 평균의 30% 미만 | warning |
| `churn_signal` | 구독 취소, 다운그레이드 등 이탈 징후 | high |
| `payment_issue` | 결제 실패, 환불, 차지백 | high |
| `cs_escalation` | 긴급/중요 CS 티켓 | high |

```bash
# 인사이트 조회
curl http://localhost:8002/insights
curl http://localhost:8002/insights?severity=high
```

### 7.5 L3: 의사결정 (Decision)

인사이트를 기반으로 최적의 액션을 추천합니다.

```bash
# 미처리 인사이트에 대한 의사결정 생성
curl -X POST http://localhost:8002/decide
```

내장 액션 플레이북:

| 인사이트 | 추천 액션 | 기본 Confidence |
|----------|----------|----------------|
| churn_signal | `trigger_retention_workflow` | 0.80 |
| payment_issue | `handle_payment_failure` | 0.85 |
| cs_escalation | `escalate_cs_ticket` | 0.90 |
| volume_spike | `investigate_volume_spike` | 0.75 |
| volume_drop | `investigate_volume_drop` | 0.70 |

의사결정 상태:
- `proposed`: 제안됨 (검토 필요)
- `approved`: 승인됨 (자동 또는 수동)
- `awaiting_approval`: 정책에 의해 수동 승인 대기
- `blocked`: 정책에 의해 차단됨

```bash
# 의사결정 조회
curl http://localhost:8002/decisions
curl http://localhost:8002/decisions?status=awaiting_approval

# 수동 승인
curl -X POST http://localhost:8002/decisions/{decision_id}/approve
```

### 7.6 L4: 실행 (Execution)

승인된 의사결정을 외부 시스템에 실행합니다.

```bash
# 승인된 의사결정 일괄 실행
curl -X POST http://localhost:8002/execute
```

실행 모듈이 수행하는 작업:
- **리텐션 워크플로우**: CRM에 리텐션 오퍼 발송, CSM 에스컬레이션 생성
- **결제 실패 처리**: 결제 재시도, 고객 알림 발송
- **CS 에스컬레이션**: 시니어 에이전트 재배정, 우선순위 상향
- **볼륨 조사**: AXEngine에 크로스 엔진 트리거 전송

```bash
# 실행 이력 조회
curl http://localhost:8002/executions
curl http://localhost:8002/executions?status=completed
```

### 7.7 L5: 학습 (Learning)

실행 결과를 기반으로 피드백을 축적하고 모델을 개선합니다.

```bash
# 수동 피드백 제출
curl -X POST http://localhost:8002/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "execution_id": "exec-uuid",
    "metric_name": "customer_retained",
    "metric_value": 1.0,
    "feedback_type": "manual",
    "detail": {"note": "고객이 리텐션 오퍼 수락"}
  }'

# 피드백 이력 조회
curl http://localhost:8002/feedback

# 특정 액션의 효과 분석
curl http://localhost:8002/learning/effectiveness/trigger_retention_workflow
```

효과 분석 응답 예시:
```json
{
  "action_type": "trigger_retention_workflow",
  "sample_size": 45,
  "success_rate": 0.82,
  "metrics": {
    "completion_success": {"mean": 0.82, "count": 45},
    "execution_latency_seconds": {"mean": 2.3, "count": 45}
  }
}
```

### 7.8 전체 파이프라인 한 번에 실행

L2 -> L3 -> L4 -> L5 전체를 한 번의 호출로 실행합니다:

```bash
curl -X POST http://localhost:8002/pipeline/run?window_minutes=60
```

응답:
```json
{
  "events_captured": 0,
  "insights_generated": 5,
  "decisions_made": 3,
  "executions_run": 2,
  "feedbacks_recorded": 4
}
```

### 7.9 대시보드 통계

```bash
curl http://localhost:8002/stats
```

---

## 8. Policy Engine 사용법 (정책 및 거버넌스)

### 8.1 API 기본 URL

```
http://localhost:8003
```

### 8.2 정책 생성

정책은 AI 행동의 가드레일입니다. 어떤 액션이 자동 실행 가능하고, 어떤 액션이 승인이 필요한지 규칙을 정의합니다.

```bash
curl -X POST http://localhost:8003/policies \
  -H "Content-Type: application/json" \
  -d '{
    "name": "결제 관련 액션 정책",
    "description": "결제 관련 모든 자동 실행에 0.85 이상의 confidence 필요",
    "domain": "payment_issue",
    "priority": 10,
    "rules": [
      {
        "action_pattern": "handle_payment*",
        "min_confidence": 0.85,
        "require_approval": false,
        "deny": false
      }
    ]
  }'
```

### 8.3 정책 규칙(Rule) 구조

각 정책은 하나 이상의 규칙(rule)을 포함합니다:

| 필드 | 타입 | 설명 |
|------|------|------|
| `action_pattern` | string | 액션 이름 매칭 패턴 (`*`로 와일드카드) |
| `min_confidence` | float | 자동 실행에 필요한 최소 confidence |
| `require_approval` | bool | true면 항상 수동 승인 필요 |
| `deny` | bool | true면 해당 액션 완전 차단 |

#### 정책 규칙 예시

```json
// 모든 액션에 대해 0.80 이상 confidence 요구
{"action_pattern": "*", "min_confidence": 0.80}

// 결제 관련은 무조건 수동 승인
{"action_pattern": "handle_payment*", "require_approval": true}

// 특정 액션 완전 차단
{"action_pattern": "delete_user*", "deny": true}
```

### 8.4 정책 체크 (다른 엔진이 호출)

AXEngine/AXE_POE가 액션 실행 전에 자동으로 호출합니다:

```bash
curl -X POST http://localhost:8003/policies/check \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "handle_payment_failure",
    "domain": "payment_issue",
    "confidence": 0.75
  }'
```

응답:
```json
{
  "allowed": true,
  "requires_approval": true,
  "matched_policies": ["결제 관련 액션 정책"],
  "reason": "Confidence 0.75 below threshold 0.85 in policy '결제 관련 액션 정책'"
}
```

### 8.5 승인 워크플로우

```bash
# 대기 중인 승인 목록
curl http://localhost:8003/approvals?status=pending

# 승인/거절
curl -X POST http://localhost:8003/approvals/{approval_id}/decide \
  -H "Content-Type: application/json" \
  -d '{
    "decided_by": "admin@axeworks.xyz",
    "approve": true,
    "reason": "수동 검토 완료, 실행 승인"
  }'
```

### 8.6 정책 조회

```bash
# 전체 정책
curl http://localhost:8003/policies

# 도메인별 필터
curl http://localhost:8003/policies?domain=payment_issue

# 개별 정책 상세
curl http://localhost:8003/policies/{policy_id}
```

---

## 9. poQat Monitor 사용법 (시스템 건강도 모니터링)

### 9.1 API 기본 URL

```
http://localhost:8004
```

### 9.2 자동 모니터링

poQat Monitor는 **30초 간격**으로 모든 등록된 서비스의 헬스체크를 자동 수행합니다. 별도 설정 없이 docker-compose로 실행하면 즉시 동작합니다.

모니터링 대상:
- AXEngine (http://axengine:8001/health)
- AXE_POE (http://axe-poe:8002/health)
- Policy Engine (http://policy-engine:8003/health)
- Data Foundation (http://data-foundation:8005/health)

### 9.3 시스템 전체 현황 조회

```bash
curl http://localhost:8004/overview
```

응답:
```json
{
  "total_services": 4,
  "healthy_services": 3,
  "degraded_services": 1,
  "unhealthy_services": 0,
  "total_agents": 2,
  "healthy_agents": 2,
  "services": [...],
  "agents": [...]
}
```

### 9.4 수동 리포트 제출

외부 모니터링 도구나 커스텀 에이전트에서 건강도를 직접 보고할 수 있습니다:

```bash
# 서비스 건강도 리포트
curl -X POST http://localhost:8004/services/report \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "custom-etl-service",
    "status": "healthy",
    "latency_ms": 45.2,
    "error_count": 0
  }'

# 에이전트 건강도 리포트
curl -X POST http://localhost:8004/agents/report \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "hr_recruitment_agent",
    "domain": "hr",
    "status": "healthy",
    "tasks_completed": 150,
    "tasks_failed": 3,
    "avg_confidence": 0.87
  }'
```

### 9.5 서비스/에이전트 목록 조회

```bash
curl http://localhost:8004/services
curl http://localhost:8004/agents
```

---

## 10. Operator Cockpit 대시보드

### 10.1 접속

브라우저에서 다음 주소로 접속합니다:

```
http://localhost:3000
```

### 10.2 페이지 구성

| 페이지 | 경로 | 설명 |
|--------|------|------|
| Dashboard | `/` | 전체 시스템 현황 요약. 서비스 건강도, POE 통계, 실패율 |
| AXEngine | `/axengine` | Goal 생성/관리, HITL 통계, 커넥터 상태 |
| AXE_POE | `/poe` | 파이프라인 실행, 인사이트/의사결정 관리, 승인 처리 |
| Policies | `/policies` | 활성 정책 목록, 대기 중인 승인 |
| System Health | `/health` | poQat 서비스/에이전트 건강도 상세 (15초 자동 갱신) |

### 10.3 주요 기능

- **실시간 모니터링**: Dashboard와 Health 페이지는 자동으로 데이터를 갱신합니다 (15~30초)
- **Goal 생성**: AXEngine 페이지에서 직접 비즈니스 Goal을 입력하고 Plan 생성 가능
- **의사결정 승인**: AXE_POE 페이지에서 대기 중인 의사결정을 수동 승인 가능
- **파이프라인 실행**: "Run Pipeline" 버튼으로 POE 전체 파이프라인 즉시 실행

### 10.4 로컬 개발 (프론트엔드)

```bash
cd operator_cockpit
npm install
npm run dev
```

환경 변수로 백엔드 URL을 지정합니다:

```bash
NEXT_PUBLIC_AXENGINE_URL=http://localhost:8001
NEXT_PUBLIC_AXE_POE_URL=http://localhost:8002
NEXT_PUBLIC_POLICY_URL=http://localhost:8003
NEXT_PUBLIC_POQAT_URL=http://localhost:8004
```

---

## 11. 엔진 간 통신 (Inter-Engine Communication)

### 11.1 AXE_POE -> AXEngine 트리거

AXE_POE가 외부 이상을 감지하면 AXEngine에 내부 점검을 요청합니다:

```bash
# AXE_POE의 Execution 모듈이 자동으로 호출하는 API
curl -X POST http://localhost:8001/triggers/from-poe \
  -H "Content-Type: application/json" \
  -d '{
    "source": "axe_poe",
    "trigger_type": "volume_investigation",
    "payload": {
      "source": "analytics",
      "current": 500,
      "average": 100,
      "ratio": 5.0
    },
    "priority": 60
  }'
```

이 API가 호출되면 AXEngine에 자동으로 Goal이 생성됩니다.

### 11.2 통신 흐름 예시: 결제 이상 감지

```
1. [AXE_POE L1] 결제 실패 이벤트 수집
2. [AXE_POE L2] payment_issue 인사이트 생성 (severity: high)
3. [AXE_POE L3] handle_payment_failure 의사결정 생성
4. [Policy Engine] 정책 체크 -> confidence 0.85 이상이면 approved
5. [AXE_POE L4] 결제 재시도 + 고객 알림 실행
6. [AXE_POE L4] AXEngine에 트리거 전송 (내부 점검 요청)
7. [AXEngine] 자동 Goal 생성 -> Plan -> Execute (ERP 정합성 확인)
8. [AXE_POE L5] 실행 결과 피드백 기록 및 학습
```

---

## 12. Human-in-the-Loop (HITL) 운영 가이드

### 12.1 신뢰도(Confidence) 기반 분기

| Confidence 범위 | 동작 |
|----------------|------|
| >= 임계값 (기본 0.80) | 자동 실행 |
| >= 임계값 - 0.15 | 수동 검토 대기 |
| < 임계값 - 0.15 | 차단 |

### 12.2 Confidence 평가 API

```bash
curl -X POST "http://localhost:8001/hitl/evaluate?confidence=0.75&action=analyze_data"
```

응답:
```json
{
  "confidence": 0.75,
  "action": "analyze_data",
  "decision": "needs_review"
}
```

### 12.3 Override (수동 재정의) 기록

AI 판단을 사람이 수정한 경우를 기록합니다:

```bash
curl -X POST http://localhost:8001/hitl/override \
  -H "Content-Type: application/json" \
  -d '{
    "execution_log_id": "log-uuid",
    "original_action": {"action": "send_alert", "target": "team-a"},
    "override_action": {"action": "send_alert", "target": "team-b"},
    "reason": "팀 A가 아닌 팀 B가 담당 부서",
    "overridden_by": "manager@axeworks.xyz"
  }'
```

### 12.4 동적 임계값 자동 조정

시스템은 Override 이력을 분석하여 임계값을 자동 조정합니다:

- **Override 비율 > 20%**: 임계값 상향 (최대 +0.10) -> 더 많은 수동 검토
- **Override 비율 < 5%**: 임계값 하향 (최대 -0.05) -> 더 많은 자동 실행
- **데이터 10건 미만**: 조정하지 않음 (기본값 유지)

### 12.5 HITL 통계 조회

```bash
curl http://localhost:8001/hitl/stats
```

---

## 13. 외부 시스템 연동 가이드

### 13.1 Anti-Corruption Layer 원칙

모든 외부 시스템 연동은 **읽기 전용**입니다. AXEngine의 커넥터는:
- 외부 시스템의 데이터를 **읽기만** 합니다
- 데이터를 **AXEworks 표준 형식(CanonicalRecord)**으로 변환합니다
- 외부 시스템의 스키마나 데이터를 **절대 변경하지 않습니다**

### 13.2 새로운 커넥터 추가 방법

`axengine/integration_layer/` 디렉토리에 새 커넥터를 추가합니다:

```python
# axengine/integration_layer/custom_connector.py

from shared_infra.config import get_settings
from axengine.integration_layer.connector_base import ConnectorBase, CanonicalRecord

settings = get_settings()

class CustomConnector(ConnectorBase):
    def __init__(self):
        super().__init__(
            name="custom",
            endpoint=settings.custom_system_endpoint,  # .env에 추가 필요
            api_key=settings.custom_api_key,
        )

    async def fetch_records(self, resource="items", **kwargs) -> list[CanonicalRecord]:
        if not self.endpoint:
            return []
        data = await self.read(f"/api/{resource}", params=kwargs)
        if "error" in data:
            return []
        records = data if isinstance(data, list) else data.get("items", [])
        return [
            CanonicalRecord(
                source_system="custom",
                source_id=str(r.get("id", "")),
                record_type=resource,
                data=r,
            )
            for r in records
        ]

    async def health_check(self) -> bool:
        if not self.endpoint:
            return False
        result = await self.read("/health")
        return "error" not in result
```

그리고 `connector_registry.py`에 등록합니다:

```python
from axengine.integration_layer.custom_connector import CustomConnector

# ConnectorRegistry.__new__() 내부에 추가
cls._connectors["custom"] = CustomConnector()
```

### 13.3 AXE_POE 데이터 소스 추가

`axe_poe/data_capture/etl_pipeline.py`의 `DataCaptureService.source_configs`에 새 소스를 추가하고, `EventNormalizer.normalize()`에 정규화 로직을 추가합니다.

---

## 14. LLM 연동 설정

### 14.1 LLM 라우팅 우선순위

```
1. Ollama (로컬) - 프라이버시 보장, 네트워크 불필요
2. OpenAI API - 높은 성능, 클라우드 의존
3. Anthropic API - 높은 성능, 클라우드 의존
```

### 14.2 Ollama 설정 (권장)

```bash
# Ollama 설치 (macOS)
brew install ollama

# 모델 다운로드
ollama pull llama3

# 서비스 시작
ollama serve
```

Docker 환경에서 호스트의 Ollama에 접근하려면:
```bash
# .env 파일
LOCAL_LLM_ENDPOINT="http://host.docker.internal:11434/api/generate"
```

### 14.3 사용 가능한 모델 확인

```bash
curl http://localhost:8001/llm/providers
```

### 14.4 로컬 전용 모드

민감한 데이터를 처리할 때는 `require_local: true`로 설정하면 클라우드 API를 사용하지 않습니다:

```bash
curl -X POST http://localhost:8001/llm/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "분석해줘",
    "require_local": true
  }'
```

---

## 15. 데이터베이스 스키마 참조

### 15.1 테이블 목록

모든 테이블은 `ax_` 접두사를 사용하여 기존 데이터베이스와 충돌을 방지합니다.

| 테이블 | 소속 | 설명 |
|--------|------|------|
| `ax_audit_log` | 공통 | 전체 감사 추적 로그 |
| `ax_policies` | Policy Engine | 정책 정의 |
| `ax_approval_workflows` | Policy Engine | 승인 워크플로우 |
| `ax_goals` | AXEngine | 비즈니스 목표 |
| `ax_execution_plans` | AXEngine | 실행 계획 |
| `ax_execution_logs` | AXEngine | 실행 단계별 로그 |
| `ax_hitl_overrides` | AXEngine | HITL 재정의 이력 |
| `ax_poe_data_events` | AXE_POE | 수집된 원시 이벤트 |
| `ax_poe_insights` | AXE_POE | 생성된 인사이트 |
| `ax_poe_decisions` | AXE_POE | 의사결정 기록 |
| `ax_poe_executions` | AXE_POE | 실행 이력 |
| `ax_poe_learning_feedback` | AXE_POE | 학습 피드백 |
| `ax_service_health` | poQat | 서비스 건강도 |
| `ax_agent_health` | poQat | 에이전트 건강도 |

### 15.2 벡터 DB 컬렉션 (Qdrant)

| 컬렉션 | 차원 | 용도 |
|--------|------|------|
| `axengine_knowledge` | 1536 | AXEngine 내부 지식 |
| `poe_playbook` | 1536 | POE 운영 플레이북 |
| `policy_rules` | 1536 | 정책 규칙 벡터 검색 |

### 15.3 직접 DB 접속

```bash
# PostgreSQL 접속
docker-compose exec postgres psql -U axeworks -d axeworks

# 테이블 확인
\dt ax_*

# 감사 로그 조회 예시
SELECT * FROM ax_audit_log ORDER BY timestamp DESC LIMIT 10;
```

---

## 16. 트러블슈팅

### 16.1 서비스가 시작되지 않는 경우

```bash
# 로그 확인
docker-compose logs axengine
docker-compose logs axe-poe

# PostgreSQL 연결 문제
docker-compose logs postgres

# 서비스 재빌드
docker-compose up --build --force-recreate
```

### 16.2 "Policy engine unreachable" 경고

Policy Engine이 아직 시작되지 않았거나 네트워크 문제입니다. 의사결정은 기본 정책(confidence < threshold면 수동 승인)으로 대체되며 시스템은 정상 동작합니다.

### 16.3 LLM이 응답하지 않는 경우

```bash
# Ollama 상태 확인
curl http://localhost:11434/api/tags

# LLM 제공자 확인
curl http://localhost:8001/llm/providers
```

LLM이 모두 사용 불가능해도 시스템은 동작합니다. Goal Parser는 내장 템플릿으로 대체됩니다.

### 16.4 Docker 메모리 부족

`docker-compose.yml`에서 개별 서비스의 메모리 제한을 설정합니다:

```yaml
services:
  axengine:
    deploy:
      resources:
        limits:
          memory: 512M
```

### 16.5 포트 충돌

`.env` 파일에서 포트를 변경합니다:

```bash
AXENGINE_PORT=9001
AXE_POE_PORT=9002
```

### 16.6 데이터 초기화

```bash
# 모든 데이터 삭제 (주의: 되돌릴 수 없음)
docker-compose down -v
docker-compose up --build
```

---

## 17. 개발 가이드

### 17.1 로컬 개발 환경 설정

```bash
# Python 가상환경
python -m venv venv
source venv/bin/activate
pip install -r requirements-base.txt

# 인프라만 Docker로 실행
docker-compose up postgres redis qdrant -d

# 개별 서비스 로컬 실행
uvicorn axengine.main:app --host 0.0.0.0 --port 8001 --reload
uvicorn axe_poe.main:app --host 0.0.0.0 --port 8002 --reload
uvicorn shared_infra.policy_engine.main:app --host 0.0.0.0 --port 8003 --reload

# 프론트엔드 로컬 실행
cd operator_cockpit && npm install && npm run dev
```

### 17.2 새로운 도메인 에이전트 추가 (Layer 2 확장)

1. `axengine/orchestrator/executor.py`에 새 액션 핸들러를 등록합니다:

```python
@register_action("hr_screening")
async def handle_hr_screening(params: dict) -> ExecutionResult:
    # 이력서 스크리닝 로직
    return ExecutionResult(success=True, output={"candidates": [...]}, confidence=0.85)
```

2. Goal Parser 템플릿에 패턴을 추가합니다:

```python
# axengine/orchestrator/goal_parser.py
GOAL_TEMPLATES["recruit"] = [
    ParsedStep(index=0, action="hr_screening", agent="hr_agent"),
    ParsedStep(index=1, action="schedule_interview", agent="hr_agent", dependencies=[0]),
]
```

### 17.3 프로젝트 구조 요약

```
axe/
├── docker-compose.yml          # 전체 서비스 오케스트레이션
├── .env.example                # 환경 변수 템플릿
├── requirements-base.txt       # Python 공통 의존성
├── shared_infra/               # 공통 인프라
│   ├── config.py               # 환경 변수 로딩
│   ├── database.py             # Async DB 엔진
│   ├── redis_client.py         # Redis 클라이언트
│   ├── vector_store.py         # Qdrant 벡터 DB
│   ├── data_foundation/        # 데이터 표준화 서비스
│   │   ├── init.sql            # DB 스키마
│   │   ├── models.py           # SQLAlchemy ORM
│   │   ├── schemas.py          # Pydantic 스키마
│   │   └── main.py             # FastAPI 앱
│   ├── policy_engine/          # 정책 및 거버넌스
│   │   ├── schemas.py
│   │   └── main.py
│   └── poqat_monitor/          # 품질 모니터링
│       ├── schemas.py
│       └── main.py
├── axengine/                   # 내부 업무 AI 엔진
│   ├── main.py                 # FastAPI 앱 (API 진입점)
│   ├── schemas.py
│   ├── orchestrator/           # 4계층 오케스트레이터
│   │   ├── goal_parser.py      # 목표 분해
│   │   ├── planner.py          # 실행 계획 수립
│   │   ├── executor.py         # 실행 엔진
│   │   ├── monitor.py          # 이상 감지
│   │   ├── replanner.py        # 대안 경로 생성
│   │   └── hitl.py             # Human-in-the-Loop
│   ├── integration_layer/      # 외부 시스템 커넥터
│   │   ├── connector_base.py   # Anti-Corruption Layer
│   │   ├── erp_connector.py
│   │   ├── mes_connector.py
│   │   ├── crm_connector.py
│   │   └── connector_registry.py
│   └── local_agent_bridge/     # 로컬 AI 브릿지
│       ├── ollama_client.py    # Ollama 연동
│       ├── openclaw_bridge.py  # UI 자동화 브릿지
│       └── llm_router.py       # LLM 라우팅
├── axe_poe/                    # 외부 프로덕트 AI 운영 엔진
│   ├── main.py                 # FastAPI 앱 (API 진입점)
│   ├── schemas.py
│   ├── data_capture/           # L1 데이터 수집
│   │   └── etl_pipeline.py
│   ├── intelligence_decision/  # L2 분석 + L3 의사결정
│   │   ├── intelligence.py
│   │   └── decision.py
│   └── execution_learning/     # L4 실행 + L5 학습
│       ├── execution.py
│       └── learning.py
└── operator_cockpit/           # 프론트엔드 대시보드
    ├── app/                    # Next.js App Router 페이지
    │   ├── layout.tsx          # 사이드바 포함 레이아웃
    │   ├── page.tsx            # 메인 대시보드
    │   ├── axengine/page.tsx   # AXEngine 관리
    │   ├── poe/page.tsx        # AXE_POE 관리
    │   ├── policies/page.tsx   # 정책 관리
    │   └── health/page.tsx     # 시스템 건강도
    ├── components/shared/      # 재사용 컴포넌트
    └── lib/api.ts              # 백엔드 API 클라이언트
```

---

## 부록: API 빠른 참조

### AXEngine (포트 8001)

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/health` | 헬스체크 |
| GET | `/stats` | 시스템 통계 |
| POST | `/goals` | Goal 생성 |
| GET | `/goals` | Goal 목록 |
| POST | `/goals/{id}/plan` | 실행 계획 수립 |
| POST | `/plans/{id}/execute` | 계획 실행 |
| GET | `/plans/{id}/monitor` | 계획 모니터링 |
| POST | `/hitl/evaluate` | HITL Confidence 평가 |
| POST | `/hitl/override` | HITL Override 기록 |
| GET | `/hitl/stats` | HITL 통계 |
| GET | `/connectors` | 커넥터 목록 |
| GET | `/connectors/health` | 커넥터 건강도 |
| GET | `/connectors/{name}/fetch` | 커넥터 데이터 조회 |
| POST | `/llm/generate` | LLM 생성 요청 |
| GET | `/llm/providers` | LLM 제공자 목록 |
| POST | `/triggers/from-poe` | POE 트리거 수신 |

### AXE_POE (포트 8002)

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/health` | 헬스체크 |
| GET | `/stats` | 대시보드 통계 |
| POST | `/capture/webhook` | 웹훅 이벤트 수집 |
| POST | `/capture/batch` | 배치 이벤트 수집 |
| GET | `/events` | 이벤트 목록 |
| POST | `/analyze` | L2 분석 실행 |
| GET | `/insights` | 인사이트 목록 |
| POST | `/decide` | L3 의사결정 생성 |
| GET | `/decisions` | 의사결정 목록 |
| POST | `/decisions/{id}/approve` | 의사결정 승인 |
| POST | `/execute` | L4 승인된 결정 실행 |
| GET | `/executions` | 실행 이력 |
| POST | `/feedback` | L5 피드백 제출 |
| GET | `/feedback` | 피드백 목록 |
| GET | `/learning/effectiveness/{action}` | 액션 효과 분석 |
| POST | `/pipeline/run` | 전체 파이프라인 실행 |

### Policy Engine (포트 8003)

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/health` | 헬스체크 |
| POST | `/policies` | 정책 생성 |
| GET | `/policies` | 정책 목록 |
| GET | `/policies/{id}` | 정책 상세 |
| POST | `/policies/check` | 정책 체크 |
| POST | `/approvals` | 승인 요청 |
| GET | `/approvals` | 승인 목록 |
| POST | `/approvals/{id}/decide` | 승인/거절 |

### poQat Monitor (포트 8004)

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/health` | 헬스체크 |
| GET | `/overview` | 전체 현황 |
| POST | `/services/report` | 서비스 건강도 보고 |
| GET | `/services` | 서비스 목록 |
| POST | `/agents/report` | 에이전트 건강도 보고 |
| GET | `/agents` | 에이전트 목록 |

---

**AXEworks Foundation Engine** - 비파괴적 AI 실행 아키텍처로 기존 시스템 위에 지능을 더합니다.

문의: hello@axeworks.xyz
