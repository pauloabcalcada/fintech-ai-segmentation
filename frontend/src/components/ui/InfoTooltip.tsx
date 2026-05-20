import { useState } from "react";

export function InfoTooltip({ text }: { text: string }) {
  const [visible, setVisible] = useState(false);
  return (
    <span className="relative inline-flex items-center">
      <button
        type="button"
        className="ml-1 text-muted-foreground hover:text-foreground text-xs leading-none focus:outline-none"
        onMouseEnter={() => setVisible(true)}
        onMouseLeave={() => setVisible(false)}
        aria-label="info"
        data-testid="info-tooltip-trigger"
      >
        ⓘ
      </button>
      {visible && (
        <span
          role="tooltip"
          className="absolute left-5 top-0 z-50 w-56 rounded-md px-3 py-2 text-xs shadow-lg"
          style={{ backgroundColor: "#18181b", color: "#f4f4f5", border: "1px solid #3f3f46" }}
        >
          {text}
        </span>
      )}
    </span>
  );
}
