import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";

// Solo el área privada pide sesión; la landing y el resto quedan públicos.
// /connect/callback NO va acá: llega desde Tiendanube (navegación cross-site) y en esa request el
// middleware no siempre ve la sesión; el hook useConnectCallback la verifica en el cliente.
// /authorize (consentimiento del OAuth del MCP) tampoco: llega desde el asistente de IA vía el backend;
// useAuthorizationRequest manda al login y vuelve. /connect-ai es la guía pública.
const isPrivateRoute = createRouteMatcher(["/dashboard(.*)", "/connect"]);

export default clerkMiddleware(async (auth, request) => {
  if (isPrivateRoute(request)) {
    await auth.protect();
  }
});

export const config = {
  matcher: [
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
    "/(api|trpc)(.*)",
    "/__clerk/:path*",
  ],
};
