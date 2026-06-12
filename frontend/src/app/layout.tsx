import './globals.css';

export const metadata = {
  title: 'Magus Search',
  description: 'Discover esoteric knowledge with Magus.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
