import React from "react";
import "./ActionBar.css";

export default function ActionsBar({
  value,
  onChange,
  onEnter,
  onLeftClick,
  onRightClick,
  placeholder = "Paste the URL",
  leftLabel = "Load",
  rightLabel = "Add",
}) {
  const fire = (fn) => fn?.(value);

  return (
    <div className="actionsBar">
      <input
        className="actionsInput"
        type="text"
        value={value}
        placeholder={placeholder}
        onChange={(e) => onChange?.(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter") fire(onEnter); // envia o value
        }}
      />
      <div className="actionsButtons">
        <button className="btn btnPrimary" onClick={() => fire(onLeftClick)}>
          {leftLabel}
        </button>
        <button className="btn btnGhost" onClick={() => fire(onRightClick)}>
          {rightLabel}
        </button>
      </div>
    </div>
  );
}
