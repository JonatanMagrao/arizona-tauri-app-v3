import { useState, useMemo } from "react";
import "./ErrorLogger.css";

/**
 * Props:
 * - errors: string[]
 * - onClear: () => void
 * - anchor: "parent" | "viewport"   (default: "viewport")
 * - wide: boolean                    (default: true) -> usa painel 90% width, 50% height
 */
export default function ErrorLogger({ errors = [], onClear, anchor = "viewport", wide = true }) {
  const [open, setOpen] = useState(false);
  const count = errors.length;
  const hasErrors = count > 0;

  const lastMsg = useMemo(
    () => (hasErrors ? errors[errors.length - 1] : ""),
    [errors, hasErrors]
  );

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(errors.join("\n"));
      alert("Errors copied to clipboard.");
    } catch {
      alert("Could not copy errors.");
    }
  };

  const containerClass =
    anchor === "parent" ? "error-logger anchor-parent" : "error-logger anchor-viewport";
  const chipClass = `chip ${hasErrors ? "chip-error" : "chip-idle"}`;
  const panelClass = [
    "panel",
    wide ? "panel-wide" : "",
    anchor === "parent" ? "panel-parent" : "panel-viewport",
  ].join(" ");

  return (
    <div className={containerClass}>
      {/* Chip sempre visível */}
      <button
        className={chipClass}
        onClick={() => setOpen(v => !v)}
        title={hasErrors ? lastMsg : "No errors"}
        aria-expanded={open}
        aria-controls="error-logger-panel"
      >
        <span className={`dot ${hasErrors ? "dot-error" : "dot-idle"}`} aria-hidden />
        <span className="chip-label">Errors</span>
        <span className="chip-count">{count}</span>
      </button>

      {/* Painel largo com lista e scroll */}
      {open && (
        <div id="error-logger-panel" className={panelClass} role="region" aria-label="Errors">
          <div className="panel-header">
            <strong>Errors</strong>
            <div className="spacer" />
            <button className="btn ghost" onClick={handleCopy}>Copy</button>
            <button className="btn ghost" onClick={onClear}>Clear</button>
            <button className="btn primary" onClick={() => setOpen(false)}>Close</button>
          </div>

          <div className="panel-list">
            {hasErrors ? (
              errors.map((msg, i) => (
                <div key={i} className="panel-item">
                  <span className="idx">#{i + 1}</span>
                  <span className="msg" title={msg}>{msg}</span>
                </div>
              ))
            ) : (
              <div className="panel-empty">No errors.</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
