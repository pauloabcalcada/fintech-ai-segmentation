import { useState, useRef } from "react";
import { createPortal } from "react-dom";

export function InfoTooltip({ text, side = "right" }: { text: string; side?: "left" | "right" }) {
  const [visible, setVisible] = useState(false);
  const [coords, setCoords] = useState({ top: 0, left: 0 });
  const buttonRef = useRef<HTMLButtonElement>(null);

  function handleMouseEnter() {
    if (buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect();
      const tooltipWidth = 224; // w-56
      setCoords({
        top: rect.top,
        left: side === "left" ? rect.left - tooltipWidth - 4 : rect.right + 4,
      });
    }
    setVisible(true);
  }

  return (
    <span className="relative inline-flex items-center">
      <button
        ref={buttonRef}
        type="button"
        className="ml-1 text-muted-foreground hover:text-foreground text-xs leading-none focus:outline-none"
        onMouseEnter={handleMouseEnter}
        onMouseLeave={() => setVisible(false)}
        aria-label="info"
        data-testid="info-tooltip-trigger"
      >
        ⓘ
      </button>
      {visible &&
        createPortal(
          <span
            role="tooltip"
            style={{
              position: "fixed",
              top: coords.top,
              left: coords.left,
              backgroundColor: "#18181b",
              color: "#f4f4f5",
              border: "1px solid #3f3f46",
              zIndex: 9999,
            }}
            className="w-56 rounded-md px-3 py-2 text-xs shadow-lg"
          >
            {text}
          </span>,
          document.body
        )}
    </span>
  );
}
