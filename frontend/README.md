# Web interface (Presentation Layer)

Next.js 16 app, exported as static pages (`out/`) that the FastAPI backend serves at http://localhost:8000. The `app/` folder sits at the root of the project, not inside `src/`.

| Folder | Contents |
|---|---|
| `app/login`, `app/page.tsx` | Sign-in and the redirect to the dashboard |
| `app/(portal)/` | Signed-in pages (shared sidebar layout): dashboard, students, students/view, records, alerts, reports, model, users, account |
| `components/` | UI building blocks (`ui.tsx`), charts (`charts.tsx`), the prediction panel, the session context |
| `lib/` | API client (`api.ts`), types and formatting |

## Commands

```bash
npm install          # once
npm run build        # rebuild out/ after changing the interface
npm run dev          # live editing at http://localhost:3000
```

`npm run dev` needs the backend running separately and `NEXT_PUBLIC_API_URL=http://localhost:8000` set (for example in `.env.development.local`). The built app calls the API on its own origin, so it needs no setting.

Static export has rules (see `node_modules/next/dist/docs/01-app/02-guides/static-exports.md`):
- Pages fetch data in the browser.
- Student pages use `?code=` rather than dynamic routes.
- `useSearchParams` sits inside `<Suspense>`.
- `cacheComponents` stays off.
