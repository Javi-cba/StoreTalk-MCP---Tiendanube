import {
  Layers,
  PackagePlus,
  Tag,
  Ticket,
  Truck,
  type LucideIcon,
} from "lucide-react";
import type { ComponentType } from "react";
import {
  ClaudeIcon,
  CursorIcon,
  GeminiIcon,
  OpenAiIcon,
  WindsurfIcon,
} from "@/components/ui/icons";

export const hero = {
  badge: "Para Tiendanube",
  title: "Gestioná tu tienda",
  titleHighlight: "conversando con tu IA",
  description:
    "Conectás tu Tiendanube una vez y después le pedís a tu asistente lo que necesitás, en lenguaje natural: precios, stock, pedidos, cupones y ventas.",
  primaryCta: { label: "Conectar mi tienda", href: "/connect" },
  // Con sesión iniciada el CTA lleva a sus tiendas.
  dashboardCta: { label: "Ir a mis tiendas", href: "/dashboard" },
  compatibility: "Compatible con Claude, ChatGPT, Cursor y cualquier cliente MCP",
};

export type UseCaseTone = "danger" | "success" | "info" | "neutral";

/** Cliente de IA (compatible con MCP) desde el que se muestra cada conversación. */
export type AiClient = {
  name: string;
  icon: ComponentType<{ size?: number | string; className?: string }>;
  /** Color de marca (clase de texto de Tailwind). */
  color: string;
};

const aiClients = {
  claude: { name: "Claude", icon: ClaudeIcon, color: "text-[#d97757]" },
  chatgpt: { name: "ChatGPT", icon: OpenAiIcon, color: "text-[#10a37f]" },
  cursor: { name: "Cursor", icon: CursorIcon, color: "text-slate-900" },
  gemini: { name: "Gemini", icon: GeminiIcon, color: "text-[#4285f4]" },
  windsurf: { name: "Windsurf", icon: WindsurfIcon, color: "text-teal-600" },
} satisfies Record<string, AiClient>;

export type UseCase = {
  client: AiClient;
  icon: LucideIcon;
  category: string;
  question: string;
  answer: string;
  rows: { label: string; detail?: string; badge?: string; tone?: UseCaseTone }[];
  tool: string;
};

/** Conversaciones de ejemplo que rotan en el cubo del hero, de la más llamativa a la más simple (máximo 4 filas). */
export const heroUseCases: UseCase[] = [
  {
    client: aiClients.claude,
    icon: PackagePlus,
    category: "Productos",
    question: "Creá estos productos: buzo oversize, gorra y medias",
    answer: "Listo, creé 3 productos nuevos en tu tienda:",
    rows: [
      { label: "Buzo oversize", detail: "$32.000 · S a XL", badge: "Nuevo", tone: "success" },
      { label: "Gorra trucker", detail: "$14.500 · Talle único", badge: "Nuevo", tone: "success" },
      { label: "Medias pack x3", detail: "$6.900 · 3 colores", badge: "Nuevo", tone: "success" },
      { label: "Categoría", detail: "Invierno", badge: "Publicados", tone: "info" },
    ],
    tool: "create_products",
  },
  {
    client: aiClients.chatgpt,
    icon: Layers,
    category: "Variantes",
    question: "Al jean mom agregale el talle 44 y dejá 10 u. por talle",
    answer: "Actualicé las variantes del Jean mom celeste:",
    rows: [
      { label: "Talle 38", detail: "10 u.", badge: "Actualizado", tone: "info" },
      { label: "Talle 40", detail: "10 u.", badge: "Actualizado", tone: "info" },
      { label: "Talle 42", detail: "10 u.", badge: "Actualizado", tone: "info" },
      { label: "Talle 44", detail: "10 u.", badge: "Nuevo", tone: "success" },
    ],
    tool: "update_product_variants",
  },
  {
    client: aiClients.cursor,
    icon: Ticket,
    category: "Cupones",
    question: "Creá un cupón del 15% para el finde",
    answer: "Cupón creado y activo en tu tienda:",
    rows: [
      { label: "Código", badge: "FINDE15", tone: "info" },
      { label: "Descuento", badge: "15% off", tone: "success" },
      { label: "Vigencia", badge: "Sáb y dom", tone: "neutral" },
      { label: "Compra mínima", badge: "$30.000", tone: "neutral" },
    ],
    tool: "create_coupon",
  },
  {
    client: aiClients.gemini,
    icon: Tag,
    category: "Precios",
    question: "Subí un 10% los precios de las remeras",
    answer: "Listo, actualicé 24 productos. Algunos:",
    rows: [
      { label: "Remera oversize negra", detail: "$19.800", badge: "+10%", tone: "success" },
      { label: "Remera básica blanca", detail: "$13.750", badge: "+10%", tone: "success" },
      { label: "Remera rayada", detail: "$16.500", badge: "+10%", tone: "success" },
      { label: "Remera manga larga", detail: "$22.000", badge: "+10%", tone: "success" },
    ],
    tool: "update_product_prices",
  },
  {
    client: aiClients.windsurf,
    icon: Truck,
    category: "Pedidos",
    question: "Marcá como enviados los pedidos pagados de hoy",
    answer: "Marqué 4 pedidos como enviados y avisé a los clientes:",
    rows: [
      { label: "#1043 · Lucía Gómez", detail: "$48.900", badge: "Enviado", tone: "success" },
      { label: "#1041 · Martín Ruiz", detail: "$23.500", badge: "Enviado", tone: "success" },
      { label: "#1038 · Sofía Paz", detail: "$71.200", badge: "Enviado", tone: "success" },
      { label: "#1036 · Diego Torres", detail: "$35.400", badge: "Enviado", tone: "success" },
    ],
    tool: "fulfill_orders",
  },
];

export const heroStore = {
  name: "Tiendanube",
  status: "En vivo",
  stats: [
    { value: "248", label: "Productos" },
    { value: "1.240", label: "Pedidos" },
  ],
};
