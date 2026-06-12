'use client';

import { FormEvent, useCallback, useEffect, useMemo, useState } from 'react';
import type { Result } from '@/lib/types';

type Theme = 'light' | 'dark';
type HeartSpec = {
  id: number;
  left: number;
  size: number;
  duration: number;
  delay: number;
  hue: number;
};

const MAGUS_COLORS = ['#4285F4', '#EA4335', '#FBBC04', '#34A853', '#A142F4'];
const MAGIC_ENHANCEMENTS = [
  'primary sources',
  'occult correspondences',
  'ritual steps',
  'historical context',
  'symbolism and meaning',
  'scholarly commentary',
];
const APOCALYPSE_URL =
  'https://youtube.com/playlist?list=PLPyavnZEPWe2gUXtcqcgzs3m5lNK8eyiM&si=_LBSk5WqqRacMTml';
const BABYLON_IMAGE =
  'https://images-wixmp-ed30a86b8c4ca887773594c2.wixmp.com/f/ceb9e091-7c46-41e1-a84e-a636e9e7b50d/d9asma3-aa191e4b-fc03-47e9-9c88-7e84f897b174.png/v1/fit/w_800,h_963/babel_tower_png_stock_by_mahdi_dawood_d9asma3-414w-2x.png?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1cm46YXBwOjdlMGQxODg5ODIyNjQzNzNhNWYwZDQxNWVhMGQyNmUwIiwiaXNzIjoidXJuOmFwcDo3ZTBkMTg4OTgyMjY0MzczYTVmMGQ0MTVlYTBkMjZlMCIsIm9iaiI6W1t7ImhlaWdodCI6Ijw9OTYzIiwicGF0aCI6Ii9mL2NlYjllMDkxLTdjNDYtNDFlMS1hODRlLWE2MzZlOWU3YjUwZC9kOWFzbWEzLWFhMTkxZTRiLWZjMDMtNDdlOS05Yzg4LTdlODRmODk3YjE3NC5wbmciLCJ3aWR0aCI6Ijw9ODAwIn1dXSwiYXVkIjpbInVybjpzZXJ2aWNlOmltYWdlLm9wZXJhdGlvbnMiXX0.fnh7vocueMgg3GmtplteAWgsBAwvQdNETYd7AcgPbZQ';

export default function Page() {
  const [theme, setTheme] = useState<Theme>('light');
  const [mounted, setMounted] = useState(false);
  const [q, setQ] = useState('');
  const [results, setResults] = useState<Result[]>([]);
  const [count, setCount] = useState<number>(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [babylonMode, setBabylonMode] = useState(false);

  const applyTheme = useCallback((next: Theme) => {
    const root = document.documentElement;
    root.classList.toggle('dark', next === 'dark');
    root.dataset.theme = next;
    root.style.setProperty('color-scheme', next);
    localStorage.setItem('magus-theme', next);
  }, []);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const stored = localStorage.getItem('magus-theme') as Theme | null;
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const initial = stored ?? (prefersDark ? 'dark' : 'light');
    setTheme(initial);
    applyTheme(initial);
    setMounted(true);
  }, [applyTheme]);

  useEffect(() => {
    if (!mounted) return;
    applyTheme(theme);
  }, [theme, mounted, applyTheme]);

  const isBabylonQuery = useCallback((input: string) => input.trim().toLowerCase() === 'babylon', []);

  const runSearch = useCallback(
    async (query: string) => {
      const trimmed = query.trim();
      if (!trimmed) {
        setResults([]);
        setCount(0);
        return;
      }
       // Redirect easter egg for apocalypse
      if (trimmed.toLowerCase() === 'apocalypse') {
        if (typeof window !== 'undefined') {
          window.location.href = APOCALYPSE_URL;
        }
        return;
      }
      setLoading(true);
      setError(null);
      setBabylonMode(isBabylonQuery(trimmed));
      try {
        const params = new URLSearchParams({ q: trimmed });
        const res = await fetch(`http://localhost:8000/search?${params.toString()}`);
        if (!res.ok) throw new Error(`Search failed with status ${res.status}`);
        const data = await res.json();
        setResults(data.results || []);
        setCount(data.count || 0);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Unknown error';
        setError(message);
        setResults([]);
        setCount(0);
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  const handleSubmit = useCallback(
    (event: FormEvent) => {
      event.preventDefault();
      runSearch(q);
    },
    [q, runSearch],
  );

  const enchantQuery = useCallback(
    (query: string) => {
      const addition =
        MAGIC_ENHANCEMENTS[Math.floor(Math.random() * MAGIC_ENHANCEMENTS.length)];
      return `${query.trim()} ${addition}`.trim();
    },
    [],
  );

  const handleFeelingMagical = useCallback(() => {
    const enchanted = enchantQuery(q || 'esoteric wisdom');
    setQ(enchanted);
    runSearch(enchanted);
  }, [enchantQuery, q, runSearch]);

  const themeLabel = useMemo(
    () => (theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'),
    [theme],
  );

  const hearts = useMemo<HeartSpec[]>(() => {
    if (!babylonMode) return [];
    return Array.from({ length: 40 }, (_, idx) => ({
      id: idx,
      left: Math.random() * 100,
      size: 16 + Math.random() * 26,
      duration: 6 + Math.random() * 4,
      delay: Math.random() * 2,
      hue: 330 + Math.random() * 40,
    }));
  }, [babylonMode]);

  return (
    <div className="flex min-h-screen flex-col">
      <header className="flex justify-end px-6 py-4">
        <button
          type="button"
          onClick={() => setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'))}
          className="flex items-center gap-2 rounded-full border border-transparent bg-[var(--card-bg)] px-4 py-2 text-sm shadow-sm transition hover:border-sky-400/60 hover:shadow"
          aria-label={themeLabel}
        >
          <span>{theme === 'dark' ? '🌞' : '🌙'}</span>
          <span className="hidden sm:inline">{theme === 'dark' ? 'Light Mode' : 'Dark Mode'}</span>
        </button>
      </header>

      <main className="flex flex-1 flex-col items-center px-4">
        <div className="mt-16 flex w-full max-w-2xl flex-col items-center">
          <div className="select-none text-6xl font-medium tracking-tight sm:text-7xl">
            {'Magus'.split('').map((letter, index) => (
              <span
                key={`${letter}-${index}`}
                style={{ color: MAGUS_COLORS[index % MAGUS_COLORS.length] }}
              >
                {letter}
              </span>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="mt-10 flex w-full flex-col items-center gap-6">
            <div className="search-shell w-full">
              <input
                className="search-input"
                value={q}
                onChange={(event) => setQ(event.target.value)}
                placeholder="Search Magus or ask for esoteric guidance"
                aria-label="Search Magus"
              />
            </div>
            <div className="flex flex-wrap justify-center gap-4">
              <button
                type="submit"
                className="rounded-lg bg-[#f8f9fa] px-6 py-2 text-sm font-medium text-[#202124] shadow-sm transition hover:bg-[#f1f3f4] hover:shadow md:px-8 dark:bg-[#1f1f24] dark:text-[#e8eaed] dark:hover:bg-[#2f3034]"
              >
                Magus Search
              </button>
              <button
                type="button"
                onClick={handleFeelingMagical}
                className="rounded-lg bg-[#f8f9fa] px-6 py-2 text-sm font-medium text-[#202124] shadow-sm transition hover:bg-[#f1f3f4] hover:shadow md:px-8 dark:bg-[#1f1f24] dark:text-[#e8eaed] dark:hover:bg-[#2f3034]"
              >
                I&apos;m Feeling Magical
              </button>
            </div>
          </form>

          <div className="mt-6 h-6 text-sm text-neutral-500 dark:text-neutral-400">
            {loading && <span>Conjuring results…</span>}
            {!loading && count > 0 && (
              <span>
                Found {count} enchanted {count === 1 ? 'result' : 'results'}
              </span>
            )}
            {!loading && !error && count === 0 && q.trim().length > 0 && (
              <span>No results yet—try refining your incantation.</span>
            )}
            {error && <span className="text-red-500 dark:text-red-400">{error}</span>}
          </div>
        </div>

        {results.length > 0 && (
          <section className="mt-12 flex w-full max-w-4xl flex-col gap-4 pb-20">
            {results.map((r) => (
              <article key={r.id} className="card">
                <div className="flex flex-col gap-1">
                  <a
                    href={r.citation?.url || '#'}
                    target={r.citation?.url ? '_blank' : undefined}
                    rel="noreferrer"
                    className="text-sm text-sky-600 underline underline-offset-2 dark:text-sky-400"
                  >
                    {r.citation?.url || 'Unlinked source'}
                  </a>
                  <h3 className="text-xl font-medium text-[var(--fg)]">{r.title}</h3>
                  <div className="text-sm text-neutral-500 dark:text-neutral-400">
                    {r.author ? `by ${r.author} • ` : ''}
                    {r.date}
                    {r.genre ? ` • ${r.genre}` : ''}
                  </div>
                </div>
                <p className="mt-3 text-sm leading-relaxed text-[var(--fg)]/85">{r.snippet}</p>
                <div className="mt-4 flex flex-wrap gap-2">
                  {r.tradition.map((t) => (
                    <span key={t} className="chip">
                      {t}
                    </span>
                  ))}
                  {r.tags.map((t) => (
                    <span key={t} className="badge">
                      {t}
                    </span>
                  ))}
                  <span className="badge">score {r.score.toFixed(3)}</span>
                </div>
              </article>
            ))}
          </section>
        )}
      </main>

      {babylonMode && (
        <div className="babylon-overlay" aria-hidden>
          {hearts.map((heart) => (
            <span
              key={heart.id}
              className="babylon-heart"
              style={{
                left: `${heart.left}%`,
                animationDuration: `${heart.duration}s`,
                animationDelay: `${heart.delay}s`,
                fontSize: `${heart.size}px`,
                color: `hsl(${heart.hue}, 82%, 62%)`,
              }}
            >
              ♥
            </span>
          ))}
          <div className="babylon-tower-rise">
            <img src={BABYLON_IMAGE} alt="Tower of Babel rising" className="babylon-tower" />
          </div>
        </div>
      )}
    </div>
  );
}
