import { CopyField } from "@/components/ui/copy-field";
import { assistantGuideCopy } from "@/content/assistantGuide";

type GuideStepsProps = {
  steps: readonly { title: string; description: string; command?: string }[];
  mcpUrl: string;
};

/** Pasos numerados unidos por una línea vertical; cada uno entra con un leve escalonado. */
export function GuideSteps({ steps, mcpUrl }: GuideStepsProps) {
  const copy = assistantGuideCopy;

  return (
    <ol className="relative flex flex-col gap-4">
      {steps.map((step, index) => (
        <li
          key={step.title}
          style={{ animationDelay: `${index * 80}ms` }}
          className="relative flex animate-rise-in gap-4 motion-reduce:animate-none"
        >
          {index < steps.length - 1 && (
            <span aria-hidden className="absolute top-10 bottom-[-1rem] left-[1.1875rem] w-0.5 bg-linear-to-b from-blue-200 to-transparent" />
          )}
          <span className="relative grid size-10 shrink-0 place-items-center rounded-full bg-linear-to-br from-blue-600 to-sky-400 text-sm font-bold text-white shadow-md shadow-blue-600/30 ring-4 ring-white">
            {index + 1}
          </span>
          <div className="min-w-0 flex-1 pt-1.5">
            <h3 className="font-semibold text-slate-900">{step.title}</h3>
            <p className="mt-1 text-sm leading-relaxed text-slate-600">{step.description}</p>
            {step.command && (
              <CopyField
                value={step.command.replace("{url}", mcpUrl)}
                copyLabel={copy.copyCommand}
                copiedLabel={copy.copied}
                tone="code"
                className="mt-3"
              />
            )}
          </div>
        </li>
      ))}
    </ol>
  );
}
