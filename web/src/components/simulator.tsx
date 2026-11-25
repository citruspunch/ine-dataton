"use client";

import * as React from "react";

import { AboutCba } from "@/components/about-cba";
import { ControlPanel } from "@/components/control-panel";
import { GroupBreakdown } from "@/components/group-breakdown";
import { MethodAlert } from "@/components/method-alert";
import { MethodologyBreakAlert } from "@/components/methodology-break-alert";
import { NoticeBanner } from "@/components/notice-banner";
import { ProductsTable } from "@/components/products-table";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import { SummaryCards } from "@/components/summary-cards";
import {
  availableYears,
  basketData,
  findIpc,
  findMonth,
  latestPeriod,
  monthsForYear,
} from "@/lib/data";
import type { Area, Mode, VariationType } from "@/lib/types";

const DEFAULTS = {
  area: "Urbana" as Area,
  members: 4,
  mode: "total" as Mode,
  variation: "monthly" as VariationType,
  direct: false,
};

export function Simulator() {
  const [area, setArea] = React.useState<Area>(DEFAULTS.area);
  const [members, setMembers] = React.useState(DEFAULTS.members);
  const [period, setPeriod] = React.useState(() => latestPeriod(DEFAULTS.area));
  const [mode, setMode] = React.useState<Mode>(DEFAULTS.mode);
  const [variation, setVariation] = React.useState<VariationType>(
    DEFAULTS.variation,
  );
  const [direct, setDirect] = React.useState(DEFAULTS.direct);
  const [resetToken, setResetToken] = React.useState(0);

  const meta = basketData.meta;
  const month = React.useMemo(() => findMonth(area, period), [area, period]);
  const ipc = React.useMemo(() => findIpc(period), [period]);
  const years = React.useMemo(() => availableYears(area), [area]);
  const availableMonths = React.useMemo(
    () => monthsForYear(area, month.year),
    [area, month.year],
  );

  const year = Number(period.slice(0, 4));
  const monthNumber = Number(period.slice(5, 7));

  const handleYearChange = (nextYear: number) => {
    const months = monthsForYear(area, nextYear);
    const nextMonth = months.includes(monthNumber)
      ? monthNumber
      : months[months.length - 1];
    setPeriod(`${nextYear}-${String(nextMonth).padStart(2, "0")}`);
  };

  const handleMonthChange = (nextMonth: number) => {
    setPeriod(`${year}-${String(nextMonth).padStart(2, "0")}`);
  };

  const handleReset = () => {
    setArea(DEFAULTS.area);
    setMembers(DEFAULTS.members);
    setPeriod(latestPeriod(DEFAULTS.area));
    setMode(DEFAULTS.mode);
    setVariation(DEFAULTS.variation);
    setDirect(DEFAULTS.direct);
    setResetToken((current) => current + 1);
  };

  const crossBase =
    variation === "monthly" ? ipc.crossBaseMonthly : ipc.crossBaseInterannual;
  const showMethodAlert = direct && crossBase;

  return (
    <div className="flex min-h-dvh flex-col">
      <SiteHeader />

      <main className="mx-auto w-full max-w-[1180px] flex-1 px-5 py-5 sm:px-6 lg:px-8">
        <div className="space-y-4">
          <NoticeBanner />

          <div className="grid items-start gap-5 lg:grid-cols-[340px_minmax(0,1fr)]">
            <div className="space-y-4">
              <ControlPanel
                area={area}
                onAreaChange={setArea}
                members={members}
                onMembersChange={setMembers}
                year={year}
                month={monthNumber}
                years={years}
                availableMonths={availableMonths}
                onYearChange={handleYearChange}
                onMonthChange={handleMonthChange}
                mode={mode}
                onModeChange={setMode}
                variation={variation}
                onVariationChange={setVariation}
                direct={direct}
                onDirectChange={setDirect}
                onReset={handleReset}
                meta={meta}
              />
              <AboutCba />
            </div>

            <div className="min-w-0 space-y-4">
              <SummaryCards
                area={area}
                mode={mode}
                month={month}
                members={members}
                ipc={ipc}
                variation={variation}
                direct={direct}
              />

              <MethodAlert
                visible={showMethodAlert}
                ipc={ipc}
                month={month}
                variation={variation}
              />

              <MethodologyBreakAlert visible={period === meta.period.first} />

              <GroupBreakdown
                key={`groups-${resetToken}`}
                area={area}
                month={month}
                members={members}
                mode={mode}
              />

              <ProductsTable
                key={`products-${resetToken}`}
                area={area}
                month={month}
                members={members}
                mode={mode}
              />
            </div>
          </div>
        </div>
      </main>

      <SiteFooter />
    </div>
  );
}
