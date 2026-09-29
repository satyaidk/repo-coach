# RepoCompass web

The Next.js frontend for RepoCompass (Next.js 16, React 19, TypeScript, Tailwind CSS v4).
It talks to the FastAPI backend in the parent folder; see the [main README](../README.md) for setup.

```bash
npm install
npm run dev      # http://localhost:3000 (the API must be running on :8000)
```

- Colors live in `src/app/globals.css`: the `clay` palette is Claude orange, and the semantic tokens
  (`bg-surface`, `text-muted`, `bg-accent`...) switch between light and dark themes.
- Themes are applied before the first paint by the inline script from `src/lib/theme.ts`.
- `NEXT_PUBLIC_API_URL` (see `.env.example`) points the app at a different API address.
