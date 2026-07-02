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
  { year: 2026, age: 26, phase: "P0-P1", phaseName: "생존-저축", pillTone: "warning", rowTone: "danger", monthlyNet: 4331351, monthlySave: 102777, monthlyFree: 102777, netWorth: 17928921, events: "5/18 입사 · 여친 소득 8월~" },
  { year: 2027, age: 27, phase: "P1", phaseName: "저축전성", pillTone: "warning", rowTone: "danger", monthlyNet: 4886473, monthlySave: 2185081, monthlyFree: 0, netWorth: 41871217, events: "TOPIK6 · 집자금 4천" },
  { year: 2028, age: 28, phase: "P2", phaseName: "혼인", pillTone: "warning", rowTone: "warning", monthlyNet: 5081932, monthlySave: 2185081, monthlyFree: 0, netWorth: 66418978, events: "혼인 · 신혼특공" },
  { year: 2029, age: 29, phase: "P3", phaseName: "분양", pillTone: "warning", rowTone: "warning", monthlyNet: 5285209, monthlySave: 2185081, monthlyFree: 0, netWorth: 91587513, events: "카카오 상환 · 계약금" },
  { year: 2030, age: 30, phase: "P3", phaseName: "대기", pillTone: "warning", rowTone: "warning", monthlyNet: 5496617, monthlySave: 2185081, monthlyFree: 0, netWorth: 117392522, events: "입주 자금 1억" },
  { year: 2031, age: 31, phase: "P4", phaseName: "입주", pillTone: "info", rowTone: "info", monthlyNet: 4698532, monthlySave: 1485081, monthlyFree: 735081, netWorth: 143990789, events: "운정 입주 · 여유 74만" },
  { year: 2032, age: 32, phase: "P4", phaseName: "적응", pillTone: "info", rowTone: "info", monthlyNet: 4886473, monthlySave: 1673022, monthlyFree: 923022, netWorth: 171510410, events: "대출 적응" },
  { year: 2033, age: 33, phase: "P5", phaseName: "출산", pillTone: "success", rowTone: "success", monthlyNet: 5081932, monthlySave: 1018481, monthlyFree: 368481, netWorth: 191787772, events: "출산 · ISA 조정" },
  { year: 2034, age: 34, phase: "P5", phaseName: "안정", pillTone: "success", rowTone: "success", monthlyNet: 5285209, monthlySave: 1221758, monthlyFree: 571758, netWorth: 215052500, events: "여유 회복" },
  { year: 2035, age: 35, phase: "P5", phaseName: "안정", pillTone: "success", rowTone: "success", monthlyNet: 5496617, monthlySave: 1433166, monthlyFree: 783166, netWorth: 241479027, events: "숨통 안정" },
  { year: 2036, age: 36, phase: "P6", phaseName: "일상", pillTone: "neutral", rowTone: "neutral", monthlyNet: 5716482, monthlySave: 1653031, monthlyFree: 1003031, netWorth: 271250153, events: "중장기" },
  { year: 2040, age: 40, phase: "P6", phaseName: "일상", pillTone: "neutral", rowTone: "neutral", monthlyNet: 6687476, monthlySave: 2624025, monthlyFree: 1974025, netWorth: 427750459, events: "30대 후반 점검" },
];

const MILESTONES = [
  { year: 2026, offset: 0.65, label: "생존", sub: "7월" },
  { year: 2026, offset: 0.85, label: "저축", sub: "219만" },
  { year: 2027, offset: 0.15, label: "비자", sub: "D-10" },
  { year: 2028, offset: 0.4, label: "혼인", sub: "F-6" },
  { year: 2029, offset: 0.65, label: "분양", sub: "계약" },
  { year: 2031, offset: 0.4, label: "입주", sub: "59형" },
  { year: 2033, offset: 0.4, label: "출산", sub: "권장" },
  { year: 2036, offset: 0.5, label: "일상", sub: "100만" },
];

export default function LifeLineCanvas() {
  const theme = useHostTheme();
  const netWorthData = YEARS.map((y) => ({ x: y.year, y: y.netWorth / 10_000 }));
  const saveData = YEARS.map((y) => ({ x: y.year, y: y.monthlySave / 10_000 }));

  return (
    <Stack gap={20} style={{ padding: 20, maxWidth: 960 }}>
      <Stack gap={4}>
        <H1>인생라인 · 재무 투영</H1>
        <Text tone="secondary">2026~2040 · 운정 59형 · 2인 가구</Text>
      </Stack>

      <Row gap={12} wrap>
        <Stat label="허리띠" value="~5년" tone="danger" />
        <Stat label="정규 저축" value="219만/월" tone="warning" />
        <Stat label="입주 후 여유" value="74만" tone="success" />
        <Stat label="2040 순자산" value="~4.28억" tone="info" />
      </Row>

      <Callout tone="info" title="허리띠는 죽을 때까지가 아님">
        2026.07~2031 입주 전이 최대 조임. 입주 후 집마련 중단으로 월 여유 ~74만 회복.
      </Callout>

      <Grid columns={2} gap={16}>
        <Card>
          <CardHeader trailing="만원">순자산 추이</CardHeader>
          <CardBody>
            <LineChart
              data={netWorthData}
              xLabel="연도"
              yLabel="순자산(만)"
              height={220}
              markers={MILESTONES.map((m) => ({
                x: m.year + m.offset,
                label: m.label,
                sublabel: m.sub,
              }))}
            />
          </CardBody>
        </Card>
        <Card>
          <CardHeader trailing="만원/월">월 저축 vs 여유</CardHeader>
          <CardBody>
            <BarChart
              categories={YEARS.filter((y) => y.year >= 2026 && y.year <= 2036).map((y) => String(y.year))}
              series={[
                { name: "저축", data: YEARS.filter((y) => y.year >= 2026 && y.year <= 2036).map((y) => Math.round(y.monthlySave / 10_000)), tone: "info" },
                { name: "여유", data: YEARS.filter((y) => y.year >= 2026 && y.year <= 2036).map((y) => Math.round(y.monthlyFree / 10_000)), tone: "success" },
              ]}
              height={220}
            />
          </CardBody>
        </Card>
      </Grid>

      <Card>
        <CardHeader trailing="P0~P6">연도별 상세</CardHeader>
        <CardBody>
          <Table
            headers={["연도", "나이", "페이즈", "세후", "저축", "여유", "순자산", "이벤트"]}
            rows={YEARS.map((y) => [
              y.year,
              y.age,
              <Pill tone={y.pillTone}>{y.phaseName}</Pill>,
              `${Math.round(y.monthlyNet / 10_000)}만`,
              `${Math.round(y.monthlySave / 10_000)}만`,
              y.monthlyFree > 0 ? `${Math.round(y.monthlyFree / 10_000)}만` : "0",
              `${Math.round(y.netWorth / 10_000).toLocaleString()}만`,
              y.events,
            ])}
            rowTone={YEARS.map((y) => y.rowTone)}
            columnAlign={["left", "right", "left", "right", "right", "right", "right", "left"]}
            striped
          />
        </CardBody>
      </Card>
    </Stack>
  );
}
