web/
├── public/                 # Static assets (images, svgs, fonts)
├── src/                    # Main application source wrapper
│   ├── app/                # Next.js App Router (Routing, Layouts, Pages)
│   │   ├── layout.tsx      # Root layout (HTML wrapper, global providers)
│   │   ├── page.tsx        # Homepage (/)
│   │   ├── dashboard/      # Nested route (/dashboard)
│   │   │   ├── page.tsx    # Dashboard page component
│   │   │   └── _components/# Route-specific components (ignored by router)
│   │   └── api/            # Route Handlers (Backend API endpoints)
│   │       └── route.ts
│   │
│   ├── components/         # Global reusable UI components
│   │   ├── ui/             # Atomic, generic components (buttons, inputs)
│   │   ├── common/         # Layout pieces (navbar, footer, sidebar)
│   │   └── forms/          # Reusable form modules
│   │
│   ├── hooks/              # Custom global React hooks (useAuth, useDebounce)
│   ├── lib/                # Third-party client initializations (prisma, supabase, axios)
│   ├── services/           # API fetch wrappers or server actions
│   ├── styles/             # Global CSS/Tailwind configs
│   ├── types/              # Shared TypeScript definitions/interfaces
│   └── utils/              # Pure utility/helper functions (formatDate, cn)
│
├── tailwind.config.js
├── tsconfig.json
└── package.json