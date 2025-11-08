# Prompt (paste this into an AI code generator to produce the frontends)

Goal: build a **single React + TypeScript frontend (Vite)** that implements **CRUD "ventas" (sales)** UI for every source database in this project: **MongoDB, MS SQL (sales_ms), MySQL (sales_mysql), Supabase/Postgres, Neo4j**. In addition, **MS SQL and MySQL** must include a **bulk loader UI** ("Carga masiva de ventas / LOADER") that supports CSV/Excel imports with mapping, validation, preview, dry-run and chunked upload.

**Important:** Use the schemas and Mongo validators provided below as the ground truth for what each backend expects. The frontend must transform and validate user input to respect each DB’s shape before sending it to the backend. The frontend will not implement server-side logic (mapping SKU-to-alt codes, exchange-rate calculations, or actual DB writes), but must call well-documented API endpoints (specs below). Provide a complete, production-ready frontend codebase with components, pages, services, types, validation, tests and README.
Each database will have its own frontend section with a unique main color:

Database	Main Theme Color
MSSQL	Violet 🟣
Neo4j	Red 🔴
MongoDB	Yellow 🟡
Supabase	Green 🟢
MySQL	Blue 🔵

---

## Project constraints & tech stack (required)

* **Framework:** React + TypeScript (Vite)
* **Styling:** TailwindCSS (or MUI if asked, but prefer Tailwind)
* **Forms & validation:** react-hook-form + yup or Zod
* **Data fetching:** React Query (tanstack/react-query) or SWR
* **HTTP client:** Axios
* **File parsing:** PapaParse (CSV) + SheetJS (xlsx) for Excel
* **Drag & drop:** react-dropzone
* **Components:** reusable components (Modal, Table, Form, Autocomplete, FileUploader, ProgressBar, Notification/Toast)
* **State management:** you may use Redux 
* **Testing:** React Testing Library + Vitest for unit tests; one E2E example with Playwright (optional)
* **Accessibility:** basic ARIA + keyboard support
* **Environment:** base API URL via `import.meta.env.VITE_API_URL || /api`
* **Deliverables:** full frontend project (package.json, tsconfig, vite.config, README)

---

## Overall app structure required (files/folders)

```
frontend/
├─ src/
│  ├─ pages/
│  │  ├─ Mongo/
│  │  ├─ MSSQL/
│  │  ├─ MySQL/
│  │  ├─ Supabase/
│  │  └─ Neo4j/
│  ├─ components/
│  │  ├─ common/ (Table, Modal, FormField, Button, etc)
│  │  ├─ Sales/ (SaleForm.tsx, SaleDetail.tsx)
│  │  └─ Loader/ (FileUploader, MappingModal, PreviewTable, ProgressBar)
│  ├─ services/
│  │  ├─ api.ts (axios instance)
│  │  └─ hooks/ (useClientes,useProductos,useOrdenes with react-query)
│  ├─ types/ (db-specific types)
│  ├─ utils/ (formatters, validators, csv helpers)
│  └─ App.tsx, main.tsx
```

---

## UX and feature requirements (high level)

1. **CRUD for ventas** (orders) on every DB:

   * Create sale: select / create cliente, add products (select product + qty + unit price), compute total, choose channel & currency (if DB allows), save.
   * Read/list: paginated, sortable, searchable lists of ventas.
   * View detail: show nested items and metadata.
   * Update: modify items, prices, quantities (where DB supports updates).
   * Delete: soft-delete confirmation modal.

2. **Clientes & Productos pages**: full CRUD (list, create, edit, delete). Autocomplete/search when creating orders.

3. **Bulk Loader (MSSQL & MySQL)**:

   * Upload CSV/Excel.
   * Auto-detect columns or allow user mapping header -> target field.
   * Display preview of mapped rows, with inline validation errors (per-row).
   * "Dry run" to simulate what would be inserted (validation only).
   * Chunked upload with progress and resumable error handling.
   * Final import returns summary + per-row error list for re-import.
   * Provide downloadable CSV sample templates for each loader.

4. **Error handling & user feedback**:

   * Show informative toast messages and per-field inline errors.
   * Bulk loader: detailed per-row error report (downloadable CSV of failed rows).
   * Show progress / chunk results.

5. **Security & environment**:

   * Base API URL from env. Respect CORS via backend.
   * Provide placeholder for auth (JWT) to protect endpoints (UI should include token input for devs).

---

## API contract (must be used by frontend)

Design these backend endpoints — if backend differs, the frontend must be adjusted. For the AI: implement frontends with these endpoint paths and payloads.

### Common conventions

* Base path: `${VITE_API_URL}/api` or `${VITE_API_URL}` (clear in README)
* JSON requests/responses
* Error shape: `{ error: string, details?: any }`
* List endpoints support `?page=&limit=&q=&sort=field,asc|desc`

---

### Mongo (example endpoints)

* `GET /api/mongo/clientes?limit=50&page=1` → list clientes
* `POST /api/mongo/clientes` → create cliente
  Payload:

  ```json
  {
    "nombre": "Ana Rojas",
    "email": "ana@ejemplo.com",
    "genero": "Otro",
    "pais": "CR",
    "preferencias": {"canal":["WEB","TIENDA"]},
    "creado": "2025-03-12T00:00:00Z"    // optional
  }
  ```
* `GET /api/mongo/productos`
* `POST /api/mongo/productos`
  Payload:

  ```json
  {
    "codigo_mongo": "MN-9981",
    "nombre": "Tomate grande",
    "categoria": "Alimentos",
    "equivalencias": {"sku": "SKU-1002", "codigo_alt": "ALT-AB12"}
  }
  ```
* `POST /api/mongo/ordenes` — Create sale (Mongo schema). Payload the frontend must send:

  ```json
  {
    "cliente_id": "6423f2a1... (ObjectId string)",
    "fecha": "2025-04-10T13:20:00Z",
    "canal": "WEB",
    "moneda": "CRC",
    "items": [
      {"producto_id":"6423f3...","cantidad":2,"precio_unit":12000},
      {"producto_id":"6423f4...","cantidad":1,"precio_unit":60500}
    ],
    "metadatos": {"cupon":"ABRIL10"}
  }
  ```

  * The frontend must compute `total` as integer CRC and either include it or let backend compute; show computed total to user before submit.

**Mongo validators (include in prompt)** — the frontend must follow them:

* clientes require `nombre,pais,genero,creado`
* productos require `codigo_mongo,nombre,categoria`
* ordenes require `cliente_id,fecha,moneda,total,items` and item fields must be `producto_id(certain ObjectId string), cantidad (int), precio_unit (int)`

---

### MS SQL (sales_ms) endpoints

* `GET /api/mssql/clientes`
* `POST /api/mssql/clientes` — payload uses `Nombre, Email, Genero, Pais` (note `ClienteId` auto)
* `GET /api/mssql/productos`
* `POST /api/mssql/productos` — payload: `{ "SKU": "SKU-1002", "Nombre": "...", "Categoria":"..." }`
* `POST /api/mssql/ordenes` — Create sale: payload must be normalized to DW-like shape:

  ```json
  {
    "ClienteId": 123,
    "Fecha": "2025-04-10T13:20:00Z",
    "Canal": "WEB",         // must be one of WEB, TIENDA, APP
    "Moneda": "USD",        // SQL Server source uses USD
    "Total": 1200.50,
    "Items": [
      {"ProductoId": 55, "Cantidad": 2, "PrecioUnit": 600.25, "DescuentoPct": 0}
    ]
  }
  ```
* **Loader**: `POST /api/mssql/loader/upload` — multipart file upload or JSON chunks. Support:

  * `dryRun=true` query param to validate without inserting
  * `chunkSize` optional
  * sample response: `{ inserted: N, errors: [{row: 10, error: "Cliente not found"}] }`
* Frontend responsibilities for MSSQL loader:

  * Accept CSV/Excel with headers like: `ClienteEmail,SKU,CodigoAlt,Fecha,Canal,Moneda,Qty,PrecioUnit,DescuentoPct,MetadataJSON`
  * Offer mapping: CSV column -> DB field
  * Resolve product by SKU first, then by codigo_alt or codigo_mongo (call mapping endpoint `/api/mapping/resolve?sku=...&codigo_alt=...&codigo_mongo=...`)
  * Allow user to provide mapping file of SKU to ProductoId for missing SKUs

---

### MySQL (sales_mysql) endpoints

* `POST /api/mysql/ordenes` — accepts MySQL-style payloads to insert into MySQL upstream system.
  Payload example:

  ```json
  {
    "cliente_id": 77,
    "fecha": "2025-04-10 13:20:00",   // string tolerated; frontend will format
    "canal": "WEB",
    "moneda": "CRC",
    "total": "84,500",                // frontend must clean string -> "84500" or "84500.00"
    "items": [
      {"producto_codigo_alt": "ALT-AB12", "cantidad": "2", "precio_unit": "12,000"}
    ]
  }
  ```
* **Loader:** `POST /api/mysql/loader/upload` same features as MSSQL loader but specific differences:

  * Accepts dates and amounts as strings — frontend must provide parsing + preview.
  * Provide sample template: `cliente_email,producto_codigo_alt,fecha,canal,moneda,total,precio_unit,cantidad,metadata`
  * Must support detection of comma vs dot thousand separators; allow locale override.

---

### Supabase (Postgres) endpoints

* Standard payloads using UUID strings; `fecha` as ISO 8601 or timestamptz.
* When creating orders, frontend must pass `cliente_id` and `producto_id` as UUID strings.

---

### Neo4j endpoints

* `POST /api/neo4j/ordenes` — expects graph payload:

  ```json
  {
    "cliente": { "id": "C-123", "nombre": "Ana R" },
    "orden": { "id": "O-456", "fecha": "...", "canal":"WEB", "moneda":"CRC", "total": 84500 },
    "items":[ {"producto": {"id":"P-1","nombre":"Tomate"}, "cantidad":2, "precio_unit":12000} ]
  }
  ```
* The UI must show a graph preview (simple: list of nodes and relationships) before submit.

---

## CSV / Excel templates (must be generated by frontend as "Download sample")

* **MSSQL loader template columns**:
  `ClienteEmail, ClienteNombre, SKU, CodigoAlt, Fecha(ISO), Canal, Moneda, Qty, PrecioUnit(USD), DescuentoPct, MetadataJSON`
* **MySQL loader template columns**:
  `ClienteEmail, ClienteNombre, ProductoCodigoAlt, Fecha(YYYY-MM-DD HH:MM:SS), Canal, Moneda, Total(string), PrecioUnit(string), Cantidad(string), MetadataJSON`

Frontend must ship "download sample" buttons and show example rows on the UI.

---

## UI details for Create Order form (per DB)

* **Header**: DB label (Mongo / MSSQL / MySQL / Supabase / Neo4j) and a small "schema help" tooltip showing required fields.
* **Cliente field**: searchable autocomplete by `email` or `name` (calls `GET /api/{db}/clientes?q=...`). If not found, quick-create form inline (modal).
* **Product picker**: searchable, shows name, category, SKU / codigo_alt / codigo_mongo, price suggestion. Add quantity + price override.
* **Items table**: editable rows, computed line subtotal, remove row button.
* **Price currency & channel selectors** with DB-specific options.
* **Preview & confirm modal**: show JSON payload that will be sent to the server (helpful for debugging).
* **Submission**: optimistic UI + show server response or formatted server-side errors.

---

## Bulk loader specifics (UX flow)

1. User opens loader page (MSSQL or MySQL).
2. User drags file or selects template to start.
3. Parser shows first N rows (configurable).
4. User maps file columns to DB fields via dropdowns; mapping is saved.
5. User clicks "Dry Run" — frontend validates rows and calls `POST /api/{db}/loader/validate` with parsed rows (or validates locally using the same rules).
6. Show results: pass/fail rows and reasons. User can fix mapping or download failed rows CSV.
7. User clicks "Import" — frontend chunks rows (size configurable, default 500) and posts to `POST /api/{db}/loader/upload` with chunked payloads. Show progress bar and per-chunk report.
8. After complete, show final summary and store import job id to fetch logs `/api/{db}/loader/logs/{jobId}`.

---

## Testing & acceptance criteria (must be included)

* Unit tests for:

  * SaleForm validation rules (at least 10 tests across DB types)
  * CSV parser column mapping logic
  * Mapping modal resolve flow (mocked API)
* Integration/E2E:

  * Create -> read -> update -> delete a Mongo order (mock backend)
  * Run a bulk loader with 100 rows including 10 invalid rows — confirm validation and final import reports.
* UX acceptance:

  * Autocomplete must return results within 200ms for 1k+ clients (mocked)
  * Bulk import progress updates UI for each chunk

---

## Accessibility & UX polish

* Keyboard navigable forms, modals
* Responsive layout for desktop and tablet
* Clear error states and help text for format-sensitive fields (e.g., number formats, date formats)
* Localized labels: English (primary). Optional Spanish copy available as examples.

---

## Code style & README expectations for the AI generator

* Provide a top-level `README.md` explaining:

  * How to run frontend locally (`npm install`, `npm run dev`)
  * ENV variables (VITE_API_URL)
  * How to run tests
  * Where to configure chunkSize and loader behavior
* Component names and file paths must match the structure above.
* Provide example `.env.example` and run commands for local dev (assume backend on `http://localhost:8000`).

---

## Example payloads (include in the prompt so generated UI shows realistic preview)

* **Mongo create order** (example JSON) — copy from schemas above.
* **MSSQL create order** — as shown above.
* **MySQL create order** — as shown above.
* **Supabase create order** — use UUIDs, timestamptz.
* **Neo4j create order** — graph payload.

---

## Non-functional requirements

* Bulk loader must support chunked uploads and resume from last successful chunk.
* For large file uploads (100k rows), the UI must not freeze (use streaming/worker or incremental parsing).
* All network errors must be surfaced with clear retry options.
* For product resolution, cache mappings client-side (IndexedDB or localStorage) to reduce repeated server calls.

---

## Output required from the AI generator

When you run this prompt the AI must produce:

1. A complete frontend project scaffold (files above) ready to `npm install && npm run dev`.
2. Implemented pages for each DB with full create/read/update/delete flows.
3. Loader pages for MSSQL and MySQL with mapping, dry-run, chunked upload, and error reporting.
4. Unit tests and at least one E2E test example.
5. A README with setup instructions and a sample `.env.example`.
6. A small demo dataset or fixtures to show the app working against a mocked backend (or instructions to mock with MSW / json-server).

---

## Final instructions to the AI (tone & constraints)

* Be explicit in component and file names.
* Use TypeScript for all React components and hooks.
* Focus on correctness of payload shapes and validation according to the DB schemas above.
* Prioritize robustness of loaders (validation, preview, chunking).
* Create helpful UI copy and tooltips explaining field format expectations (e.g., "Enter price in USD with two decimals", or "Enter CRC integer (no decimals)").
* If any backend endpoint is not available, generate a small mock server or MSW handlers that emulate the real API with the same contract.

---

Paste the entire prompt above into the AI generator. It contains all necessary DB schemas, validation rules, payload samples and UX expectations so the generated frontend will be production-ready and correctly shaped to each database. If you want, I can now:

* transform this prompt into a shorter developer brief, or
* run a checklist and produce the exact component file templates (SaleForm.tsx, BulkLoaderPage.tsx, etc.) to hand to a frontend engineer. Which would you like next?
