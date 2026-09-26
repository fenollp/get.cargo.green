// Compiled at build time by build.py (Tailwind CLI v3). Neutrals and accents read
// CSS variables from theme.css, so the same classes serve the dark and light themes.
const v = name => `rgb(var(--c-${name}) / <alpha-value>)`;

module.exports = {
  theme: {
    extend: {
      colors: {
        white:  v('white'),
        slate:  { 200: v('slate-200'), 300: v('slate-300'), 400: v('slate-400'), 500: v('slate-500'), 600: v('slate-600') },
        ink:    { 950: v('ink-950'), 900: v('ink-900'), 800: v('ink-800'), 700: v('ink-700') },
        moss:   { 300: v('moss-300'), 400: v('moss-400'), 500: v('moss-500'), 600: v('moss-600'), 700: v('moss-700') },
        haze:   { 400: v('haze-400') }
      },
      fontFamily: {
        display: ['"Instrument Sans"', 'system-ui', 'sans-serif'],
        sans:    ['Inter', 'system-ui', 'sans-serif'],
        mono:    ['"JetBrains Mono"', 'ui-monospace', 'monospace']
      },
      maxWidth: { screen: '1240px' }
    }
  }
};
