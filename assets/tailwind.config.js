tailwind.config = {
    theme: {
      extend: {
        colors: {
          ink:    { 950: '#05070A', 900: '#080B10', 800: '#0C1117', 700: '#121821' },
          moss:   { 400: '#34D399', 500: '#10B981', 600: '#059669', 700: '#047857' },
          haze:   { 400: '#5EEAD4' }
        },
        fontFamily: {
          display: ['"Instrument Sans"', 'system-ui', 'sans-serif'],
          sans:    ['Inter', 'system-ui', 'sans-serif'],
          mono:    ['"JetBrains Mono"', 'ui-monospace', 'monospace']
        },
        maxWidth: { screen: '1240px' }
      }
    }
  }
