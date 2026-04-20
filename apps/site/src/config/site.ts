/**
 * Single source of truth for site copy. Edit here, not in the Astro files.
 */

export const site = {
  // --- Meta ---
  title: 'RAG Portfolio',
  description: 'An interactive AI portfolio. Ask anything.',
  url: 'https://example.com',

  // --- Owner ---
  owner: {
    name: 'Your Name',
    role: 'Director of AI · VP of Technology',
    tagline: 'Builder. Problem solver. Systems thinker.',
    headshot: '/assets/headshot-placeholder.svg',
  },

  // --- Hero copy ---
  hero: {
    pitch: 'One sentence on what you build and for whom. Make it sharp.',
    secondary: 'A second sentence of context. Optional.',
    ctaPrimary: { label: 'Ask me anything', href: '#chat' },
    ctaSecondary: { label: 'See the work', href: '#work' },
  },

  // --- About section ---
  about: {
    heading: 'About',
    body: [
      'Paragraph one. Who you are, what you build, what you care about.',
      'Paragraph two. A specific thing you have shipped recently, or a point of view you hold.',
      'Paragraph three. What you are looking for next.',
    ],
  },

  // --- Work section (optional project cards) ---
  work: {
    heading: 'Selected work',
    projects: [
      {
        title: 'Project one',
        blurb: 'One-line description. What it is and the outcome that mattered.',
        href: '#',
      },
      {
        title: 'Project two',
        blurb: 'Another project. Keep these tight. The AI chat handles depth.',
        href: '#',
      },
    ],
  },

  // --- RAG chat iframe ---
  chat: {
    heading: 'Ask me anything',
    // URL of your deployed RAG chat API. Locally: http://localhost:8510
    // In production: your Cloudflare Tunnel / reverse proxy URL.
    iframeUrl: 'http://localhost:8510?embed=1',
    height: '600px',
  },

  // --- Links shown in nav + footer ---
  links: {
    linkedin: '',
    github: '',
    email: '',
    booking: '',  // e.g. https://calendly.com/your-link
  },
} as const;
