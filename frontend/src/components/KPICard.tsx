interface Props {
  label: string
  value: string
  sub?: string
  help?: string
}

export default function KPICard({ label, value, sub, help }: Props) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
      <div className="flex items-start justify-between gap-1">
        <p className="text-xs text-gray-500 font-medium leading-tight">{label}</p>
        {help && (
          <span title={help} className="text-gray-300 text-xs cursor-default select-none">?</span>
        )}
      </div>
      <p className="text-2xl font-extrabold text-gray-900 mt-1 leading-none">{value}</p>
      {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
    </div>
  )
}
