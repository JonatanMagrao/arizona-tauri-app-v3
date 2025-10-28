import { useState, useEffect } from "react";
import { callFunction } from "tauri-plugin-python-api";
import "./App.css";
import ProjectsPanel from "./components/ProjectTable/ProjectTable";
import ActionsBar from "./components/ActionBar/ActionBar";

function App() {
  const loadProject = (links) => callFunction("loadProject", [links]);
  const copiar = () => callFunction("copiar", []);
  const slackMessage = () => callFunction("slackMessage", []);
  const mondayStatus = () => callFunction("mondayStatus", []);
  const getProjectMetadata = () => callFunction("getProjectMetadata", []);

  const openFolder = (filePath) => callFunction("openFolder", [filePath])
  const openThumbnail = (filePath) => callFunction("openThumbnail", [filePath])
  const openParentFileFolder = (filePath) => callFunction("openParentFileFolder", [filePath])

  // test env fns
  const enableTestEnv = () => callFunction("enableTestEnv", []);
  const disableTestEnv = () => callFunction("disableTestEnv", []);
  const isTestEnvEnabled = () => callFunction("isTestEnv", []);

  // estados
  const [data, setData] = useState([]);
  const [links, setLinks] = useState([]);
  const [linksInput, setLinksInput] = useState("");

  // estado do checkbox
  const [isTest, setIsTest] = useState(false);
  const [bootstrapped, setBootstrapped] = useState(false);

  // helper robusto para interpretar retorno (bool, "true"/"false", "1"/"0")
  const toBool = (v) => {
    if (typeof v === "boolean") return v;
    const s = String(v).trim().toLowerCase();
    return s === "true" || s === "1" || s === "yes";
  };

  useEffect(() => {
    (async () => {
      try {
        const resp = await isTestEnvEnabled();
        setIsTest(toBool(resp));
        console.log(resp)
      } catch (e) {
        console.error("Error on isTestEnvEnabled:", e);
      } finally {
        setBootstrapped(true);
      }
    })();
  }, []);

  const handleTestCheckbox = async (e) => {
    const next = e.target.checked;
    // UI otimista
    const prev = isTest;
    setIsTest(next);
    try {
      if (next) await enableTestEnv();
      else await disableTestEnv();
    } catch (err) {
      console.error("Error on enableTestEnv:", err);
      // reverte em caso de erro
      setIsTest(prev);
    }
  };

  const handleLoadProject = async (valueFromBar) => {
    const candidate = String(valueFromBar ?? linksInput).trim();
    const finalLinks = candidate
      ? Array.from(new Set([...links, candidate]))
      : [...links];
    if (finalLinks.length === 0) return;

    const saida = JSON.parse(await loadProject(finalLinks));
    setData(saida);
    setLinks([]);
    setLinksInput("");
  };

  const handleAddLink = (urlFromBar) => {
    const url = String(urlFromBar ?? linksInput).trim();
    if (!url) return;
    if (links.includes(url)) {
      setLinksInput("");
      return;
    }
    setLinks((prev) => [...prev, url]);
    setLinksInput("");
  };

  // ⬇️ NOVO: copiar e depois atualizar o metadata (para refletir exists)
  const handleCopyAndRefresh = async () => {
    try {
      await copiar(); // cria/copias pastas no backend
      const updated = await getProjectMetadata(); // pega o cache atualizado do backend
      const data = JSON.parse(updated);
      setData(data); // atualiza tabela → ícones atualizam opacidade
    } catch (e) {
      console.error("Error on copy & refresh:", e);
    }
  };

  const handleNotifySlack = async () => {
    try{
      await slackMessage();
      const updated = await getProjectMetadata()
      const data = JSON.parse(updated);
      setData(data);
    } catch (e) {
      console.error("Error on notify slack:", e);
    }
  }

  const handleFullProcess = async () => {
    try {
      await handleCopyAndRefresh();
      await handleNotifySlack();
      await mondayStatus();
    } catch (e) {
      console.error("Error on full process:", e);
    }
  }

  return (
    <div>
      <ActionsBar
        value={linksInput}
        onChange={setLinksInput}
        onEnter={handleAddLink}
        onLeftClick={handleLoadProject}
        onRightClick={handleAddLink}
        leftLabel="Load"
        rightLabel="Add"
      />

      <div style={{ display: "flex", gap: 8, alignItems: "center", margin: "8px 0" }}>
        <label style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <input
            type="checkbox"
            checked={isTest}
            onChange={handleTestCheckbox}
            disabled={loadingTest}
          />
          Test Mode { isTest ? "(enabled)" : "(disabled)"}
        </label>
      </div>

      <button onClick={handleCopyAndRefresh}>Copy</button>
      <button onClick={handleNotifySlack}>Slack</button>
      <button onClick={mondayStatus}>Monday</button>
      <button onClick={handleFullProcess}>Full</button>
      <button onClick={() => { console.log(links); }}>Show links</button>

      <ProjectsPanel
        data={data}
        openFolder={openFolder}
        openThumbnail={openThumbnail}
        openParentFileFolder={openParentFileFolder}
      />
    </div>
  );
}

export default App;
