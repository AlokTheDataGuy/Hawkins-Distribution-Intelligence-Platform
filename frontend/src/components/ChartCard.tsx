import { ReactNode } from 'react'

interface Props {
  title: string
  children: ReactNode
  className?: string
}

export default function ChartCard({ title, children, className = '' }: Props) {
  return (
    <div className={`bg-white border border-gray-200 rounded-xl p-4 shadow-sm ${className}`}>
      <h3 className="text-sm font-bold text-gray-700 mb-3">{title}</h3>
      {children}
    </div>
  )
}
