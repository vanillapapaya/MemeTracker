"""
멀티에이전트 토론 시스템: 디씨 짤 검색 서비스 리스크 분석
5명의 전문가가 라운드별로 토론하며 리스크와 기술적 문제점을 다층적으로 분석합니다.

사용법:
    export ANTHROPIC_API_KEY="your-api-key"
    python multi_agent_discussion.py

    # 옵션
    python multi_agent_discussion.py --rounds 4 --model claude-sonnet-4-6
"""

import anthropic
import argparse
import json
import sys
from datetime import datetime


# ──────────────────────────────────────────────
# 5명의 전문가 페르소나 정의
# ──────────────────────────────────────────────

AGENTS = [
    {
        "id": "backend_engineer",
        "name": "김도현 (백엔드 엔지니어)",
        "emoji": "",
        "system_prompt": """당신은 10년차 백엔드/인프라 엔지니어 김도현입니다.
크롤링, 분산 시스템, DB 설계, API 아키텍처에 정통합니다.
Playwright, Qdrant, FastAPI 등의 기술 스택에 대해 실무 경험이 풍부합니다.

토론 스타일:
- 기술적 실현 가능성에 초점
- 구체적인 수치와 벤치마크를 근거로 제시
- "이론적으로는 되지만 실무에서는..." 같은 현실적 관점
- 다른 참여자의 기술적 오해를 정정
- 대안 기술 스택이나 아키텍처를 제안

한국어로 답변하세요. 존댓말을 쓰되 전문가답게 직설적으로 말하세요.
답변은 200-350자 내외로 핵심만 말하세요."""
    },
    {
        "id": "legal_expert",
        "name": "박서연 (법률/컴플라이언스 전문가)",
        "emoji": "",
        "system_prompt": """당신은 IT/저작권법 전문 변호사 박서연입니다.
웹 스크래핑 관련 판례, 저작권법, 개인정보보호법, 통신비밀보호법에 정통합니다.
스타트업 법률 자문 경험이 많아 사업적 맥락도 이해합니다.

토론 스타일:
- 법적 리스크를 구체적 조문과 판례로 설명
- "할 수 있다/없다"보다 "리스크 수준"으로 판단
- 다른 참여자가 법적 리스크를 과소평가하면 경고
- 합법적 우회 방법이 있으면 제안
- 해외 사례(미국 CFAA, EU 등)와 비교

한국어로 답변하세요. 존댓말을 쓰되 전문가답게 직설적으로 말하세요.
답변은 200-350자 내외로 핵심만 말하세요."""
    },
    {
        "id": "product_manager",
        "name": "이준호 (프로덕트 매니저)",
        "emoji": "",
        "system_prompt": """당신은 콘텐츠/커뮤니티 플랫폼 출신 PM 이준호입니다.
디씨인사이드, 에펨코리아 등 한국 커뮤니티 생태계를 잘 이해합니다.
사용자 행동 분석, PMF 검증, 그로스 해킹에 경험이 많습니다.

토론 스타일:
- 사용자 관점에서 "이걸 왜 쓰지?"를 끊임없이 질문
- 경쟁 서비스와 비교 (구글 이미지, 짤방저장소 등)
- MVP 범위와 우선순위에 대해 의견 제시
- 기술적으로 가능해도 사용자가 안 쓰면 의미없다는 관점
- 구체적인 사용 시나리오를 들어 설명

한국어로 답변하세요. 존댓말을 쓰되 전문가답게 직설적으로 말하세요.
답변은 200-350자 내외로 핵심만 말하세요."""
    },
    {
        "id": "security_engineer",
        "name": "최민지 (보안/안티어뷰즈 엔지니어)",
        "emoji": "",
        "system_prompt": """당신은 대형 플랫폼 출신 보안 엔지니어 최민지입니다.
봇 탐지, Rate Limiting, DDoS 방어, 안티 스크래핑에 전문성이 있습니다.
크롤링을 "하는 쪽"과 "막는 쪽" 모두의 관점을 이해합니다.

토론 스타일:
- 공격자(안티봇 시스템) 관점에서 취약점 분석
- 디씨인사이드의 봇 차단 메커니즘을 구체적으로 설명
- 서비스 운영 시 보안 이슈 (악용 가능성 등) 지적
- "뚫린다"가 아니라 "얼마나 오래 유지 가능한가"의 관점
- 실제 우회 경험 기반으로 현실적 난이도 평가

한국어로 답변하세요. 존댓말을 쓰되 전문가답게 직설적으로 말하세요.
답변은 200-350자 내외로 핵심만 말하세요."""
    },
    {
        "id": "business_analyst",
        "name": "정하은 (사업/수익화 분석가)",
        "emoji": "",
        "system_prompt": """당신은 콘텐츠 스타트업 경험이 있는 사업 분석가 정하은입니다.
광고 수익 모델, 유닛 이코노믹스, 스케일링 비용 분석에 전문성이 있습니다.
"짤방저장소", "모기", "디시콘" 같은 밈 관련 서비스 시장을 알고 있습니다.

토론 스타일:
- 숫자로 말함 (MAU, CAC, LTV, 서버 비용 등)
- "기술적으로 멋져도 돈이 안 되면 의미없다" 관점
- 비용 구조와 수익 모델의 현실성 검증
- 비슷한 서비스의 실패/성공 사례 인용
- 규모의 경제와 네트워크 효과 분석

한국어로 답변하세요. 존댓말을 쓰되 전문가답게 직설적으로 말하세요.
답변은 200-350자 내외로 핵심만 말하세요."""
    }
]


# ──────────────────────────────────────────────
# 프로젝트 설명 (토론 대상)
# ──────────────────────────────────────────────

PROJECT_DESCRIPTION = """
## 프로젝트: 디씨인사이드 짤(밈) 텍스트 검색 서비스

### 전체 아키텍처
[디씨 크롤러] -> [메타데이터 + URL 저장] -> [자동 캡셔닝] -> [벡터 임베딩] -> [검색 엔진]
                                                                              ^
                                                                        [사용자 텍스트 입력]

### 구성 요소별 설계
1. **크롤러**: 디씨 인기 갤러리(유머, 게임, 합성 등)에서 이미지 URL + 게시글 제목 + 댓글 수집.
   이미지 자체는 저장 안 하고 URL과 메타데이터만 DB에 저장.
   디씨 봇 차단 때문에 Playwright로 브라우저 자동화.

2. **자동 캡셔닝 (핵심)**:
   - LLM 캡셔닝: Claude나 GPT-4V로 이미지 설명 자동 생성 ("남자가 컴퓨터 앞에서 멘붕한 표정")
   - 게시글 맥락 활용: 제목, 댓글에서 자연어 태그 추출

3. **벡터 DB**: 캡션을 임베딩해서 저장
   - 임베딩 모델: multilingual-e5-large (한국어 강함)
   - 벡터 DB: Qdrant (무료, 로컬 운영 가능)

4. **검색**: 사용자가 "억울한 표정 짤" 입력 -> 텍스트 임베딩 -> 벡터 유사도 검색 -> URL 반환 -> 이미지 표시

### 기술 스택
- 크롤링: Python + Playwright
- 캡셔닝: Claude API (vision)
- 임베딩: multilingual-e5-large
- 벡터 DB: Qdrant
- 백엔드: FastAPI
- 프론트: Next.js or 단순 HTML
- 호스팅: Vercel (프론트) + Railway (백엔드)

### 개발 순서
1단계: 크롤러로 디씨 인기 짤 URL 500개 수집
2단계: Claude API로 자동 캡션 생성
3단계: Qdrant에 임베딩 저장
4단계: 검색 API 구현
5단계: 간단한 UI 붙이기
6단계: 광고 붙이고 오픈

### 비용 추산 (초기)
Claude API로 이미지 500장 캡셔닝하면 약 5달러 이내. 이후 검색은 거의 무료.
"""


# ──────────────────────────────────────────────
# 라운드별 토론 주제
# ──────────────────────────────────────────────

ROUND_TOPICS = [
    {
        "round": 1,
        "topic": "초기 반응 및 핵심 리스크 식별",
        "instruction": """프로젝트 설명을 읽고, 자신의 전문 분야 관점에서 가장 큰 리스크 1-2개를 식별하세요.
다른 참여자들이 놓칠 수 있는, 자기 분야 특유의 관점을 제시하세요."""
    },
    {
        "round": 2,
        "topic": "상호 검증 및 반론",
        "instruction": """이전 라운드에서 다른 참여자들이 제기한 리스크에 대해 반응하세요.
동의하는 부분, 반박하는 부분, 보완할 부분을 구분해서 말하세요.
다른 사람의 의견에 자기 전문 분야의 시각을 더하세요."""
    },
    {
        "round": 3,
        "topic": "대안 제시 및 실행 가능성",
        "instruction": """지금까지 논의된 리스크들에 대한 구체적인 대안이나 완화 방법을 제시하세요.
"이러면 된다"가 아니라 "이게 현실적으로 가능한 이유/불가능한 이유"를 설명하세요.
다른 참여자의 대안에 대해서도 피드백하세요."""
    },
    {
        "round": 4,
        "topic": "최종 판단 및 Go/No-Go 의견",
        "instruction": """모든 논의를 종합해서 이 프로젝트에 대한 최종 의견을 제시하세요.
Go(진행) / Conditional Go(조건부 진행) / No-Go(중단) 중 하나를 선택하고 근거를 밝히세요.
진행한다면 반드시 선행해야 할 조건을 명시하세요."""
    }
]


# ──────────────────────────────────────────────
# 토론 엔진
# ──────────────────────────────────────────────

class DiscussionEngine:
    def __init__(self, model: str = "claude-sonnet-4-6"):
        self.client = anthropic.Anthropic()
        self.model = model
        self.discussion_log = []  # 전체 토론 기록

    def _call_agent(self, agent: dict, user_message: str) -> str:
        """단일 에이전트에게 메시지를 보내고 응답을 받습니다."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=agent["system_prompt"],
            messages=[{"role": "user", "content": user_message}]
        )
        return response.content[0].text

    def _format_previous_discussion(self) -> str:
        """이전 라운드의 토론 내용을 포맷팅합니다."""
        if not self.discussion_log:
            return ""

        formatted = "\n\n--- 이전 토론 내용 ---\n"
        for entry in self.discussion_log:
            formatted += f"\n[라운드 {entry['round']} - {entry['agent_name']}]\n"
            formatted += f"{entry['response']}\n"
        return formatted

    def run_round(self, round_info: dict) -> list:
        """한 라운드의 토론을 실행합니다."""
        round_num = round_info["round"]
        topic = round_info["topic"]
        instruction = round_info["instruction"]

        print(f"\n{'='*60}")
        print(f"  라운드 {round_num}: {topic}")
        print(f"{'='*60}\n")

        round_results = []

        for agent in AGENTS:
            # 각 에이전트에게 보낼 메시지 구성
            message = f"""## 토론 프로젝트
{PROJECT_DESCRIPTION}

## 현재 라운드: 라운드 {round_num} - {topic}
{instruction}

{self._format_previous_discussion()}

위 맥락을 바탕으로 자신의 전문가 관점에서 의견을 제시하세요."""

            print(f"[{agent['name']}] 발언 중...")
            response_text = self._call_agent(agent, message)

            # 기록 저장
            entry = {
                "round": round_num,
                "agent_id": agent["id"],
                "agent_name": agent["name"],
                "topic": topic,
                "response": response_text
            }
            self.discussion_log.append(entry)
            round_results.append(entry)

            # 출력
            print(f"\n--- {agent['name']} ---")
            print(response_text)
            print()

        return round_results

    def run_full_discussion(self, num_rounds: int = 4) -> list:
        """전체 토론을 실행합니다."""
        rounds_to_run = ROUND_TOPICS[:num_rounds]

        print("\n" + "=" * 60)
        print("  디씨 짤 검색 서비스 - 멀티에이전트 리스크 분석 토론")
        print(f"  참여자: {len(AGENTS)}명 | 라운드: {num_rounds}회")
        print(f"  모델: {self.model}")
        print(f"  시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        print("\n[참여자 소개]")
        for agent in AGENTS:
            print(f"  - {agent['name']}")

        for round_info in rounds_to_run:
            self.run_round(round_info)

        return self.discussion_log

    def generate_summary(self) -> str:
        """토론 결과를 종합 요약합니다."""
        print(f"\n{'='*60}")
        print("  종합 요약 생성 중...")
        print(f"{'='*60}\n")

        # 전체 토론 내용을 모아서 요약 요청
        full_discussion = ""
        for entry in self.discussion_log:
            full_discussion += f"\n[라운드 {entry['round']} - {entry['agent_name']}]\n"
            full_discussion += f"{entry['response']}\n"

        summary_prompt = f"""다음은 5명의 전문가가 "디씨인사이드 짤 텍스트 검색 서비스" 프로젝트에 대해
4라운드에 걸쳐 토론한 내용입니다.

{full_discussion}

위 토론을 종합하여 다음 구조로 요약하세요:

1. **핵심 리스크 TOP 5** (심각도 순)
   - 각 리스크에 대해 어떤 전문가가 어떤 관점에서 지적했는지

2. **의견이 갈린 쟁점**
   - 전문가들 간 의견이 달랐던 부분과 각자의 논거

3. **합의된 사항**
   - 전문가들이 공통적으로 동의한 부분

4. **최종 Go/No-Go 집계**
   - 각 전문가의 최종 판단과 조건

5. **권장 액션 아이템**
   - 프로젝트를 진행한다면 우선적으로 해결해야 할 사항 (우선순위 순)

한국어로 작성하세요."""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[{"role": "user", "content": summary_prompt}]
        )
        return response.content[0].text

    def save_results(self, filepath: str, summary: str):
        """토론 결과를 JSON과 마크다운으로 저장합니다."""
        # JSON 저장
        json_data = {
            "metadata": {
                "project": "디씨 짤 검색 서비스 리스크 분석",
                "model": self.model,
                "agents": [{"id": a["id"], "name": a["name"]} for a in AGENTS],
                "timestamp": datetime.now().isoformat(),
                "total_rounds": len(set(e["round"] for e in self.discussion_log))
            },
            "discussion_log": self.discussion_log,
            "summary": summary
        }

        json_path = filepath.replace(".md", ".json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        print(f"JSON 저장: {json_path}")

        # 마크다운 저장
        md_content = f"""# 디씨 짤 검색 서비스 - 멀티에이전트 리스크 분석 토론

> 생성일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
> 모델: {self.model}
> 참여자: {', '.join(a['name'] for a in AGENTS)}

---

"""
        # 라운드별 토론 내용
        current_round = 0
        for entry in self.discussion_log:
            if entry["round"] != current_round:
                current_round = entry["round"]
                round_info = next(r for r in ROUND_TOPICS if r["round"] == current_round)
                md_content += f"\n## 라운드 {current_round}: {round_info['topic']}\n\n"

            md_content += f"### {entry['agent_name']}\n\n"
            md_content += f"{entry['response']}\n\n"

        # 종합 요약
        md_content += f"\n---\n\n## 종합 요약\n\n{summary}\n"

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md_content)
        print(f"마크다운 저장: {filepath}")


# ──────────────────────────────────────────────
# 메인 실행
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="멀티에이전트 토론 시스템")
    parser.add_argument("--rounds", type=int, default=4, choices=[1, 2, 3, 4],
                        help="토론 라운드 수 (기본: 4)")
    parser.add_argument("--model", type=str, default="claude-sonnet-4-6",
                        help="사용할 Claude 모델 (기본: claude-sonnet-4-6)")
    parser.add_argument("--output", type=str, default="discussion_result.md",
                        help="결과 저장 파일명 (기본: discussion_result.md)")
    parser.add_argument("--no-summary", action="store_true",
                        help="종합 요약 생성 건너뛰기")
    args = parser.parse_args()

    # API 키 확인
    try:
        client = anthropic.Anthropic()
    except anthropic.AuthenticationError:
        print("ANTHROPIC_API_KEY 환경변수를 설정해주세요.")
        print("  export ANTHROPIC_API_KEY='your-api-key'")
        sys.exit(1)

    # 토론 실행
    engine = DiscussionEngine(model=args.model)
    engine.run_full_discussion(num_rounds=args.rounds)

    # 종합 요약
    summary = ""
    if not args.no_summary:
        summary = engine.generate_summary()
        print("\n" + "=" * 60)
        print("  종합 요약")
        print("=" * 60)
        print(summary)

    # 결과 저장
    engine.save_results(args.output, summary)

    print(f"\n완료! 결과가 {args.output}에 저장되었습니다.")


if __name__ == "__main__":
    main()
