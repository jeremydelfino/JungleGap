export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        bg:       '#111215',
        surface:  '#1c1d23',
        surface2: '#16171d',
        border:   '#ffffff08',
        border2:  '#ffffff12',
        text:     '#e8eaf0',
        muted:    '#9ca3af',
        hint:     '#4b5563',
        cyan:     '#00e5ff',
        violet:   '#a78bfa',
        gold:     '#c89b3c',
        success:  '#22c55e',
        danger:   '#ef4444',
      },
      fontFamily: {
        title: ['Syne', 'sans-serif'],
        body:  ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
}