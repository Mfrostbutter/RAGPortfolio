# Portfolio site

Astro 5 static site that frames the RAG chat (`apps/rag-chat`) and showcases your work.

## Customize

All copy lives in [`src/config/site.ts`](src/config/site.ts). Edit that one file:

- Owner name, role, tagline, headshot path
- Hero pitch + CTAs
- About paragraphs
- Work cards (title + blurb + link)
- Chat iframe URL (point it at your deployed `apps/rag-chat`)
- Social / booking links

Replace `public/assets/headshot-placeholder.svg` with your own photo and update `owner.headshot` in the config.

## Commands

```sh
npm install
npm run dev       # localhost:4321
npm run build     # static output to ./dist
npm run preview   # preview the build
```

## Deploy to Cloudflare Pages

```sh
# Install wrangler once
npm install -g wrangler

# Deploy
npm run build
wrangler pages deploy dist --project-name=rag-portfolio-site
```

Or connect the GitHub repo in the Cloudflare Pages dashboard and set the build command to `npm run build` and output directory to `dist`.

## Chat iframe

By default the chat iframe points at `http://localhost:8510?embed=1`. For production:

1. Deploy `apps/rag-chat` behind a reverse proxy or Cloudflare Tunnel
2. Set `ALLOWED_ORIGIN` on the chat server to your site's URL
3. Update `chat.iframeUrl` in `site.ts` to the public chat URL
