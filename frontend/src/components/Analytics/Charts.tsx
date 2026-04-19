"use client";

import React from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  BarChart as ReBarChart,
  Bar,
  Legend,
} from "recharts";

type DayCount = { day: string; count: number };

function normalize(data: DayCount[]) {
  // Ensure we have a stable x-axis order and friendly labels
  return data.map((d) => ({ ...d, label: d.day }));
}

export function MeetingsLine({ data }: { data: DayCount[] }) {
  const series = normalize(data);

  return (
    <div className="w-full h-64">
      <ResponsiveContainer>
        <LineChart data={series} margin={{ top: 8, right: 16, left: -12, bottom: 6 }}>
          <defs>
            <linearGradient id="g1" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--info)" stopOpacity={0.18} />
              <stop offset="100%" stopColor="var(--info)" stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(15,23,42,0.04)" />
          <XAxis dataKey="label" tick={{ fill: "var(--text-muted)", fontSize: 12 }} />
          <YAxis tick={{ fill: "var(--text-muted)", fontSize: 12 }} allowDecimals={false} />
          <Tooltip contentStyle={{ borderRadius: 8 }} />
          <Area type="monotone" dataKey="count" stroke="var(--info)" fill="url(#g1)" strokeWidth={0} activeDot={{ r: 5 }} />
          <Line type="monotone" dataKey="count" stroke="var(--info)" strokeWidth={2.2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export function MeetingsBar({ data }: { data: DayCount[] }) {
  const series = normalize(data);

  return (
    <div className="w-full h-56">
      <ResponsiveContainer>
        <ReBarChart data={series} margin={{ top: 6, right: 8, left: -10, bottom: 6 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(15,23,42,0.04)" />
          <XAxis dataKey="label" tick={{ fill: "var(--text-muted)", fontSize: 12 }} />
          <YAxis tick={{ fill: "var(--text-muted)", fontSize: 12 }} allowDecimals={false} />
          <Tooltip contentStyle={{ borderRadius: 8 }} />
          <Bar dataKey="count" fill="var(--peach)" radius={[6,6,0,0]} />
        </ReBarChart>
      </ResponsiveContainer>
    </div>
  );
}

export default {
  MeetingsLine,
  MeetingsBar,
};
