import {
  BarChart,
  Callout,
  Card,
  CardBody,
  CardHeader,
  Grid,
  H1,
  LineChart,
  Pill,
  Row,
  Stack,
  Stat,
  Table,
  Text,
  useHostTheme,
  type CanvasHostTheme,
  type PillTone,
  type TableRowTone,
} from "cursor/canvas";

type YearRow = {
  year: number;
  age: number;
  phase: string;
  phaseName: string;
  pillTone: PillTone;
  rowTone: TableRowTone;
  monthlyNet: number;
  monthlySave: number;
  monthlyFree: number;
  netWorth: number;
  events: string;
};

const YEARS: YearRow[] = [
  { year: 2026, age: 26, phase: "P0-P1", phaseName: "생존-저축", pillTone: "warning", rowTone: "danger", monthlyNet: 4083333, monthlySave: 614520, monthlyFree: 614520, netWorth: 16279689, events: "7월 생존 · 8월 분배" },
  { year: 2027, age: 27, phase: "P1", phaseName: "저축전성", pillTone: "warning", rowTone: "danger", monthlyNet: 4576000, monthlySave: 2078032, monthlyFree: 0, netWorth: 38880869, events: "TOPIK6 · 집자금 4천" },
  { year: 2028, age: 28, phase: "P2", phaseName: "혼인", pillTone: "warning", rowTone: "warning", monthlyNet: 4759040, monthlySave: 2078032, monthlyFree: 0, netWorth: 62053598, events: "혼인 · 신혼특공" },
  { year: 2029, age: 29, phase: "P3", phaseName: "분양", pillTone: "warning", rowTone: "warning", monthlyNet: 4949401, monthlySave: 2078032, monthlyFree: 0, netWorth: 85812330, events: "카카오 상환 · 계약금" },
  { year: 2030, age: 30, phase: "P3", phaseName: "대기", pillTone: "warning", rowTone: "warning", monthlyNet: 5147377, monthlySave: 2078032, monthlyFree: 0, netWorth: 110171884, events: "입주 자금 1억" },
  { year: 2031, age: 31, phase: "P4", phaseName: "입주", pillTone: "info", rowTone: "info", monthlyNet: 4400000, monthlySave: 1378032, monthlyFree: 628032, netWorth: 136770151, events: "운정 입주 · 여유 63만" },
  { year: 2032, age: 32, phase: "P4", phaseName: "적응", pillTone: "info", rowTone: "info", monthlyNet: 4576000, monthlySave: 1554032, monthlyFree: 804032, netWorth: 162662818, events: "대출 적응" },
  { year: 2033, age: 33, phase: "P5", phaseName: "출산", pillTone: "success", rowTone: "success", monthlyNet: 4759040, monthlySave: 887072, monthlyFree: 237072, netWorth: 181121335, events: "출산 · ISA 조정" },
  { year: 2034, age: 34, phase: "P5", phaseName: "안정", pillTone: "success", rowTone: "success", monthlyNet: 4949401, monthlySave: 1077433, monthlyFree: 427433, netWorth: 202364442, events: "여유 회복" },
  { year: 2035, age: 35, phase: "P5", phaseName: "안정", pillTone: "success", rowTone: "success", monthlyNet: 5147377, monthlySave: 1275409, monthlyFree: 625409, netWorth: 226555181, events: "숨통 안정" },
  { year: 2036, age: 36, phase: "P6", phaseName: "일상", pillTone: "neutral", rowTone: "neutral", monthlyNet: 5353272, monthlySave: 1481304, monthlyFree: 831304, netWorth: 253864405, events: "중장기" },
  { year: 2040, age: 40, phase: "P6", phaseName: "일상", pillTone: "neutral", rowTone: "neutral", monthlyNet: 6262571, monthlySave: 2390603, monthlyFree: 1740603, netWorth: 397997021, events: "30대 후반 점검" },
];

const MILESTONES = [
  { year: 2026, offset: 0.65, label: "생존", sub: "7월" },
  { year: 2026, offset: 0.85, label: "저축", sub: "208만" },
  { year: 2027, offset: 0.15, label: "비자", sub: "D-10" },
  { year: 2028, offset: 0.4, label: "혼인", sub: "F-6" },
  { year: 2029, offset: 0.65, label: "분양", sub: "계약" },
  { year: 2031, offset: 0.4, label: "입주", sub: "59형" },
  { year: 2033, offset: 0.4, label: "출산", sub: "권장" },
  { year: 2036, offset: 0.5, label: "일상", sub: "83만" },
];

const BANDS: { from: number; to: number; label: string; colorKey: keyof CanvasHostTheme["category"] }[] = [
  { from: 2026, to: 2028.5, label: "스프린트", colorKey: "orange" },
  { from: 2028.5, to: 2031, label: "혼인·분양", colorKey: "yellow" },
  { from: 2031, to: 2033, label: "입주", colorKey: "blue" },
  { from: 2033, to: 2036, label: "안정", colorKey: "green" },
  { from: 2036, to: 2040, label: "일상", colorKey: "gray" },
];

function fmtMan(won: number): string {
  if (won >= 100_000_000) return `${(won / 100_000_000).toFixed(1)}억`;
  return `${Math.round(won / 10_000)}만`;
}

function LifeTimeline({ theme }: { theme: CanvasHostTheme }) {
  const start = 2026;
  const end = 2040;
  const width = 920;
  const height = 120;
  const padX = 48;
  const y = 56;

  const xForYear = (year: number) =>
    padX + ((year - start) / (end - start)) * (width - padX * 2);

  return (
    <svg width="100%" viewBox={`0 0 ${width} ${height}`} style={{ display: "block" }}>
      {BANDS.map((band) => {
        const x1 = xForYear(band.from);
        const x2 = xForYear(band.to);
        return (
          <g key={band.label}>
            <rect
              x={x1}
              y={12}
              width={x2 - x1}
              height={height - 24}
              fill={theme.category[band.colorKey]}
              opacity={0.15}
              rx={4}
            />
            <text
              x={(x1 + x2) / 2}
              y={22}
              textAnchor="middle"
              fill={theme.text.tertiary}
              fontSize={10}
            >
              {band.label}
            </text>
          </g>
        );
      })}
      <line
        x1={padX}
        y1={y}
        x2={width - padX}
        y2={y}
        stroke={theme.stroke.secondary}
        strokeWidth={2}
      />
      {[2026, 2028, 2030, 2032, 2034, 2036, 2040].map((year) => (
        <g key={year}>
          <line
            x1={xForYear(year)}
            y1={y - 6}
            x2={xForYear(year)}
            y2={y + 6}
            stroke={theme.stroke.primary}
            strokeWidth={1}
          />
          <text
            x={xForYear(year)}
            y={y + 22}
            textAnchor="middle"
            fill={theme.text.secondary}
            fontSize={10}
          >
            {year}
          </text>
        </g>
      ))}
      {MILESTONES.map((m) => {
        const x = xForYear(m.year + m.offset);
        const row = YEARS.find((yr) => yr.year === m.year);
        const dot = row?.pillTone === "warning"
          ? theme.category.orange
          : row?.pillTone === "info"
            ? theme.category.blue
            : row?.pillTone === "success"
              ? theme.category.green
              : theme.category.gray;
        return (
          <g key={`${m.year}-${m.label}`}>
            <circle cx={x} cy={y} r={7} fill={theme.bg.elevated} stroke={dot} strokeWidth={2.5} />
            <text x={x} y={y - 14} textAnchor="middle" fill={theme.text.primary} fontSize={10} fontWeight={600}>
              {m.label}
            </text>
            <text x={x} y={y - 3} textAnchor="middle" fill={theme.text.tertiary} fontSize={8}>
              {m.sub}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

export default function LifeLineCanvas() {
  const theme = useHostTheme();
  const categories = YEARS.map((y) => String(y.year));
  const netWorthMan = YEARS.map((y) => Math.round(y.netWorth / 10_000));
  const monthlyFreeMan = YEARS.map((y) => Math.round(y.monthlyFree / 10_000));
  const monthlySaveMan = YEARS.map((y) => Math.round(y.monthlySave / 10_000));
  const y2031 = YEARS.find((y) => y.year === 2031)!;
  const y2040 = YEARS.find((y) => y.year === 2040)!;

  return (
    <Stack gap={20} style={{ padding: 20, maxWidth: 960 }}>
      <Stack gap={4}>
        <H1>종합 인생라인</H1>
        <Text tone="secondary">현철·여친 · 운정 59형 · 2026-2040 · 소득 연 4% 성장 가정</Text>
        <Text tone="tertiary" size="small">Source: config/life_timeline.py · sheets/종합인생라인.xlsx</Text>
      </Stack>

      <Row gap={12} wrap>
        <Stat label="허리띠 최대" value="~2031" tone="danger" />
        <Stat label="입주" value="2031" tone="info" />
        <Stat label="입주 후 여유" value="63만/월" tone="success" />
        <Stat label="출산 권장" value="2033" tone="warning" />
        <Stat label="2040 순자산" value={fmtMan(y2040.netWorth)} tone="info" />
      </Row>

      <Card>
        <CardHeader trailing="마일스톤">인생선 2026 → 2040</CardHeader>
        <CardBody>
          <LifeTimeline theme={theme} />
        </CardBody>
      </Card>

      <Grid columns={1} gap={16}>
        <Card>
          <CardHeader trailing="만원">순자산 추이</CardHeader>
          <CardBody>
            <LineChart
              categories={categories}
              series={[{ name: "순자산", data: netWorthMan, tone: "info" }]}
              height={220}
              fill
              beginAtZero
              valueSuffix="만"
              referenceLines={[
                { value: Math.round(y2031.netWorth / 10_000), label: "입주 2031", tone: "warning" },
              ]}
            />
          </CardBody>
        </Card>

        <Card>
          <CardHeader trailing="만원/월">월 현금흐름</CardHeader>
          <CardBody>
            <BarChart
              categories={categories}
              series={[
                { name: "저축+여유", data: monthlySaveMan, tone: "info" },
                { name: "여유", data: monthlyFreeMan, tone: "success" },
              ]}
              height={220}
              stacked
              beginAtZero
              valueSuffix="만"
            />
          </CardBody>
        </Card>
      </Grid>

      <Callout tone="info" title="핵심">
        2026-2030은 월 여유 0에 가깝지만 순자산은 1.6천만에서 1.1억으로 성장합니다. 2031 입주 후 집마련
        133만이 끊기며 여유 63만이 생기고, 2033 출산 직후 1년은 다시 빡빡해도 2034부터 소득 성장으로 회복합니다.
      </Callout>

      <Table
        headers={["연도", "나이", "페이즈", "단계", "순자산", "월 여유", "이벤트"]}
        rows={YEARS.map((y) => [
          y.year,
          `만${y.age}`,
          y.phase,
          <Pill tone={y.pillTone}>{y.phaseName}</Pill>,
          fmtMan(y.netWorth),
          y.monthlyFree === 0 ? "0" : fmtMan(y.monthlyFree),
          y.events,
        ])}
        rowTone={YEARS.map((y) => y.rowTone)}
        columnAlign={["left", "left", "left", "left", "right", "right", "left"]}
        striped
      />
    </Stack>
  );
}
