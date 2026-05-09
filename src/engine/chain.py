"""인과관계 체인 추적 엔진

이벤트 입력 → 공급망/매크로 그래프를 따라 영향받는 섹터/종목 자동 탐색.
02_supply_chain_map.md의 내용을 코드로 구현.
"""

from dataclasses import dataclass, field

# ─── 데이터 구조 ───


@dataclass
class Impact:
    target: str
    direction: str  # "+" 수혜, "-" 피해
    confidence: str  # A/B/C/D
    reason: str
    tickers: list[str] = field(default_factory=list)


@dataclass
class ChainResult:
    event: str
    depth: int
    impacts: list[Impact]

    @property
    def label(self) -> str:
        return {1: "1차 (직접)", 2: "2차 (파급)", 3: "3차 (간접)", 4: "4차 (약한 연결)"}[self.depth]


# ─── 인과관계 그래프 정의 ───

CAUSAL_GRAPH: dict[str, list[ChainResult]] = {}


def _register(trigger: str, chains: list[ChainResult]):
    CAUSAL_GRAPH[trigger] = chains


# ── 원유 급등 ──
_register("원유급등", [
    ChainResult("원유급등", 1, [
        Impact("석유/에너지", "+", "A", "원유 가격 직접 수혜", ["XOM", "CVX", "SHEL"]),
        Impact("유전서비스", "+", "A", "시추 투자 확대", ["SLB", "HAL"]),
        Impact("항공", "-", "A", "연료비 비중 30%+", ["UAL", "DAL", "003490"]),
        Impact("해운/물류", "-", "B", "운송비 증가", ["HMM", "FDX", "UPS"]),
        Impact("화학/플라스틱", "-", "B", "나프타 원가 상승", ["051910"]),
    ]),
    ChainResult("원유급등", 2, [
        Impact("대체에너지", "+", "B", "원유 대비 경쟁력 상승", ["ENPH", "FSLR"]),
        Impact("전기차", "+", "B", "ICE 대비 유지비 이점 부각", ["TSLA", "1211.HK", "005380"]),
        Impact("인플레이션", "+", "A", "에너지 CPI 상승", []),
        Impact("소비/유통", "-", "B", "가처분소득 감소", ["WMT", "TGT"]),
        Impact("산유국 통화", "+", "B", "경상수지 개선", []),
    ]),
    ChainResult("원유급등", 3, [
        Impact("금리 인상 압력", "+", "B", "인플레 → 연준 매파 강화", []),
        Impact("성장주", "-", "C", "할인율 증가 → 밸류에이션 하락", ["NVDA", "MSFT", "035420"]),
        Impact("신흥국 원유수입국", "-", "B", "경상수지 악화 (한국,인도,일본)", ["EWY", "INDA"]),
        Impact("달러", "+", "B", "안전자산 + 금리 상승", []),
        Impact("원/달러 환율", "+", "B", "원화 약세 → 수출주 일부 수혜", ["005930"]),
    ]),
])

# ── 원유 급락 ──
_register("원유급락", [
    ChainResult("원유급락", 1, [
        Impact("석유/에너지", "-", "A", "매출/이익 직접 감소", ["XOM", "CVX"]),
        Impact("항공", "+", "A", "연료비 절감", ["UAL", "DAL", "003490"]),
        Impact("소비자", "+", "B", "유류비 절감 → 소비 여력 증가", ["WMT", "COST"]),
    ]),
    ChainResult("원유급락", 2, [
        Impact("하이일드 채권", "-", "B", "에너지 비중 높은 HY → 스프레드 확대", []),
        Impact("산유국 재정", "-", "B", "재정적자 확대", []),
        Impact("디플레 우려", "+", "C", "연준 비둘기파 전환 가능", []),
        Impact("여행/레저", "+", "B", "여행 비용 절감", ["MAR", "HLT"]),
    ]),
])

# ── 금리 인상 ──
_register("금리인상", [
    ChainResult("금리인상", 1, [
        Impact("채권", "-", "A", "금리와 역관계", ["TLT", "IEF"]),
        Impact("은행/금융", "+", "A", "NIM(순이자마진) 확대 (초기)", ["JPM", "BAC", "105560"]),
        Impact("성장주", "-", "A", "할인율 증가 → 미래 현금흐름 현재가치 하락", ["NVDA", "TSLA", "035420"]),
        Impact("달러", "+", "A", "금리 차이 확대 → 달러 유입", []),
        Impact("부동산/리츠", "-", "A", "모기지 금리 상승 → 수요 감소", ["AMT", "PLD"]),
    ]),
    ChainResult("금리인상", 2, [
        Impact("가치주/배당주", "+", "B", "성장주 대비 상대 매력", ["KO", "PG", "033780"]),
        Impact("신흥국", "-", "B", "자본 유출 + 달러 부채 부담 증가", ["EEM"]),
        Impact("고부채 기업", "-", "B", "이자비용 증가", []),
        Impact("자사주매입", "-", "C", "차입 비용 증가 → 환원 축소", []),
    ]),
    ChainResult("금리인상", 3, [
        Impact("경기침체 리스크", "+", "C", "장단기 금리 역전 시 12-18개월 후 침체", []),
        Impact("원자재", "-", "C", "달러 강세로 가격 하락 압력", ["GLD", "COPX"]),
    ]),
])

# ── 금리 인하 ──
_register("금리인하", [
    ChainResult("금리인하", 1, [
        Impact("성장주/기술주", "+", "A", "할인율 감소 → 밸류에이션 상승", ["NVDA", "MSFT", "AAPL"]),
        Impact("채권", "+", "A", "금리 하락 → 채권 가격 상승", ["TLT"]),
        Impact("부동산/리츠", "+", "A", "모기지 부담 감소", ["AMT"]),
        Impact("달러", "-", "B", "금리 매력 감소 → 달러 유출", []),
    ]),
    ChainResult("금리인하", 2, [
        Impact("신흥국", "+", "B", "자본 유입 + 달러 약세 수혜", ["EEM"]),
        Impact("금", "+", "B", "달러 약세 + 실질금리 하락", ["GLD"]),
        Impact("소형주", "+", "B", "유동성 확대 → 위험자산 선호", ["IWM"]),
        Impact("원/달러", "-", "B", "원화 강세 → 내수주 수혜", []),
    ]),
])

# ── 브라질 가뭄 ──
_register("브라질가뭄", [
    ChainResult("브라질가뭄", 1, [
        Impact("커피", "+", "A", "브라질 = 세계 1위 커피 생산국 (30%+)", []),
        Impact("설탕", "+", "A", "사탕수수 피해", []),
        Impact("대두", "+", "A", "브라질 = 세계 1위 대두 수출국", []),
        Impact("오렌지주스", "+", "B", "감귤류 피해", []),
    ]),
    ChainResult("브라질가뭄", 2, [
        Impact("커피체인", "-", "B", "원가 부담 증가", ["SBUX"]),
        Impact("식품기업", "-", "B", "원자재 가격 상승", ["NESN", "ULVR"]),
        Impact("농기업", "+", "B", "곡물 가격 상승 수혜", ["ADM", "BG"]),
        Impact("비료", "+", "B", "농산물 가격 상승 → 농가 투자 증가", ["NTR", "MOS"]),
        Impact("브라질 헤알화", "-", "B", "수출 감소 → 경상수지 악화", []),
    ]),
    ChainResult("브라질가뭄", 3, [
        Impact("식품 CPI", "+", "C", "식품 물가 상승 → 전체 인플레 압력", []),
        Impact("사료비", "+", "C", "대두/옥수수 → 축산 비용 증가", []),
        Impact("바이오연료", "-", "C", "에탄올 원료 부족 → 에너지 영향", []),
        Impact("물류량 감소", "-", "C", "브라질 수출 감소 → 해운/물류 수익 감소", []),
    ]),
    ChainResult("브라질가뭄", 4, [
        Impact("IT 공급망", "-", "D", "물류 감소 → IT부품 발주 감소 가능 (약한 연결)", []),
        Impact("중앙은행 긴축", "+", "D", "식품발 인플레 → 금리 인상 연쇄", []),
    ]),
])

# ── 반도체 업사이클 ──
_register("반도체업사이클", [
    ChainResult("반도체업사이클", 1, [
        Impact("GPU", "+", "A", "AI 데이터센터 수요 폭증", ["NVDA", "AMD"]),
        Impact("메모리", "+", "A", "HBM/DRAM 수요 급증", ["005930", "000660", "MU"]),
        Impact("파운드리", "+", "A", "첨단 공정 수요", ["TSM"]),
        Impact("반도체장비", "+", "A", "CapEx 투자 확대", ["ASML", "AMAT", "LRCX"]),
    ]),
    ChainResult("반도체업사이클", 2, [
        Impact("전력 인프라", "+", "B", "데이터센터 전력 소비 급증", ["012450"]),
        Impact("네트워킹", "+", "B", "데이터센터 간 연결 수요", ["AVGO", "CSCO"]),
        Impact("냉각시스템", "+", "B", "고밀도 GPU 냉각 수요", []),
        Impact("PCB/기판", "+", "B", "서버 기판 수요", []),
        Impact("소재(웨이퍼)", "+", "B", "실리콘웨이퍼 수요 증가", []),
    ]),
    ChainResult("반도체업사이클", 3, [
        Impact("클라우드/SaaS", "+", "C", "AI 서비스 확대", ["AMZN", "MSFT", "GOOGL"]),
        Impact("로봇/자율주행", "+", "C", "AI 칩 탑재 가속", []),
        Impact("전력회사", "+", "C", "데이터센터 전력 수요", []),
    ]),
])

# ── 반도체 다운사이클 ──
_register("반도체다운사이클", [
    ChainResult("반도체다운사이클", 1, [
        Impact("메모리", "-", "A", "가격 하락 → 실적 악화", ["005930", "000660", "MU"]),
        Impact("반도체장비", "-", "A", "CapEx 축소 → 수주 감소", ["ASML", "AMAT"]),
    ]),
    ChainResult("반도체다운사이클", 2, [
        Impact("한국/대만 수출", "-", "B", "반도체 = 주력 수출품", []),
        Impact("원화/대만달러", "-", "B", "수출 감소 → 통화 약세", []),
        Impact("전자기기 수요", "-", "C", "소비 부진 신호", []),
    ]),
])

# ── 대만해협 긴장 ──
_register("대만해협긴장", [
    ChainResult("대만해협긴장", 1, [
        Impact("TSMC/대만반도체", "-", "A", "공급 차단 리스크", ["TSM"]),
        Impact("방산", "+", "A", "군비 증강 기대", ["LMT", "RTX", "012450", "329180"]),
        Impact("금/안전자산", "+", "A", "지정학 리스크 프리미엄", ["GLD"]),
        Impact("대만 증시", "-", "A", "직접 리스크", []),
    ]),
    ChainResult("대만해협긴장", 2, [
        Impact("TSMC 의존 기업", "-", "B", "첨단칩 공급 차질", ["AAPL", "NVDA", "AMD", "QCOM"]),
        Impact("해운 운임", "+", "B", "남중국해 물류 불안", []),
        Impact("미국/일본 반도체", "+", "B", "자국 생산 투자 가속", ["INTC"]),
        Impact("희토류", "+", "B", "중국 제재 시 공급 차질", []),
    ]),
    ChainResult("대만해협긴장", 3, [
        Impact("글로벌 전자기기", "-", "C", "첨단 반도체 부족", []),
        Impact("자동차(반도체)", "-", "C", "차량용 반도체 공급 차질", ["005380"]),
    ]),
])

# ── 중동 긴장 ──
_register("중동긴장", [
    ChainResult("중동긴장", 1, [
        Impact("원유", "+", "A", "호르무즈 해협 = 일일 석유 운송 20%", []),
        Impact("방산", "+", "A", "군비 수요", ["LMT", "RTX", "012450"]),
        Impact("금", "+", "A", "안전자산 수요", ["GLD"]),
        Impact("항공", "-", "B", "운항 불안 + 유가", ["UAL"]),
    ]),
    ChainResult("중동긴장", 2, [
        Impact("에너지주", "+", "A", "원유 가격 동반 상승", ["XOM", "CVX"]),
        Impact("인플레이션", "+", "B", "에너지발 물가 상승", []),
    ]),
])

# ── 팬데믹/전염병 ──
_register("팬데믹", [
    ChainResult("팬데믹", 1, [
        Impact("바이오/제약", "+", "A", "백신/치료제 수요", ["PFE", "MRNA", "207940"]),
        Impact("진단/의료기기", "+", "A", "검사 수요 폭증", ["096530"]),
        Impact("항공/여행", "-", "A", "이동 제한", ["UAL", "DAL", "003490"]),
        Impact("호텔/크루즈", "-", "A", "관광 중단", ["MAR", "HLT"]),
        Impact("오프라인 유통", "-", "A", "봉쇄/사회적 거리두기", []),
    ]),
    ChainResult("팬데믹", 2, [
        Impact("이커머스", "+", "A", "온라인 쇼핑 전환", ["AMZN", "CPNG"]),
        Impact("클라우드/SaaS", "+", "A", "재택근무 전환", ["MSFT", "ZM"]),
        Impact("게임/엔터", "+", "B", "실내 여가 수요", ["263750"]),
        Impact("원유", "-", "A", "이동 수요 급감", ["XOM"]),
    ]),
    ChainResult("팬데믹", 3, [
        Impact("재정부양", "+", "B", "정부 지출 확대 → 유동성 증가", []),
        Impact("연준 양적완화", "+", "B", "금리 인하 + QE → 자산 가격 상승", []),
        Impact("공급망 병목", "+", "C", "봉쇄 → 생산 차질 → 인플레 씨앗", []),
    ]),
])

# ── 엘니뇨 ──
_register("엘니뇨", [
    ChainResult("엘니뇨", 1, [
        Impact("동남아 농산물", "-", "B", "가뭄으로 팜유/쌀 생산 감소", []),
        Impact("호주 석탄/광산", "-", "B", "가뭄 → 조업 차질", ["BHP"]),
        Impact("남미 홍수", "-", "B", "광산 침수 → 구리/리튬 공급 감소", []),
    ]),
    ChainResult("엘니뇨", 2, [
        Impact("천연가스", "-", "B", "북미 따뜻한 겨울 → 난방 수요 감소", []),
        Impact("식량 인플레", "+", "C", "인도 몬순 약화 → 쌀/밀 가격 상승", []),
        Impact("전력 수요", "+", "C", "이상기온 → 냉방 수요 변동", []),
    ]),
])

# ── 중국 경기 둔화 ──
_register("중국경기둔화", [
    ChainResult("중국경기둔화", 1, [
        Impact("원자재", "-", "A", "세계 최대 소비국 수요 감소", []),
        Impact("철광석", "-", "A", "건설/인프라 수요 감소", ["BHP", "RIO", "VALE"]),
        Impact("구리", "-", "A", "산업 수요 감소", []),
        Impact("호주 달러", "-", "B", "대중 수출 의존", []),
    ]),
    ChainResult("중국경기둔화", 2, [
        Impact("명품", "-", "B", "중국 소비 위축", ["MC", "RMS"]),
        Impact("한국 수출", "-", "B", "대중 수출 비중 높음", ["005930", "000660"]),
        Impact("동남아 신흥국", "-", "B", "공급망 연계 약화", []),
        Impact("유럽 자동차", "-", "C", "중국 판매 감소", ["MBG", "BMW"]),
    ]),
])

# ── 달러 강세 ──
_register("달러강세", [
    ChainResult("달러강세", 1, [
        Impact("금", "-", "B", "역상관 관계", ["GLD"]),
        Impact("원자재 전반", "-", "B", "달러 표시 가격 하락 압력", []),
        Impact("신흥국 주식", "-", "B", "자본 유출", ["EEM"]),
        Impact("미국 다국적 기업", "-", "B", "해외 매출 환산 감소", []),
    ]),
    ChainResult("달러강세", 2, [
        Impact("한국 수출주", "+", "B", "원화 약세 → 가격 경쟁력", ["005930", "000270"]),
        Impact("한국 내수주", "-", "B", "수입 원가 증가", []),
        Impact("일본 수출주", "+", "B", "엔화 약세 동반 시", []),
    ]),
])

# ── 전쟁/지정학 충격 ──
_register("전쟁", [
    ChainResult("전쟁", 1, [
        Impact("방산", "+", "A", "군비 증강", ["LMT", "RTX", "NOC", "012450", "329180"]),
        Impact("에너지", "+", "B", "공급 불안", ["XOM", "CVX"]),
        Impact("금", "+", "A", "안전자산 수요", ["GLD"]),
        Impact("국채", "+", "B", "안전자산 수요", ["TLT"]),
        Impact("항공/관광", "-", "B", "여행 수요 감소", []),
    ]),
    ChainResult("전쟁", 2, [
        Impact("곡물", "+", "B", "교전국이 주요 수출국인 경우", []),
        Impact("사이버보안", "+", "B", "사이버 위협 증가", ["PANW", "CRWD"]),
        Impact("인플레이션", "+", "C", "에너지/곡물 가격 전이", []),
    ]),
])

# ── 은행 위기 ──
_register("은행위기", [
    ChainResult("은행위기", 1, [
        Impact("은행/금융주", "-", "A", "뱅크런 + 부실 우려", ["JPM", "BAC", "105560"]),
        Impact("금", "+", "B", "안전자산 수요", ["GLD"]),
        Impact("국채", "+", "B", "안전자산 + 금리 인하 기대", ["TLT"]),
    ]),
    ChainResult("은행위기", 2, [
        Impact("연준 긴급 대응", "+", "B", "유동성 공급 → 시장 안정화", []),
        Impact("핀테크", "+", "C", "전통 은행 불신 → 대안 수요", []),
        Impact("부동산", "-", "B", "대출 긴축", []),
    ]),
])

# ── 미국 대선 ──
_register("미국대선", [
    ChainResult("미국대선", 1, [
        Impact("방산", "+", "B", "양당 모두 국방 지출 유지/확대", ["LMT", "RTX", "NOC"]),
        Impact("인프라", "+", "B", "선거 공약 → 인프라 투자 기대", []),
        Impact("VIX(변동성)", "+", "A", "불확실성 확대 → 옵션 프리미엄 상승", []),
        Impact("헬스케어", "-", "B", "약가 규제 공약 시 제약주 하락", ["UNH", "LLY", "PFE"]),
    ]),
    ChainResult("미국대선", 2, [
        Impact("친환경에너지", "+", "B", "민주당 승리 시 보조금 확대", ["ENPH", "FSLR"]),
        Impact("전통에너지", "+", "B", "공화당 승리 시 규제 완화", ["XOM", "CVX"]),
        Impact("빅테크", "-", "C", "반독점 규제 강화 가능성", ["GOOGL", "META", "AMZN"]),
        Impact("총기/교도소", "+", "C", "공화당 승리 시 수혜", []),
        Impact("한국 방산", "+", "B", "동맹국 방위비 분담금 이슈", ["012450", "329180"]),
    ]),
    ChainResult("미국대선", 3, [
        Impact("무역정책 변화", "+", "C", "관세 정책에 따라 수출주 영향", ["005930"]),
        Impact("달러 변동성", "+", "C", "정책 불확실성 → 환율 변동", []),
    ]),
])

# ── AI 버블 / AI 과열 ──
_register("AI버블", [
    ChainResult("AI버블", 1, [
        Impact("AI반도체", "-", "A", "과대평가 조정", ["NVDA", "AMD", "AVGO"]),
        Impact("AI소프트웨어", "-", "A", "실적 대비 과도한 밸류에이션 조정", []),
        Impact("클라우드 인프라", "-", "B", "CapEx 과잉투자 우려", ["AMZN", "MSFT", "GOOGL"]),
    ]),
    ChainResult("AI버블", 2, [
        Impact("전력/냉각 인프라", "-", "B", "데이터센터 투자 축소", ["012450"]),
        Impact("메모리(HBM)", "-", "B", "AI향 HBM 수요 둔화", ["005930", "000660"]),
        Impact("가치주 회전", "+", "B", "성장주 → 가치주 자금 이동", ["KO", "PG", "JPM"]),
        Impact("배당주", "+", "B", "안정적 수익 선호", ["033780"]),
    ]),
    ChainResult("AI버블", 3, [
        Impact("나스닥", "-", "B", "기술주 비중 높은 지수 하락", []),
        Impact("코스닥", "-", "C", "국내 AI 관련주 동반 조정", []),
        Impact("채권", "+", "C", "위험자산 회피 → 안전자산 선호", ["TLT"]),
    ]),
])

# ── 양적완화 (QE) ──
_register("양적완화", [
    ChainResult("양적완화", 1, [
        Impact("주식 전반", "+", "A", "유동성 공급 → 자산가격 상승", []),
        Impact("채권", "+", "A", "연준 매입 → 금리 하락", ["TLT"]),
        Impact("달러", "-", "B", "통화 공급 증가 → 달러 약세", []),
        Impact("금", "+", "A", "인플레 헤지 + 달러 약세", ["GLD"]),
    ]),
    ChainResult("양적완화", 2, [
        Impact("성장주/기술주", "+", "A", "저금리 + 유동성 → 밸류에이션 확장", ["NVDA", "MSFT", "TSLA"]),
        Impact("소형주", "+", "B", "위험선호 확대", ["IWM"]),
        Impact("부동산/리츠", "+", "B", "저금리 → 자산가격 상승", ["AMT"]),
        Impact("신흥국", "+", "B", "달러 약세 + 자본 유입", ["EEM"]),
        Impact("비트코인/가상자산", "+", "B", "유동성 확대 → 대체자산 수요", []),
    ]),
    ChainResult("양적완화", 3, [
        Impact("인플레이션", "+", "C", "과도한 유동성 → 물가 상승 씨앗", []),
        Impact("원자재", "+", "B", "달러 약세 + 수요 기대", []),
    ]),
])

# ── 양적긴축 (QT) ──
_register("양적긴축", [
    ChainResult("양적긴축", 1, [
        Impact("채권", "-", "A", "연준 매도 → 금리 상승 압력", ["TLT"]),
        Impact("주식 전반", "-", "B", "유동성 축소 → 밸류에이션 하락", []),
        Impact("달러", "+", "B", "유동성 회수 → 달러 강세", []),
    ]),
    ChainResult("양적긴축", 2, [
        Impact("성장주", "-", "B", "금리 상승 → 할인율 증가", ["NVDA", "TSLA", "035420"]),
        Impact("소형주", "-", "B", "유동성 감소에 가장 민감", ["IWM"]),
        Impact("신흥국", "-", "B", "달러 강세 + 자본 유출", ["EEM"]),
        Impact("은행", "+", "B", "금리 상승 → NIM 개선", ["JPM", "105560"]),
    ]),
])

# ── 무역전쟁 / 관세 ──
_register("무역전쟁", [
    ChainResult("무역전쟁", 1, [
        Impact("수출 제조업", "-", "A", "관세로 가격 경쟁력 하락", ["005930", "000270", "005380"]),
        Impact("농업", "-", "B", "보복 관세 → 농산물 수출 감소", []),
        Impact("반도체", "-", "A", "수출 규제 → 공급망 재편", ["NVDA", "AMD", "TSM"]),
        Impact("금", "+", "B", "불확실성 증가 → 안전자산 수요", ["GLD"]),
    ]),
    ChainResult("무역전쟁", 2, [
        Impact("물류/해운", "-", "B", "교역량 감소", ["FDX", "UPS"]),
        Impact("내수주", "+", "B", "수입품 가격 상승 → 국내 제품 경쟁력", []),
        Impact("동남아 제조업", "+", "B", "공급망 우회 수혜", []),
        Impact("소비자 물가", "+", "B", "관세 → 수입품 가격 상승 → 인플레", []),
    ]),
    ChainResult("무역전쟁", 3, [
        Impact("글로벌 GDP 둔화", "-", "C", "교역 위축 → 성장 둔화", []),
        Impact("방산", "+", "C", "지정학 긴장 동반 시", ["LMT", "012450"]),
    ]),
])

# ── 부동산 위기 ──
_register("부동산위기", [
    ChainResult("부동산위기", 1, [
        Impact("건설", "-", "A", "착공 감소 → 매출 급감", []),
        Impact("부동산/리츠", "-", "A", "부동산 가격 하락", ["AMT", "PLD"]),
        Impact("은행/금융", "-", "A", "부동산 담보 대출 부실 증가", ["JPM", "BAC", "105560"]),
        Impact("건자재", "-", "B", "시멘트/철강 수요 감소", ["005490"]),
    ]),
    ChainResult("부동산위기", 2, [
        Impact("소비 위축", "-", "B", "자산 효과 감소 → 소비 둔화", ["WMT", "COST"]),
        Impact("금리 인하 기대", "+", "B", "경기 부양 위해 연준 금리 인하", []),
        Impact("채권", "+", "B", "안전자산 + 금리 인하 기대", ["TLT"]),
        Impact("인테리어/가구", "-", "B", "주택 거래 감소 → 수요 감소", []),
    ]),
    ChainResult("부동산위기", 3, [
        Impact("경기침체", "+", "C", "부동산발 역자산효과 → 소비/투자 위축", []),
        Impact("금", "+", "C", "위기 시 안전자산 수요", ["GLD"]),
    ]),
])

# ── 인플레이션 급등 ──
_register("인플레이션급등", [
    ChainResult("인플레이션급등", 1, [
        Impact("원자재/에너지", "+", "A", "실물 자산 가격 상승", ["XOM", "CVX"]),
        Impact("금", "+", "A", "인플레 헤지 대표 자산", ["GLD"]),
        Impact("소비자 구매력", "-", "A", "실질 소득 감소", []),
        Impact("채권", "-", "A", "인플레 → 금리 상승 → 채권 가격 하락", ["TLT"]),
    ]),
    ChainResult("인플레이션급등", 2, [
        Impact("유통/소비재", "-", "B", "원가 상승 + 소비 위축", ["WMT", "COST"]),
        Impact("가치주/배당주", "+", "B", "실적 기반 주식 상대 강세", ["KO", "PG"]),
        Impact("부동산", "+", "B", "실물 자산 인플레 헤지", []),
        Impact("금리 인상 압력", "+", "A", "연준 긴축 강화", []),
    ]),
    ChainResult("인플레이션급등", 3, [
        Impact("성장주", "-", "B", "금리 상승 → 밸류에이션 하락", ["NVDA", "TSLA", "035420"]),
        Impact("임금 상승 압력", "+", "C", "노동시장 경직 → 기업 비용 증가", []),
    ]),
])

# ── 일본 엔저 ──
_register("일본엔저", [
    ChainResult("일본엔저", 1, [
        Impact("일본 수출주", "+", "A", "가격 경쟁력 상승", []),
        Impact("한국 수출주", "-", "B", "일본과 경쟁 품목에서 불리", ["005380", "000270"]),
        Impact("일본 관광", "+", "B", "방문 비용 저렴 → 관광 수요 증가", []),
    ]),
    ChainResult("일본엔저", 2, [
        Impact("한국 자동차", "-", "B", "글로벌 시장에서 일본차 가격 경쟁력↑", ["005380", "000270"]),
        Impact("한국 철강/조선", "-", "B", "일본 경쟁사 가격 우위", ["005490", "329180"]),
        Impact("엔캐리 트레이드", "+", "B", "저금리 엔화 차입 → 고금리 자산 투자", []),
    ]),
    ChainResult("일본엔저", 3, [
        Impact("신흥국 통화 불안", "-", "C", "아시아 통화 약세 전염", []),
        Impact("BOJ 정책 변화", "+", "C", "엔저 지속 시 정책 수정 기대", []),
    ]),
])

# ── 공급망 위기 ──
_register("공급망위기", [
    ChainResult("공급망위기", 1, [
        Impact("자동차", "-", "A", "부품 부족 → 생산 차질", ["TSLA", "005380", "000270"]),
        Impact("전자기기", "-", "A", "반도체/부품 수급 차질", ["AAPL"]),
        Impact("해운 운임", "+", "A", "물류 병목 → 운임 급등", []),
        Impact("물류기업", "+", "B", "높은 운임 = 매출 증가", ["FDX", "UPS"]),
    ]),
    ChainResult("공급망위기", 2, [
        Impact("인플레이션", "+", "B", "공급 부족 → 가격 상승", []),
        Impact("재고 보유 기업", "+", "B", "재고 확보 기업 상대 수혜", ["WMT", "COST"]),
        Impact("국내 생산 기업", "+", "B", "글로벌 의존도 낮은 기업 수혜", []),
    ]),
    ChainResult("공급망위기", 3, [
        Impact("리쇼어링 투자", "+", "C", "자국 생산 확대 투자", ["INTC"]),
        Impact("경기 둔화", "-", "C", "생산 차질 → 성장 둔화", []),
    ]),
])

# ── 기후변화/탄소규제 ──
_register("기후변화규제", [
    ChainResult("기후변화규제", 1, [
        Impact("재생에너지", "+", "A", "태양광/풍력 투자 확대", ["ENPH", "FSLR"]),
        Impact("전기차", "+", "A", "내연기관 규제 → EV 전환 가속", ["TSLA", "005380"]),
        Impact("배터리", "+", "A", "EV + ESS 수요 증가", ["373220", "006400"]),
        Impact("석탄/화석연료", "-", "A", "좌초자산 리스크", []),
    ]),
    ChainResult("기후변화규제", 2, [
        Impact("탄소배출권", "+", "B", "탄소 가격 상승", []),
        Impact("철강/시멘트", "-", "B", "탄소 국경세(CBAM) 부담", ["005490"]),
        Impact("원자력", "+", "B", "탄소 중립 대안 에너지", []),
        Impact("수소", "+", "B", "그린수소 투자 확대", []),
    ]),
    ChainResult("기후변화규제", 3, [
        Impact("ESG 펀드", "+", "C", "친환경 기업 자금 유입", []),
        Impact("전통 에너지", "-", "C", "장기적 수요 감소 전망", ["XOM", "CVX"]),
    ]),
])

# ── 일본 금리 인상 ──
_register("일본금리인상", [
    ChainResult("일본금리인상", 1, [
        Impact("엔화 강세", "+", "A", "금리 차이 축소 → 엔화 매수", []),
        Impact("일본 은행주", "+", "A", "NIM 개선 기대", []),
        Impact("일본 국채", "-", "A", "금리 상승 → 채권 가격 하락", []),
    ]),
    ChainResult("일본금리인상", 2, [
        Impact("엔캐리 청산", "-", "A", "엔화 차입 투자 청산 → 글로벌 위험자산 매도", []),
        Impact("신흥국 주식", "-", "B", "캐리 트레이드 자금 유출", ["EEM"]),
        Impact("한국 주식", "-", "B", "아시아 자금 유출 동반", ["005930"]),
        Impact("미국 국채 금리", "+", "B", "일본 투자자 미국채 매도 가능", ["TLT"]),
    ]),
    ChainResult("일본금리인상", 3, [
        Impact("글로벌 변동성", "+", "C", "유동성 축소 → VIX 상승", []),
        Impact("한국 수출주", "+", "C", "엔화 강세 → 한국 수출 경쟁력 회복", ["005380", "000270"]),
    ]),
])

# ── 트럼프 관세 ──
_register("트럼프관세", [
    ChainResult("트럼프관세", 1, [
        Impact("중국 수출주", "-", "A", "대미 수출 관세 부과", []),
        Impact("미국 내수 소비재", "+", "B", "수입품 가격 상승 → 국내 제품 수혜", []),
        Impact("자동차", "-", "A", "수입차 관세 + 부품 비용 상승", ["005380", "000270"]),
        Impact("반도체", "-", "A", "기술 수출 규제 동반", ["005930", "000660", "TSM"]),
        Impact("농산물", "-", "B", "보복 관세 → 미국 농산물 수출 감소", []),
    ]),
    ChainResult("트럼프관세", 2, [
        Impact("베트남/인도 제조업", "+", "B", "중국 대체 생산기지로 수혜", []),
        Impact("해운/물류", "-", "B", "교역량 감소", []),
        Impact("미국 물가", "+", "B", "관세 → 수입품 가격 상승", []),
        Impact("금", "+", "B", "불확실성 증가 → 안전자산", ["GLD"]),
    ]),
    ChainResult("트럼프관세", 3, [
        Impact("글로벌 GDP", "-", "C", "무역 위축 → 성장 둔화", []),
        Impact("연준 딜레마", "+", "C", "인플레 vs 성장 둔화 → 정책 어려움", []),
        Impact("원/달러 환율", "+", "B", "무역분쟁 → 원화 약세", []),
    ]),
])

# ── 미국 정부 셧다운 ──
_register("정부셧다운", [
    ChainResult("정부셧다운", 1, [
        Impact("국방 관련주", "-", "B", "국방부 계약 지연", ["LMT", "RTX"]),
        Impact("관광/여행", "-", "B", "국립공원 폐쇄 등 관광 수요 감소", []),
        Impact("금", "+", "B", "정치 불확실성 → 안전자산", ["GLD"]),
        Impact("VIX", "+", "B", "시장 불확실성 증가", []),
    ]),
    ChainResult("정부셧다운", 2, [
        Impact("소비 위축", "-", "B", "공무원 급여 중단 → 소비 감소", ["WMT"]),
        Impact("신용등급", "-", "C", "장기화 시 미국 신용등급 우려", []),
        Impact("달러", "-", "B", "미국 신뢰도 하락", []),
    ]),
])

# ── 암호화폐 폭락 ──
_register("암호화폐폭락", [
    ChainResult("암호화폐폭락", 1, [
        Impact("가상자산 거래소", "-", "A", "거래량 감소 → 수수료 수입 감소", []),
        Impact("반도체(채굴용)", "-", "B", "GPU 채굴 수요 감소", ["NVDA", "AMD"]),
        Impact("블록체인 기업", "-", "B", "관련 투자 심리 악화", []),
    ]),
    ChainResult("암호화폐폭락", 2, [
        Impact("위험자산 전반", "-", "B", "투기 심리 위축 → 기술주 동반 조정 가능", []),
        Impact("전통 금융", "+", "C", "가상자산 → 전통 자산으로 자금 이동", ["JPM", "BAC"]),
        Impact("규제 강화", "+", "C", "각국 규제 가속화", []),
    ]),
])


# ─── 추적 엔진 ───

ALL_EVENTS = sorted(CAUSAL_GRAPH.keys())


def trace_chain(event: str) -> list[ChainResult] | None:
    key = event.replace(" ", "").replace("_", "")
    if key in CAUSAL_GRAPH:
        return CAUSAL_GRAPH[key]

    for k in CAUSAL_GRAPH:
        if key in k or k in key:
            return CAUSAL_GRAPH[k]

    return None


def search_by_ticker(ticker: str) -> list[dict]:
    results = []
    ticker = ticker.upper()
    for event_name, chains in CAUSAL_GRAPH.items():
        for chain in chains:
            for impact in chain.impacts:
                if ticker in [t.upper() for t in impact.tickers]:
                    results.append({
                        "event": event_name,
                        "depth": chain.depth,
                        "target": impact.target,
                        "direction": impact.direction,
                        "confidence": impact.confidence,
                        "reason": impact.reason,
                    })
    return results


def get_actionable(chains: list[ChainResult]) -> dict:
    longs = []
    shorts = []
    watch = []

    for chain in chains:
        for impact in chain.impacts:
            if not impact.tickers:
                continue
            entry = {
                "target": impact.target,
                "tickers": impact.tickers,
                "reason": impact.reason,
                "confidence": impact.confidence,
                "depth": chain.depth,
            }
            if impact.direction == "+" and impact.confidence in ("A", "B"):
                longs.append(entry)
            elif impact.direction == "-" and impact.confidence in ("A", "B"):
                shorts.append(entry)
            else:
                watch.append(entry)

    longs.sort(key=lambda x: (x["confidence"], x["depth"]))
    shorts.sort(key=lambda x: (x["confidence"], x["depth"]))

    return {"long": longs, "short": shorts, "watch": watch}
