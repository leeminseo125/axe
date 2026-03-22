# Operator Cockpit 대시보드 사용 매뉴얼

**AXEworks Foundation Engine 운영 대시보드**
버전: v1.0 | 최종 수정: 2026-03-22

---

## 목차

1. [접속 방법](#1-접속-방법)
2. [화면 구성 개요](#2-화면-구성-개요)
3. [사이드바 내비게이션](#3-사이드바-내비게이션)
4. [Dashboard (메인 대시보드)](#4-dashboard-메인-대시보드)
5. [AXEngine 페이지](#5-axengine-페이지)
6. [AXE_POE 페이지](#6-axe_poe-페이지)
7. [Policies 페이지](#7-policies-페이지)
8. [System Health 페이지](#8-system-health-페이지)
9. [상태 배지(Status Badge) 색상 가이드](#9-상태-배지status-badge-색상-가이드)
10. [자동 갱신 주기](#10-자동-갱신-주기)
11. [에러 대응 가이드](#11-에러-대응-가이드)

---

## 1. 접속 방법

### 1.1 URL

```
http://localhost:3000
```

Docker Compose로 전체 시스템을 실행한 후 브라우저에서 위 주소로 접속합니다.

### 1.2 접속 확인

정상 접속 시 왼쪽에 어두운 사이드바, 오른쪽에 메인 콘텐츠 영역이 표시됩니다. 데이터 로딩 중에는 애니메이션이 적용된 스켈레톤 UI가 나타나며, 백엔드 서비스 연결이 완료되면 실제 데이터로 전환됩니다.

### 1.3 권장 환경

| 항목 | 권장 사양 |
|------|----------|
| 브라우저 | Chrome 90+, Firefox 90+, Safari 15+, Edge 90+ |
| 화면 해상도 | 1280x720 이상 (반응형 지원) |
| 네트워크 | 백엔드 API 서버(포트 8001~8005)와 동일 네트워크 |

---

## 2. 화면 구성 개요

전체 화면은 크게 두 영역으로 나뉩니다:

```
+------------------+---------------------------------------------+
|                  |                                             |
|    사이드바       |            메인 콘텐츠 영역                  |
|    (고정 264px)   |            (나머지 전체)                     |
|                  |                                             |
|  - Dashboard     |   선택한 페이지의 내용이 표시됩니다           |
|  - AXEngine      |                                             |
|  - AXE_POE       |   [StatCard] [StatCard] [StatCard] [StatCard]|
|  - Policies      |                                             |
|  - System Health |   +---------------------------------------+ |
|                  |   |          데이터 테이블/패널             | |
|                  |   +---------------------------------------+ |
+------------------+---------------------------------------------+
```

### UI 공통 컴포넌트

| 컴포넌트 | 설명 |
|---------|------|
| **StatCard** | 핵심 수치를 표시하는 카드. 왼쪽에 색상 바가 있으며 제목, 수치, 부제목으로 구성 |
| **StatusBadge** | 상태를 색상으로 구분하는 둥근 배지 (healthy, failed, pending 등) |
| **DataTable** | 데이터 목록을 행/열로 표시하는 테이블. 데이터가 없으면 안내 메시지 표시 |

---

## 3. 사이드바 내비게이션

화면 왼쪽 고정 사이드바에는 5개의 메뉴가 있습니다:

| 메뉴 | 경로 | 설명 |
|------|------|------|
| **Dashboard** | `/` | 전체 시스템 현황 요약 |
| **AXEngine** | `/axengine` | 내부 업무 엔진 관리 (Goal 생성/실행) |
| **AXE_POE** | `/poe` | 외부 프로덕트 운영 파이프라인 관리 |
| **Policies** | `/policies` | 정책 목록 및 승인 대기 워크플로우 |
| **System Health** | `/health` | poQat 기반 서비스/에이전트 건강도 모니터링 |

사이드바 상단에는 **AXEworks** 로고와 버전 정보가, 하단에는 프로젝트명이 표시됩니다.

메뉴 항목에 마우스를 올리면 배경색이 변경되며, 클릭하면 해당 페이지로 이동합니다.

---

## 4. Dashboard (메인 대시보드)

**경로**: `/`
**자동 갱신**: 30초 간격

메인 대시보드는 AXEngine, AXE_POE, poQat의 핵심 지표를 한 화면에서 종합적으로 보여줍니다.

### 4.1 상단 통계 카드 (4개)

페이지 상단에 4개의 StatCard가 한 줄로 배치됩니다:

| 카드 | 색상 | 데이터 소스 | 설명 |
|------|------|------------|------|
| **Services Health** | 초록 | poQat Monitor | `정상 서비스 수 / 전체 서비스 수` 형태로 표시. 예: `4/4` |
| **Events (24h)** | 시안 | AXE_POE | 최근 24시간 동안 수집된 데이터 이벤트 수 |
| **Pending Decisions** | 노랑 | AXE_POE | 현재 승인 대기 중이거나 검토가 필요한 의사결정 수 |
| **Failure Rate (1h)** | 초록/빨강 | AXEngine | 최근 1시간 실행 실패율. 10% 초과 시 빨간색, 이하면 초록색 |

### 4.2 엔진 상태 패널 (2개)

중간 영역에 2개의 패널이 좌우로 배치됩니다:

#### AXEngine (Internal Ops) 패널
- **LLM Providers**: 현재 사용 가능한 LLM 제공자 목록 (예: `ollama, openai`). 없으면 `None available`
- **Connectors**: 등록된 커넥터 목록 (예: `erp, mes, crm`)
- **Failure Rate**: 최근 1시간 실패율 (퍼센트)

#### AXE_POE (Product Ops) 패널
- **Events (24h)**: 24시간 이벤트 수집량
- **Insights (24h)**: 24시간 생성된 인사이트 수
- **Executions (24h)**: 24시간 실행된 액션 수
- **Pending Decisions**: 승인 대기 중인 의사결정 수 (노란색 강조)

### 4.3 Service Health 테이블

하단에 poQat Monitor가 수집한 서비스 건강도 테이블이 표시됩니다:

| 열 | 설명 |
|----|------|
| **Service** | 서비스 이름 (axengine, axe-poe, policy-engine, data-foundation) |
| **Status** | 상태 배지 (healthy / degraded / unhealthy) |
| **Latency** | 응답 지연시간 (밀리초). 예: `45ms` |

### 4.4 에러 배너

백엔드 API 호출 실패 시 페이지 상단에 **빨간색 에러 배너**가 표시됩니다. 에러 메시지가 포함되며, 다음 갱신 주기(30초)에 자동으로 재시도합니다.

---

## 5. AXEngine 페이지

**경로**: `/axengine`
**자동 갱신**: 없음 (수동 조작 시 자동 새로고침)

내부 업무 AI 엔진을 관리하는 페이지입니다. Goal 생성, 실행 계획 수립, HITL 통계를 확인할 수 있습니다.

### 5.1 상단 통계 카드 (3개)

| 카드 | 색상 | 설명 |
|------|------|------|
| **HITL Overrides** | 노랑 | 사람이 AI 판단을 수동으로 변경(Override)한 총 횟수. 부제목에 현재 Confidence 임계값 표시 (예: `Threshold: 0.8`) |
| **Active Connectors** | 시안 | 현재 정상 연결된 커넥터 수. 부제목에 전체 설정된 커넥터 수 표시 (예: `3 configured`) |
| **Total Goals** | 파랑 | 생성된 전체 Goal 수. 부제목에 대기 중인 Goal 수 표시 (예: `2 pending`) |

### 5.2 Integration Connectors 패널

등록된 각 커넥터(ERP, MES, CRM)의 연결 상태를 시각적으로 표시합니다:

- **초록색 점**: 연결 정상 (healthy)
- **빨간색 점**: 연결 실패 (unhealthy)

각 커넥터 이름은 대문자로 표시됩니다 (예: `ERP`, `MES`, `CRM`).

### 5.3 Create Goal 폼

새로운 비즈니스 목표를 생성하는 입력 폼입니다:

| 필드 | 필수 여부 | 설명 |
|------|----------|------|
| **Goal title** | 필수 | 달성하려는 비즈니스 목표 (예: "월간 ERP 매출 리포트 생성") |
| **Description** | 선택 | 목표에 대한 상세 설명 |

**사용 방법**:
1. "Goal title" 입력란에 목표를 입력합니다
2. 필요 시 "Description" 입력란에 상세 설명을 추가합니다
3. `Create` 버튼을 클릭합니다
4. 생성 완료 시 입력 폼이 초기화되고 하단 테이블에 새 Goal이 나타납니다

### 5.4 Goals 테이블

생성된 모든 Goal을 표시하는 테이블입니다:

| 열 | 설명 |
|----|------|
| **Goal** | 목표 제목 |
| **Status** | 현재 상태 배지 (pending, planned, executing, completed, failed) |
| **Priority** | 우선순위 (숫자가 높을수록 우선) |
| **Created** | 생성 날짜 |
| **Actions** | 실행 가능한 버튼 |

**Actions 열의 버튼**:

| 버튼 | 표시 조건 | 동작 |
|------|----------|------|
| `Plan` | status가 `pending`일 때 | 클릭하면 AI가 해당 Goal을 분석하여 실행 계획을 수립합니다. 완료 후 status가 `planned`로 변경됩니다 |

### 5.5 운영 워크플로우

대시보드에서의 일반적인 작업 흐름:

```
1. Create Goal 폼에서 목표 입력 -> Create 클릭
2. Goals 테이블에서 해당 Goal의 Plan 버튼 클릭
3. AI가 Goal을 분석하고 실행 단계를 생성
4. (이후 실행은 API를 통해 진행: POST /plans/{id}/execute)
```

---

## 6. AXE_POE 페이지

**경로**: `/poe`
**자동 갱신**: 없음 (수동 조작 시 자동 새로고침)

외부 프로덕트 AI 운영 파이프라인을 관리하는 페이지입니다. L1~L5 전체 파이프라인을 실행하고, 인사이트 확인 및 의사결정 승인 처리를 할 수 있습니다.

### 6.1 페이지 헤더

- **제목**: "AXE_POE - Product Operations"
- **부제목**: "Analyze - Decide - Execute - Learn Pipeline"
- **Run Pipeline 버튼**: 우측 상단에 보라색 버튼으로 배치

### 6.2 Run Pipeline 버튼

페이지 우측 상단의 보라색 `Run Pipeline` 버튼을 클릭하면:

1. 버튼 텍스트가 `Running...`으로 변경되고 비활성화됩니다
2. 최근 60분의 이벤트를 대상으로 L2->L3->L4->L5 전체 파이프라인이 실행됩니다
3. 완료 시 **파이프라인 결과 배너**가 표시됩니다:

```
Pipeline completed: 5 insights, 3 decisions, 2 executions, 4 feedbacks
```

배너 색상은 시안(cyan)이며, 실행 결과 요약 수치를 보여줍니다:
- **insights**: L2에서 생성된 인사이트 수
- **decisions**: L3에서 생성된 의사결정 수
- **executions**: L4에서 실행된 액션 수
- **feedbacks**: L5에서 기록된 피드백 수

### 6.3 상단 통계 카드 (4개)

| 카드 | 색상 | 설명 |
|------|------|------|
| **Events (24h)** | 시안 | 최근 24시간 수집된 데이터 이벤트 수 |
| **Insights (24h)** | 파랑 | 최근 24시간 생성된 인사이트 수 |
| **Pending Decisions** | 노랑 | 현재 승인/검토 대기 중인 의사결정 수 |
| **Executions (24h)** | 초록 | 최근 24시간 실행된 액션 수 |

### 6.4 Recent Insights 테이블

AI가 분석하여 생성한 인사이트 목록입니다:

| 열 | 설명 |
|----|------|
| **Type** | 인사이트 유형 (volume_spike, churn_signal, payment_issue, cs_escalation 등) |
| **Severity** | 심각도 배지 (info, warning, high, critical) |
| **Summary** | 인사이트 요약 설명 (예: "Event volume for 'analytics' is 3.2x above average") |
| **Time** | 생성 시각 |

### 6.5 Decisions 테이블

인사이트 기반으로 생성된 의사결정 목록입니다:

| 열 | 설명 |
|----|------|
| **Action** | 추천된 액션 이름 (예: trigger_retention_workflow, handle_payment_failure) |
| **Confidence** | AI의 확신도 (0~100%). 80% 이상이면 **초록색**, 미만이면 **노란색** |
| **Status** | 현재 상태 배지 |
| **Actions** | 승인 버튼 (해당되는 경우) |

**Status별 의미**:

| Status | 의미 | Actions 열 |
|--------|------|-----------|
| `proposed` | AI가 제안함, 검토 필요 | `Approve` 버튼 표시 |
| `awaiting_approval` | 정책에 의해 수동 승인 대기 | `Approve` 버튼 표시 |
| `approved` | 승인됨, 실행 대기/완료 | 버튼 없음 |
| `blocked` | 정책에 의해 차단됨 | 버튼 없음 |

**Approve 버튼 사용법**:
1. `proposed` 또는 `awaiting_approval` 상태의 의사결정에서 `Approve` 버튼 클릭
2. 해당 의사결정이 `approved` 상태로 전환됩니다
3. 다음 `Run Pipeline` 실행 시 또는 별도 Execute 호출 시 실제 액션이 수행됩니다

### 6.6 일반적인 운영 흐름

```
1. 외부 시스템에서 데이터가 웹훅/배치로 수집됨 (L1)
2. Run Pipeline 클릭 -> 분석(L2) -> 의사결정 생성(L3)
3. Decisions 테이블에서 제안된 액션 검토
4. 적절한 의사결정에 Approve 클릭
5. 다시 Run Pipeline 클릭 -> 승인된 결정 실행(L4) -> 피드백 기록(L5)
6. 통계 카드에서 처리 결과 확인
```

---

## 7. Policies 페이지

**경로**: `/policies`
**자동 갱신**: 없음 (페이지 로드 시 1회 조회)

AI 행동을 통제하는 정책 규칙과 승인 대기 중인 워크플로우를 확인하는 페이지입니다.

### 7.1 Active Policies 테이블

현재 활성화된 정책 목록입니다:

| 열 | 설명 |
|----|------|
| **Policy Name** | 정책 이름 (예: "결제 관련 액션 정책") |
| **Domain** | 적용 도메인 (예: global, payment_issue, churn_signal) |
| **Priority** | 우선순위 (숫자가 낮을수록 먼저 적용) |
| **Status** | 활성/비활성 상태 배지. 활성이면 `healthy`(초록), 비활성이면 `degraded`(노랑) |

정책이 없으면 "No policies configured" 메시지가 표시됩니다.

> **참고**: 정책 생성/수정은 현재 API를 통해서만 가능합니다. 대시보드는 조회 전용입니다.
> 정책 생성: `POST http://localhost:8003/policies` (상세 방법은 manual.md 8장 참고)

### 7.2 Pending Approvals 테이블

현재 승인 대기 중인 워크플로우 목록입니다:

| 열 | 설명 |
|----|------|
| **Action** | 승인이 필요한 액션 유형 |
| **Status** | 현재 상태 배지 (pending, approved, rejected) |
| **Requested** | 승인 요청 시각 (날짜 + 시간) |

승인 대기 항목이 없으면 "No pending approvals" 메시지가 표시됩니다.

> **참고**: 승인/거절 처리는 현재 API를 통해서만 가능합니다.
> 승인: `POST http://localhost:8003/approvals/{id}/decide`

---

## 8. System Health 페이지

**경로**: `/health`
**자동 갱신**: 15초 간격

poQat Monitor가 수집한 시스템 건강도를 실시간으로 모니터링하는 페이지입니다. 전체 페이지 중 가장 짧은 갱신 주기(15초)를 가집니다.

### 8.1 상단 통계 카드 (4개)

| 카드 | 색상 | 설명 |
|------|------|------|
| **Total Services** | 파랑 | 모니터링 대상 전체 서비스 수 |
| **Healthy** | 초록 | 정상 상태 서비스 수 |
| **Degraded** | 노랑 | 성능 저하 상태 서비스 수 |
| **Unhealthy** | 빨강 | 장애 상태 서비스 수 |

**정상 운영 시** Total Services와 Healthy의 값이 동일해야 합니다. Degraded나 Unhealthy 값이 0보다 크면 즉시 확인이 필요합니다.

### 8.2 Services 테이블

각 서비스의 상세 건강도 정보입니다:

| 열 | 설명 |
|----|------|
| **Service** | 서비스 이름 |
| **Status** | 상태 배지 (healthy / degraded / unhealthy) |
| **Latency** | 헬스체크 응답 지연시간 (밀리초). `--`이면 측정 불가 |
| **Errors** | 에러 발생 횟수. 0보다 크면 **빨간색**으로 표시 |
| **Last Check** | 마지막 헬스체크 시각 |

모니터링 대상 서비스:
- axengine
- axe-poe
- policy-engine
- data-foundation

### 8.3 Agents 테이블

등록된 AI 에이전트의 건강도 정보입니다:

| 열 | 설명 |
|----|------|
| **Agent** | 에이전트 이름 |
| **Domain** | 소속 도메인 (hr, marketing, sales 등) |
| **Status** | 상태 배지 |
| **Completed** | 완료한 작업 수 |
| **Failed** | 실패한 작업 수. 0보다 크면 **빨간색**으로 표시 |
| **Avg Confidence** | 평균 Confidence 점수 (퍼센트). `--`이면 데이터 없음 |

### 8.4 이상 징후 확인 포인트

| 확인 항목 | 정상 | 주의 | 위험 |
|----------|------|------|------|
| Unhealthy 서비스 수 | 0 | - | 1 이상 |
| Degraded 서비스 수 | 0 | 1 이상 | - |
| 서비스 Latency | < 100ms | 100~500ms | > 500ms |
| 에이전트 Failed 수 | 0 | 1~5 | 5 이상 |
| 에이전트 Avg Confidence | > 80% | 65~80% | < 65% |

---

## 9. 상태 배지(Status Badge) 색상 가이드

대시보드 전체에서 사용되는 상태 배지의 색상과 의미입니다:

### 시스템/서비스 상태

| 배지 | 색상 | 의미 |
|------|------|------|
| `healthy` | 초록 | 정상 동작 중 |
| `degraded` | 노랑 | 성능 저하 또는 부분 장애 |
| `unhealthy` | 빨강 | 장애 또는 응답 없음 |

### 작업/실행 상태

| 배지 | 색상 | 의미 |
|------|------|------|
| `pending` | 회색 | 대기 중, 아직 처리되지 않음 |
| `planned` | 시안 | 실행 계획이 수립됨 |
| `running` | 파랑 | 현재 실행 중 |
| `executing` | 노랑 | 실행 진행 중 |
| `completed` | 초록 | 성공적으로 완료 |
| `failed` | 빨강 | 실행 실패 |

### 의사결정 상태

| 배지 | 색상 | 의미 |
|------|------|------|
| `proposed` | 시안 | AI가 제안함, 검토 필요 |
| `approved` | 초록 | 승인됨, 실행 가능 |
| `awaiting_approval` | 노랑 | 정책에 의해 수동 승인 대기 |
| `blocked` | 빨강 | 정책에 의해 차단됨 |

---

## 10. 자동 갱신 주기

각 페이지의 데이터 자동 갱신 주기입니다:

| 페이지 | 갱신 주기 | 설명 |
|--------|----------|------|
| Dashboard (`/`) | **30초** | AXEngine 통계, POE 통계, 서비스 건강도 동시 갱신 |
| AXEngine (`/axengine`) | **수동** | Goal 생성, Plan 실행 등 사용자 조작 시 해당 데이터만 새로고침 |
| AXE_POE (`/poe`) | **수동** | Run Pipeline 실행, Approve 클릭 시 해당 데이터만 새로고침 |
| Policies (`/policies`) | **수동** | 페이지 최초 로드 시 1회 조회 |
| System Health (`/health`) | **15초** | 가장 빈번한 갱신. 서비스/에이전트 건강도 실시간 추적 |

**수동 갱신이 필요한 경우**: 브라우저에서 `F5` 또는 `Cmd+R`로 페이지를 새로고침하면 최신 데이터를 즉시 조회합니다.

---

## 11. 에러 대응 가이드

### 11.1 "API error" 에러 배너가 표시되는 경우

**원인**: 백엔드 서비스가 응답하지 않거나 네트워크 연결 문제

**조치**:
1. 터미널에서 서비스 상태 확인:
   ```bash
   docker-compose ps
   ```
2. 중지된 서비스가 있으면 재시작:
   ```bash
   docker-compose restart axengine axe-poe
   ```
3. 30초 후 대시보드가 자동으로 재시도합니다

### 11.2 모든 StatCard가 "--"으로 표시되는 경우

**원인**: 백엔드 API 서버가 아직 시작되지 않았거나 DB 연결 실패

**조치**:
1. 서비스 로그 확인:
   ```bash
   docker-compose logs axengine --tail 20
   docker-compose logs axe-poe --tail 20
   ```
2. PostgreSQL 상태 확인:
   ```bash
   docker-compose logs postgres --tail 10
   ```
3. 모든 서비스 재시작:
   ```bash
   docker-compose down && docker-compose up -d
   ```

### 11.3 System Health 테이블이 비어있는 경우

**원인**: poQat Monitor가 아직 첫 번째 헬스체크를 수행하지 않음 (시작 후 최대 30초 소요)

**조치**: 30초~1분 대기 후 페이지 새로고침. poQat Monitor는 30초마다 자동으로 모든 서비스를 체크합니다.

### 11.4 특정 서비스가 계속 unhealthy인 경우

**조치**:
1. 해당 서비스 로그 확인:
   ```bash
   docker-compose logs {service-name} --tail 30
   ```
2. 서비스 단독 재시작:
   ```bash
   docker-compose restart {service-name}
   ```
3. 의존성 서비스(postgres, redis, qdrant) 상태 확인:
   ```bash
   docker-compose ps postgres redis qdrant
   ```

### 11.5 대시보드 자체가 접속되지 않는 경우

**조치**:
1. Operator Cockpit 컨테이너 확인:
   ```bash
   docker-compose logs operator-cockpit --tail 20
   ```
2. 포트 3000 사용 여부 확인:
   ```bash
   lsof -i :3000
   ```
3. 컨테이너 재시작:
   ```bash
   docker-compose restart operator-cockpit
   ```

---

## 부록: 페이지별 API 의존성

각 페이지가 호출하는 백엔드 API 목록입니다. 특정 데이터가 표시되지 않을 때 해당 API를 직접 호출하여 문제를 진단할 수 있습니다.

### Dashboard (`/`)

| API | 서비스 | 포트 |
|-----|--------|------|
| `GET /stats` | AXEngine | 8001 |
| `GET /stats` | AXE_POE | 8002 |
| `GET /overview` | poQat Monitor | 8004 |

### AXEngine (`/axengine`)

| API | 서비스 | 포트 |
|-----|--------|------|
| `GET /goals` | AXEngine | 8001 |
| `POST /goals` | AXEngine | 8001 |
| `POST /goals/{id}/plan` | AXEngine | 8001 |
| `GET /hitl/stats` | AXEngine | 8001 |
| `GET /connectors/health` | AXEngine | 8001 |

### AXE_POE (`/poe`)

| API | 서비스 | 포트 |
|-----|--------|------|
| `GET /stats` | AXE_POE | 8002 |
| `GET /insights` | AXE_POE | 8002 |
| `GET /decisions` | AXE_POE | 8002 |
| `POST /decisions/{id}/approve` | AXE_POE | 8002 |
| `POST /pipeline/run` | AXE_POE | 8002 |

### Policies (`/policies`)

| API | 서비스 | 포트 |
|-----|--------|------|
| `GET /policies` | Policy Engine | 8003 |
| `GET /approvals?status=pending` | Policy Engine | 8003 |

### System Health (`/health`)

| API | 서비스 | 포트 |
|-----|--------|------|
| `GET /overview` | poQat Monitor | 8004 |

**진단 예시**:
```bash
# AXEngine 통계 API 직접 호출
curl -s http://localhost:8001/stats | python3 -m json.tool

# POE 인사이트 API 직접 호출
curl -s http://localhost:8002/insights | python3 -m json.tool

# poQat 전체 현황 API 직접 호출
curl -s http://localhost:8004/overview | python3 -m json.tool
```

---

**AXEworks Operator Cockpit** - 모든 AI 운영 상태를 한 눈에 파악하고 제어합니다.

문의: hello@axeworks.xyz
