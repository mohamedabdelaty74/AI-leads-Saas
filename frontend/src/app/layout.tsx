import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import '@/styles/globals.css'
import { ToastProvider } from '@/components/ui/Toast'
import { ThemeProvider } from '@/contexts/ThemeContext'

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'Elite Creatif - AI-Powered Lead Generation',
  description: 'Transform your B2B sales with AI-driven lead generation and intelligent outreach automation',
  keywords: 'lead generation, AI, B2B sales, marketing automation, email outreach',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={inter.variable} suppressHydrationWarning>
      <body className="font-sans antialiased bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 transition-colors">
        <ThemeProvider>
          {children}
          <ToastProvider />
        </ThemeProvider>
      </body>
    </html>
  )
}
