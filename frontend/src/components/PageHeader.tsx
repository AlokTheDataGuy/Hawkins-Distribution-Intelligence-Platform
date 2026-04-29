interface Props { title: string; subtitle?: string }

export default function PageHeader({ title, subtitle }: Props) {
  return (
    <div className="mb-5">
      <h1 className="text-xl font-extrabold text-gray-900">{title}</h1>
      {subtitle && <p className="text-sm text-gray-500 mt-0.5">{subtitle}</p>}
      <div className="border-b border-gray-200 mt-3" />
    </div>
  )
}
