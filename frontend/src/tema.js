/* Paleta única del sistema. Tailwind también la tiene en tailwind.config.js;
   esto es para los estilos en línea (barras de color, rellenos calculados). */
export const C = {
  fondo:   "#F3F7FC",
  carta:   "#FFFFFF",
  azul:    "#1E3A8A",
  azulMed: "#1D4ED8",
  azulSuave:"#EFF4FB",
  verde:   "#16A34A",
  verdeOs: "#15803D",
  ambar:   "#D97706",
  texto:   "#1F2937",
  suave:   "#64748B",
  borde:   "#E2E8F0",
};

/* Un icono por bloque. El API manda datos, no presentación. */
import {
  Ship, Truck, ShoppingCart, Palette, Leaf, HeartHandshake, Users, Home,
  Settings2, Globe, Sprout, Megaphone, Smartphone, Layers,
} from "lucide-react";

const ICONOS = {
  1: Ship, 2: Truck, 3: ShoppingCart, 4: Palette, 5: Leaf, 6: HeartHandshake,
  7: Users, 8: Home, 9: Settings2, 10: Globe, 11: Sprout, 12: Megaphone,
  13: Smartphone,
};
export const iconoDe = id => ICONOS[id] || Layers;
