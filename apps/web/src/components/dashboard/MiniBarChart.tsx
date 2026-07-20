interface BarData {
  label: string;
  value: number;
}

interface MiniBarChartProps {
  data: BarData[];
  title: string;
}

export function MiniBarChart({ data, title }: MiniBarChartProps) {
  const max = Math.max(...data.map((d) => d.value), 1);

  return (
    <div className="bg-white rounded-xl border border-gray-100 p-5">
      <h3 className="text-sm font-semibold text-gray-700 mb-4">{title}</h3>
      <div className="flex items-end gap-2 h-24">
        {data.map((item, i) => (
          <div key={i} className="flex-1 flex flex-col items-center gap-1">
            <div className="w-full flex items-end justify-center" style={{ height: '80px' }}>
              <div
                className="w-full bg-[#1e3a8a] rounded-t-sm transition-all duration-500 min-h-[2px]"
                style={{ height: `${(item.value / max) * 80}px` }}
                title={`${item.label}: ${item.value}`}
              />
            </div>
            <span className="text-[10px] text-gray-400">{item.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
