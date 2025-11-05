import folderIcon from "../../assets/folder_icon.svg";
import thumbnailIcon from "../../assets/thumbnails.svg";
import "./ProjectRow.css";
import { openUrl } from "@tauri-apps/plugin-opener"


export default function TableRow({
  id, type, loc, game, name, duration, owners, status,
  mktoutData, masterData, previewPath,
  openFolder, openThumbnail, openParentFileFolder,
  miroEndpoints,
  disabled
}) {

  async function copyText(text) {
    try {
      await navigator.clipboard.writeText(text); // precisa de HTTPS ou localhost
      console.log("Copiado!");
    } catch (err) {
      console.error("Falhou ao copiar:", err);
    }
  }

  const handleMiroLink = () => {
    const BASE_URL = "https://miro.com/app/board/"
    const projectNumber = id.split("-")[2]
    const gameProject = id.split("-")[0].toLowerCase()
    const projectType = type.toLowerCase()
    const endpoints = miroEndpoints[projectType][gameProject]
    const url = endpoints.find(({ start, end }) => projectNumber >= start && projectNumber <= end).endpoint
    openUrl(`${BASE_URL}${url}`)
  }

  // badge de status (cores inline para não depender de CSS extra)
  const statusStyle = (() => {
    const s = String(status || "").toLowerCase();
    const map = {
      ready: { bg: "#6a1b9a", fg: "#fff" },
      copied: { bg: "#0288d1", fg: "#fff" },
      notified: { bg: "#1565c0", fg: "#fff" },
      success: { bg: "#2e7d32", fg: "#fff" },
      warning: { bg: "#ed6c02", fg: "#111" },
      error: { bg: "#c62828", fg: "#fff" },
    };
    const { bg, fg } = map[s] || { bg: "#6b7280", fg: "#fff" }; // cinza default
    return {
      display: "inline-block",
      padding: "2px 8px",
      borderRadius: "10px",
      fontSize: "12px",
      background: bg,
      color: fg,
      lineHeight: 1,
      whiteSpace: "nowrap"
    };
  })();

  return (
    <tr>
      <td>{id}</td>
      <td>{type}</td>
      <td>{loc}</td>
      <td>{game}</td>
      <td>{name}</td>
      <td>{duration}</td>
      <td>{owners}</td>

      {/* status com badge */}
      <td>
        <span style={statusStyle}>{status}</span>
      </td>

      {/* ações agrupadas em um único container, mantendo só ícones */}
      <td>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 10
          }}
        >
          <button
            type="button"
            className="icon-btn"
            disabled={disabled}
            onClick={() => openParentFileFolder(previewPath)}
            aria-label="Open source folder"
            title="Open source folder"
          >
            <img src={folderIcon} alt="" />
          </button>

          <button
            type="button"
            className={`icon-btn ${(mktoutData?.exists === false) ? "icon-dim" : ""}`}
            disabled={disabled || mktoutData?.exists === false}
            onClick={() => openFolder(mktoutData.path)}
            aria-label={masterData?.exists === true ? "Open MKTOUT folder" : "MKTOUT folder don't exist"}
            title={masterData?.exists === true ? "Open MKTOUT folder" : "MKTOUT folder don't exist"}
          >
            <img src={folderIcon} alt="" />
          </button>

          <button
            type="button"
            className={`icon-btn ${(masterData?.exists === false) ? "icon-dim" : ""}`}
            disabled={disabled || masterData?.exists === false}
            onClick={() => openFolder(masterData.path)}
            aria-label={masterData?.exists === true ? "Open Master folder" : "Master folder don't exist"}
            title={masterData?.exists === true ? "Open Master folder" : "Master folder don't exist"}
          >
            <img src={folderIcon} alt="" />
          </button>

          <button
            type="button"
            className="icon-btn"
            disabled={disabled}
            onClick={() => {
              handleMiroLink()
              openThumbnail(previewPath)
            }}
            aria-label="Open Thumbnail"
            title="Open Thumbnail"
          >
            <img src={thumbnailIcon} alt="" />
          </button>
        </div>
      </td>
    </tr>
  );
}
