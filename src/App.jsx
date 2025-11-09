import { useState, useEffect } from "react";
import { callFunction } from "tauri-plugin-python-api";
import { readTextFile, writeTextFile, exists } from '@tauri-apps/plugin-fs';
import { join, dataDir } from "@tauri-apps/api/path";
import "./App.css";
import ProjectsPanel from "./components/ProjectTable/ProjectTable";
import ActionsBar from "./components/ActionBar/ActionBar";
import ErrorLogger from "./components/ErrorLogger/ErrorLogger";

function App() {

  const REL_DIR = "com.superplay.out-process.test-env";
  const REL_FILE = "test.json";

  const getTestFile = async () => {
    const base = await dataDir()
    const file = await join(base, REL_DIR, REL_FILE);
    return file;
  }

  const loadProject = (links) => callFunction("loadProject", [links]);
  const copiar = () => callFunction("copiar", []);
  const slackMessage = () => callFunction("slackMessage", []);
  const mondayStatus = () => callFunction("mondayStatus", []);
  const getProjectMetadata = () => callFunction("getProjectMetadata", []);

  const openFolder = (filePath) => callFunction("openFolder", [filePath])
  const openThumbnail = (filePath) => callFunction("openThumbnail", [filePath])
  const openParentFileFolder = (filePath) => callFunction("openParentFileFolder", [filePath])
  const configJson = () => callFunction("configJson", [])
  const slackTokenExists = () => callFunction("slackTokenExists", [])
  const genSlackToken = () => callFunction("genSlackToken", [])

  // estados
  const [data, setData] = useState([]);
  const [links, setLinks] = useState([]);
  const [linksInput, setLinksInput] = useState("");
  const [miroEndpoints, setMiroEndpoints] = useState({})
  const [errors, setErrors] = useState([])

  // estado do checkbox
  const [isTest, setIsTest] = useState(false);

  // estado global para bloquear botões durante ações
  const [busy, setBusy] = useState(false);

  const handleClearErrors = () => setErrors([]);

  useEffect(() => {
    (async () => {
      try {
        const file = await getTestFile();
        const resp = await readTextFile(file)
        const miroConfig = JSON.parse(await configJson()).miro_endpoints
        const json = JSON.parse(resp);

        setMiroEndpoints(miroConfig)
        setIsTest(json.is_test);
      } catch (e) {
        console.error("Error on isTestEnvEnabled:", e);
      }
    })();
  }, []);

  const handleTestCheckbox = async (e) => {
    const isChecked = e.target.checked;

    const file = await getTestFile();
    const content = await readTextFile(file)
    const json = JSON.parse(content);

    json.is_test = isChecked

    await writeTextFile(file, JSON.stringify(json))

    setIsTest(isChecked)

  };

  const handleLoadProject = async (valueFromBar) => {
    const candidate = String(valueFromBar ?? linksInput).trim();
    const finalLinks = candidate
      ? Array.from(new Set([...links, candidate]))
      : [...links];
    if (finalLinks.length === 0) return;

    if (busy) return;
    setBusy(true);
    try {
      let saida = JSON.parse(await loadProject(finalLinks));
      saida = saida.filter(item => {
        if (!item) return false;
        if (item.status === "error") {
          console.warn(item.msg)
          setErrors(prev => [...prev, item.msg])
          return false
        }
        return true
      })
      setData(saida);
      setLinks([]);
      setLinksInput("");
    } catch (e) {
      console.error("Error on loadProject:", e);
    } finally {
      setBusy(false);
    }
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

  const handleUpdateStatus = async (pythonFunction) => {
    if (busy) return;
    setBusy(true);
    try {
      await pythonFunction(); // cria/copias pastas no backend
      const updated = await getProjectMetadata(); // pega o cache atualizado do backend
      const data = JSON.parse(updated);
      data.forEach(item => {
        if (item.status === "error") {
          setErrors(prev => [...prev, item.msg])
        }
      })
      setData(data); // atualiza tabela → ícones atualizam opacidade
    } catch (e) {
      console.error("Error on copy & refresh:", e);
    } finally {
      setBusy(false);
    }
  };

  const handleSlackMessage = async () => {
    if (busy) return;
    setBusy(true);
    try {
      const slatkTokenExists = await slackTokenExists();
      if (slatkTokenExists === "False") {
        console.log(slatkTokenExists)
        const slackTokenResponse = await genSlackToken()
        const json = JSON.parse(slackTokenResponse)
        if(json.status === "error") {
          console.warn(json.msg)
          setErrors(prev => [...prev, json.msg])
          return
        }
      }

      await handleUpdateStatus(slackMessage)
    } catch (e) {
      console.error("Error on slack message:", e);
    } finally {
      setBusy(false);
    }
  }


  const handleFullProcess = async () => {
    if (busy) return;
    setBusy(true);
    try {
      await handleUpdateStatus(copiar);
      await handleSlackMessage();
      await handleUpdateStatus(mondayStatus);
    } catch (e) {
      console.error("Error on full process:", e);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <ActionsBar
        disabled={busy}
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
          />
          Test mode: {isTest ? "Yes" : "No"}
        </label>
      </div>

      <button disabled={busy} onClick={() => handleUpdateStatus(copiar)}>Copy</button>
      <button disabled={busy} onClick={handleSlackMessage}>Slack</button>
      <button disabled={busy} onClick={() => handleUpdateStatus(mondayStatus)}>Monday</button>
      <button disabled={busy} onClick={handleFullProcess}>Full</button>
      {/* <button disabled={busy} onClick={() => { console.log(links); }}>Show links</button> */}
      <button disabled={busy} onClick={async () => {
        try {
          setBusy(true);
          const resp = await genSlackToken()
          const json = JSON.parse(resp);
          if(json.status === "error"){
            console.warn(json.msg)
            setErrors(prev => [...prev, json.msg])
            return
          }
        } catch (e) {
          console.error("Error on gen:", e);
        } finally {
          setBusy(false);
        }
      }}>Generate Token</button>

      <ProjectsPanel
        disabled={busy}
        data={data}
        openFolder={openFolder}
        openThumbnail={openThumbnail}
        openParentFileFolder={openParentFileFolder}
        miroEndpoints={miroEndpoints}
      />

      <ErrorLogger errors={errors} onClear={handleClearErrors} />
    </div>
  );
}

export default App;
