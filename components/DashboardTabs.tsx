"use client";

// components/DashboardTabs.js — Les 5 onglets du tableau de bord
// (Vue d'ensemble, Prévisions, Anomalies, Catégories, Modèles ML)

import { useMemo } from "react";
import {
  ResponsiveContainer, ComposedChart, BarChart, Bar, AreaChart, Area,
  Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ReferenceDot, Cell,
} from "recharts";

const COLORS = {
  green: "#16a34a",
  greenLight: "#dcfce7",
  blue: "#2563eb",
  movavg: "#8b5cf6",
  trend: "#f97316",
  red: "#ef4444",
  text: "#111827",
  subtle: "#6b7280",
  border: "#e5e7eb",
};

const MODEL_COLORS: Record<string, string> = {
  linear: "#2563eb",
  polynomial: "#f97316",
  random_forest: "#16a34a",
  arima: "#8b5cf6",
  ensemble: "#dc2626",
};

export const fmtK = (n: unknown) => {
  if (n === null || n === undefined) return "—";
  const v = Number(n);
  if (Math.abs(v) >= 1e6) return (v / 1e6).toFixed(2) + "M";
  if (Math.abs(v) >= 1e3) return (v / 1e3).toFixed(1) + "K";
  return v.toFixed(0);
};

const fmtPct = (v: number) => (v > 0 ? "+" : "") + Number(v).toFixed(1) + "%";

// ============================================================
// ONGLET 1 — Vue d'ensemble
// ============================================================
export function OverviewTab({ result }: { result: any }) {
  const linear = result.models.find((m) => m.key === "linear");

  const chartData = useMemo(() => {
    const hist = result.series.map((s, i) => ({
      label: s.period,
      ventes: s.value,
      movingAverage: result.moving_average[i],
      trend: linear ? linear.fitted[i] : null,
    }));
    const fc = result.forecast_labels.map((label, i) => ({
      label,
      forecast: result.ensemble.forecast[i],
    }));
    return [...hist, ...fc];
  }, [result, linear]);

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-base font-semibold text-gray-900">
          Évolution des ventes, tendance et prévisions
        </h3>
        <p className="text-xs text-gray-500 mt-1">
          {result.stats.periods} périodes — granularité {result.granularity}
        </p>
        <div className="h-80 mt-4">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border} vertical={false} />
              <XAxis
                dataKey="label"
                tick={{ fontSize: 11, fill: COLORS.subtle }}
                interval={Math.max(1, Math.floor(chartData.length / 12))}
              />
              <YAxis tick={{ fontSize: 11, fill: COLORS.subtle }} tickFormatter={fmtK} />
              <Tooltip formatter={(v) => fmtK(v)} contentStyle={{ fontSize: 12, borderRadius: 6 }} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Area type="monotone" dataKey="ventes" name="Ventes réelles"
                stroke={COLORS.green} fill={COLORS.greenLight} strokeWidth={2} />
              <Line type="monotone" dataKey="movingAverage" name="Moyenne mobile"
                stroke={COLORS.movavg} strokeWidth={1.5} strokeDasharray="4 3" dot={false} />
              <Line type="monotone" dataKey="trend" name="Tendance linéaire"
                stroke={COLORS.trend} strokeWidth={1.5} strokeDasharray="6 4" dot={false} />
              <Line type="monotone" dataKey="forecast" name="Prévision (ensemble)"
                stroke={COLORS.blue} strokeWidth={2} dot={{ r: 4, fill: COLORS.blue }} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-base font-semibold text-gray-900 mb-4">
            Statistiques descriptives
          </h3>
          <dl className="text-sm divide-y divide-gray-100">
            <StatRow k="Total" v={fmtK(result.stats.total)} />
            <StatRow k="Moyenne par période" v={fmtK(result.stats.mean)} />
            <StatRow k="Minimum" v={fmtK(result.stats.min)} />
            <StatRow k="Maximum" v={fmtK(result.stats.max)} />
            <StatRow k="Croissance" v={fmtPct(result.stats.growth_percent)} />
            <StatRow k="Périodes analysées" v={result.stats.periods} />
          </dl>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-base font-semibold text-gray-900 mb-4">
            Nettoyage des données
          </h3>
          <dl className="text-sm divide-y divide-gray-100">
            <StatRow k="Lignes importées" v={result._cleaning?.rows_before ?? "—"} />
            <StatRow k="Doublons retirés" v={result._cleaning?.duplicates_removed ?? "—"} />
            <StatRow k="Dates invalides" v={result._cleaning?.invalid_dates_removed ?? "—"} />
            <StatRow k="Valeurs invalides" v={result._cleaning?.invalid_values_removed ?? "—"} />
            <StatRow k="Lignes exploitées" v={result._cleaning?.rows_after ?? "—"} />
          </dl>
        </div>
      </div>
    </div>
  );
}

function StatRow({ k, v }: { k: string; v: any }) {
  return (
    <div className="flex justify-between py-2.5">
      <dt className="text-gray-600">{k}</dt>
      <dd className="font-medium text-gray-900">{v}</dd>
    </div>
  );
}

// ============================================================
// ONGLET 2 — Prévisions
// ============================================================
export function ForecastTab({ result }: { result: any }) {
  const last6 = result.series.slice(-6).map((s) => ({
    label: s.period, value: s.value, kind: "real",
  }));
  const fc = result.forecast_labels.map((label, i) => ({
    label, value: result.ensemble.forecast[i], kind: "forecast",
  }));
  const chartData = [...last6, ...fc];

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-base font-semibold text-gray-900">
          Ventes réelles et prévisions
        </h3>
        <p className="text-xs text-gray-500 mt-1">
          6 dernières périodes et {result.horizon} prévisions (ensemble pondéré)
        </p>
        <div className="h-80 mt-4">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border} vertical={false} />
              <XAxis dataKey="label" tick={{ fontSize: 11, fill: COLORS.subtle }} />
              <YAxis tickFormatter={fmtK} tick={{ fontSize: 11, fill: COLORS.subtle }} />
              <Tooltip formatter={(v) => fmtK(v)} contentStyle={{ fontSize: 12, borderRadius: 6 }} />
              <Bar dataKey="value" radius={[3, 3, 0, 0]}>
                {chartData.map((d, i) => (
                  <Cell key={i} fill={d.kind === "real" ? COLORS.green : COLORS.blue} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="flex gap-4 mt-2 text-xs">
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded" style={{ background: COLORS.green }} />
            Ventes réelles
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded" style={{ background: COLORS.blue }} />
            Prévision
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
        {result.forecast_labels.map((label, i) => (
          <div key={label} className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="text-xs text-gray-500">{label}</div>
            <div className="text-2xl font-semibold mt-1" style={{ color: COLORS.blue }}>
              {fmtK(result.ensemble.forecast[i])}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ============================================================
// ONGLET 3 — Anomalies
// ============================================================
export function AnomaliesTab({ result }: { result: any }) {
  const chartData = result.series.map((s) => ({
    label: s.period, sales: s.value,
  }));

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-base font-semibold text-gray-900">
          Détection des anomalies
        </h3>
        <p className="text-xs text-gray-500 mt-1">
          Méthode Z-score, seuil 2σ —{" "}
          <span className="text-orange-600 font-medium">
            {result.anomalies.length} anomalie{result.anomalies.length > 1 ? "s" : ""} détectée
            {result.anomalies.length > 1 ? "s" : ""}
          </span>
        </p>
        <div className="h-80 mt-4">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border} vertical={false} />
              <XAxis dataKey="label" tick={{ fontSize: 11, fill: COLORS.subtle }}
                interval={Math.max(1, Math.floor(chartData.length / 12))} />
              <YAxis tickFormatter={fmtK} tick={{ fontSize: 11, fill: COLORS.subtle }} />
              <Tooltip formatter={(v) => fmtK(v)} contentStyle={{ fontSize: 12, borderRadius: 6 }} />
              <Area type="monotone" dataKey="sales" name="Ventes"
                stroke={COLORS.green} fill={COLORS.greenLight} strokeWidth={2} />
              {result.anomalies.map((a) => (
                <ReferenceDot key={a.period} x={a.period} y={a.value}
                  r={6} fill={COLORS.red} stroke="#fff" strokeWidth={2} />
              ))}
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-base font-semibold text-gray-900 mb-4">
          Périodes anormales identifiées
        </h3>
        {result.anomalies.length === 0 ? (
          <p className="text-sm text-gray-500">Aucune anomalie détectée.</p>
        ) : (
          <div className="divide-y divide-gray-100">
            {result.anomalies.map((a) => (
              <div key={a.period} className="flex justify-between items-center py-3">
                <div className="text-sm">
                  <span className="text-gray-600">Période : </span>
                  <span className="font-semibold">{a.period}</span>
                  <span className="ml-3 text-xs text-gray-500">z = {a.zscore}</span>
                </div>
                <div className="text-sm font-medium" style={{ color: COLORS.red }}>
                  {fmtK(a.value)}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ============================================================
// ONGLET 4 — Catégories
// ============================================================
export function CategoriesTab({ result }: { result: any }) {
  if (!result.category_breakdown) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-8 text-center text-gray-500 text-sm">
        Aucune colonne de catégorie sélectionnée pour ce dataset.
      </div>
    );
  }

  const data = Object.entries(result.category_breakdown as Record<string, any>)
    .map(([name, v]) => ({ name, value: v.total, count: v.count }))
    .sort((a, b) => b.value - a.value);
  const total = data.reduce((s, d) => s + d.value, 0);

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-base font-semibold text-gray-900 mb-4">
          Ventes par catégorie
        </h3>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} layout="vertical"
              margin={{ top: 10, right: 30, left: 80, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border} horizontal={false} />
              <XAxis type="number" tickFormatter={fmtK} tick={{ fontSize: 11, fill: COLORS.subtle }} />
              <YAxis type="category" dataKey="name" tick={{ fontSize: 12, fill: COLORS.text }} width={110} />
              <Tooltip formatter={(v) => fmtK(v)} contentStyle={{ fontSize: 12, borderRadius: 6 }} />
              <Bar dataKey="value" fill={COLORS.green} radius={[0, 3, 3, 0]} barSize={26} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {data.map((d) => {
          const pct = total ? (d.value / total) * 100 : 0;
          return (
            <div key={d.name} className="bg-white rounded-lg border border-gray-200 p-4">
              <div className="text-sm text-gray-600">{d.name}</div>
              <div className="text-2xl font-semibold mt-1">{fmtK(d.value)}</div>
              <div className="w-full h-1 bg-gray-100 rounded-full mt-3 overflow-hidden">
                <div className="h-full rounded-full"
                  style={{ width: `${pct}%`, background: COLORS.green }} />
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {pct.toFixed(1)}% du total — {d.count} transactions
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ============================================================
// ONGLET 5 — Modèles ML (comparaison des 4 algorithmes)
// ============================================================
export function ModelsTab({ result }: { result: any }) {
  // Graphe : prévisions des 4 modèles côte à côte
  const chartData = result.forecast_labels.map((label, i) => {
    const row: Record<string, any> = { label };
    result.models.forEach((m) => {
      row[m.key] = m.forecast[i];
    });
    row.ensemble = result.ensemble.forecast[i];
    return row;
  });

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-base font-semibold text-gray-900">
          Comparaison des modèles de prévision
        </h3>
        <p className="text-xs text-gray-500 mt-1">
          Quatre algorithmes de Machine Learning et leur ensemble pondéré
        </p>
        <div className="h-80 mt-4">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border} vertical={false} />
              <XAxis dataKey="label" tick={{ fontSize: 11, fill: COLORS.subtle }} />
              <YAxis tickFormatter={fmtK} tick={{ fontSize: 11, fill: COLORS.subtle }} />
              <Tooltip formatter={(v) => fmtK(v)} contentStyle={{ fontSize: 12, borderRadius: 6 }} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              {result.models.map((m) => (
                <Line key={m.key} type="monotone" dataKey={m.key} name={m.name}
                  stroke={MODEL_COLORS[m.key]} strokeWidth={1.5} dot={{ r: 3 }} />
              ))}
              <Line type="monotone" dataKey="ensemble" name="Ensemble"
                stroke={MODEL_COLORS.ensemble} strokeWidth={2.5} dot={{ r: 4 }} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-base font-semibold text-gray-900 mb-4">
          Métriques de qualité des modèles
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 text-left">
                <th className="py-2 pr-4 font-medium text-gray-600">Modèle</th>
                <th className="py-2 pr-4 font-medium text-gray-600">R²</th>
                <th className="py-2 pr-4 font-medium text-gray-600">MAE</th>
                <th className="py-2 pr-4 font-medium text-gray-600">RMSE</th>
                <th className="py-2 pr-4 font-medium text-gray-600">Poids ensemble</th>
              </tr>
            </thead>
            <tbody>
              {result.models.map((m) => {
                const isBest = m.key === result.best_model;
                return (
                  <tr key={m.key} className="border-b border-gray-50">
                    <td className="py-2.5 pr-4">
                      <span className="font-medium text-gray-900">{m.name}</span>
                      {isBest && (
                        <span className="ml-2 text-xs px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-700">
                          meilleur
                        </span>
                      )}
                    </td>
                    <td className="py-2.5 pr-4 text-gray-700">{m.metrics.r2 ?? "—"}</td>
                    <td className="py-2.5 pr-4 text-gray-700">{fmtK(m.metrics.mae)}</td>
                    <td className="py-2.5 pr-4 text-gray-700">{fmtK(m.metrics.rmse)}</td>
                    <td className="py-2.5 pr-4 text-gray-700">
                      {result.ensemble.weights[m.key] !== undefined
                        ? (result.ensemble.weights[m.key] * 100).toFixed(1) + "%"
                        : "—"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <p className="mt-3 text-xs text-gray-500">
          Le R² mesure la qualité de l'ajustement (plus proche de 1, meilleur).
          L'ensemble combine les modèles en pondérant par leur R².
        </p>
      </div>
    </div>
  );
}





