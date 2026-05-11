import { Sidebar } from '@/components'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return <Sidebar>{children}</Sidebar>
}