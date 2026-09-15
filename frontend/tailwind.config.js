export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        fondo:     "#F3F7FC",
        carta:     "#FFFFFF",
        azul:      "#1E3A8A",
        azulMed:   "#1D4ED8",
        azulSuave: "#EFF4FB",
        verde:     "#16A34A",
        verdeOs:   "#15803D",
        ambar:     "#D97706",
        tinta:     "#1F2937",
        suave:     "#64748B",
        borde:     "#E2E8F0",
      },
      fontFamily: {
        sans: ["'Plus Jakarta Sans'", "system-ui", "-apple-system", "sans-serif"],
      },
    },
  },
  plugins: [],
};
