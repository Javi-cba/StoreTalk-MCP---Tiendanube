/** Fondo decorativo: degradados celestes difusos y una grilla tenue. */
export function PageBackground() {
  return (
    <div aria-hidden className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
      <div className="absolute -top-28 -left-24 size-[22rem] rounded-full bg-sky-300/30 blur-3xl" />
      <div className="absolute -top-40 right-[-10%] size-[42rem] rounded-full bg-sky-300/35 blur-3xl" />
      <div className="absolute top-1/3 -left-40 size-[36rem] rounded-full bg-blue-300/25 blur-3xl" />
      <div className="absolute -bottom-40 right-1/4 size-[30rem] rounded-full bg-indigo-200/30 blur-3xl" />
      <div className="absolute inset-0 bg-[linear-gradient(to_right,rgb(148_163_184/0.12)_1px,transparent_1px),linear-gradient(to_bottom,rgb(148_163_184/0.12)_1px,transparent_1px)] bg-size-[56px_56px] mask-[radial-gradient(ellipse_at_top_right,black_20%,transparent_70%)]" />
    </div>
  );
}
