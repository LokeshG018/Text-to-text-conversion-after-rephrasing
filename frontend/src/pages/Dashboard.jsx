// import { useEffect, useState } from 'react'
// import { Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
// import WordCloud from '../components/WordCloud.jsx'
// import { useAuth } from '../context/AuthContext.jsx'
// import * as api from '../services/api.js'

// export default function Dashboard() {
//   const { user } = useAuth()
//   const [s, setS] = useState(null)
//   const [texts, setTexts] = useState([])
//   useEffect(() => {
//     api.getSummary().then(setS)
//     api.getHistory({ limit: 100 }).then((h) => setTexts(h.map((x) => x.rephrased_text)))
//   }, [])
//   if (!s) return <p>Loading…</p>
//   const styles = Object.entries(s.styles).map(([style, count]) => ({ style, count }))
//   const trend = s.recent_similarity.map((r, i) => ({ n: i + 1, similarity: r.similarity != null ? +(r.similarity * 100).toFixed(1) : null }))
//   const Stat = ({ label, value }) => <div className="card"><p className="text-sm text-slate-500">{label}</p><p className="text-3xl font-bold">{value}</p></div>
//   return (
//     <div className="space-y-6">
//       <h1 className="text-2xl font-bold">Welcome, {user.name}</h1>
//       <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
//         <Stat label="Total rephrasings" value={s.total} />
//         <Stat label="Favourites" value={s.favorites} />
//         <Stat label="Avg similarity" value={s.avg_similarity != null ? `${(s.avg_similarity * 100).toFixed(1)}%` : '–'} />
//         <Stat label="Words processed" value={s.words_processed} />
//       </div>
//       <div className="grid gap-6 lg:grid-cols-2">
//         <div className="card"><h3 className="mb-3 font-semibold">Styles used</h3>
//           <ResponsiveContainer width="100%" height={240}><BarChart data={styles}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="style" /><YAxis allowDecimals={false} /><Tooltip />
//           <Bar dataKey="count" fill="#6366f1" />
//           {/* <Bar dataKey="count" fill="#6366f1" isAnimationActive={false}/> */}
//           </BarChart></ResponsiveContainer></div>
//         <div className="card"><h3 className="mb-3 font-semibold">Semantic similarity (last 20)</h3>
//           <ResponsiveContainer width="100%" height={240}><LineChart data={trend}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="n" /><YAxis domain={[0, 100]} /><Tooltip /><Line dataKey="similarity" stroke="#10b981" strokeWidth={2} /></LineChart></ResponsiveContainer></div>
//       </div>
//       <div className="card"><h3 className="mb-3 font-semibold">Word cloud of your rephrased texts</h3><WordCloud texts={texts} /></div>
//     </div>
//   )
// }
import { useEffect, useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import WordCloud from "../components/WordCloud.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import * as api from "../services/api.js";

export default function Dashboard() {
  const { user } = useAuth();
  const [summary, setSummary] = useState(null);
  const [texts, setTexts] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    let mounted = true;

    Promise.all([api.getSummary(), api.getHistory({ limit: 100 })])
      .then(([summaryData, historyData]) => {
        if (!mounted) return;

        setSummary(summaryData);
        setTexts(
          (historyData || [])
            .map((item) => item.rephrased_text)
            .filter(Boolean),
        );
      })
      .catch((err) => {
        if (mounted) {
          setError(err.message || "Unable to load dashboard data.");
        }
      });

    return () => {
      mounted = false;
    };
  }, []);

  if (error) {
    return <div className="card text-red-600">{error}</div>;
  }

  if (!summary) {
    return <p>Loading dashboard...</p>;
  }

  const styles = Object.entries(summary.styles || {}).map(([style, count]) => ({
    style,
    count: Number(count) || 0,
  }));

  const trend = (summary.recent_similarity || []).map((item, index) => ({
    n: index + 1,
    similarity:
      item.similarity != null
        ? Number((item.similarity * 100).toFixed(1))
        : null,
  }));

  function Stat({ label, value }) {
    return (
      <div className="card">
        <p className="text-sm text-slate-500">{label}</p>
        <p className="text-3xl font-bold">{value}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Welcome, {user?.name || "User"}</h1>

      {/* Dashboard statistics */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Total rephrasings" value={summary.total ?? 0} />
        <Stat label="Favourites" value={summary.favorites ?? 0} />
        <Stat
          label="Avg similarity"
          value={
            summary.avg_similarity != null
              ? `${(summary.avg_similarity * 100).toFixed(1)}%`
              : "–"
          }
        />
        <Stat label="Words processed" value={summary.words_processed ?? 0} />
      </div>

      {/* Charts */}
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="card">
          <h3 className="mb-3 font-semibold">Styles used</h3>

          <ResponsiveContainer width="100%" height={240}>
            {/* <BarChart data={styles}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="style" />
              <YAxis allowDecimals={false} />
              <Tooltip />

              <Bar
                dataKey="count"
                fill="#6366f1"
                isAnimationActive={false}
              />
            </BarChart> */}
            <div className="card">
              <h3 className="mb-4 font-semibold">Styles used</h3>

              {styles.length === 0 ? (
                <p className="text-sm text-slate-500">
                  No style usage data yet. Generate some rephrased text first.
                </p>
              ) : (
                <div className="space-y-4">
                  {styles.map(({ style, count }) => {
                    const maxCount = Math.max(
                      1,
                      ...styles.map((item) => item.count),
                    );

                    const percentage = Math.min(100, (count / maxCount) * 100);

                    return (
                      <div key={style}>
                        <div className="mb-1 flex justify-between text-sm">
                          <span className="capitalize">{style}</span>
                          <span className="font-semibold">{count}</span>
                        </div>

                        <div className="h-3 w-full overflow-hidden rounded-full bg-slate-200">
                          <div
                            className="h-full rounded-full bg-indigo-500"
                            style={{ width: `${percentage}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <h3 className="mb-3 font-semibold">Semantic similarity (last 20)</h3>

          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={trend}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="n" />
              <YAxis domain={[0, 100]} />
              <Tooltip />

              <Line
                type="monotone"
                dataKey="similarity"
                stroke="#10b981"
                strokeWidth={2}
                dot={false}
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Word cloud */}
      <div className="card">
        <h3 className="mb-3 font-semibold">
          Word cloud of your rephrased texts
        </h3>

        <WordCloud texts={texts} />
      </div>
    </div>
  );
}
