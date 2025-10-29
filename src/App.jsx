import { useState, useEffect } from "react";
import { callFunction } from "tauri-plugin-python-api";
import { readTextFile, writeTextFile, exists } from '@tauri-apps/plugin-fs';
import { join , dataDir} from "@tauri-apps/api/path";
import "./App.css";
import ProjectsPanel from "./components/ProjectTable/ProjectTable";
import ActionsBar from "./components/ActionBar/ActionBar";

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

  // estados
  const [data, setData] = useState([]);
  const [links, setLinks] = useState([]);
  const [linksInput, setLinksInput] = useState("");

  // estado do checkbox
  const [isTest, setIsTest] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const file = await getTestFile();
        const resp = await readTextFile(file)
        const json = JSON.parse(resp);

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

    try{

      const saida = JSON.parse(await loadProject(finalLinks));
      setData(saida);
      setLinks([]);
      setLinksInput("");
    }catch(e){
      console.error("Error on loadProject:", e);
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
    try {
      await pythonFunction(); // cria/copias pastas no backend
      const updated = await getProjectMetadata(); // pega o cache atualizado do backend
      const data = JSON.parse(updated);
      setData(data); // atualiza tabela → ícones atualizam opacidade
    } catch (e) {
      console.error("Error on copy & refresh:", e);
    }
  };


  const handleFullProcess = async () => {
    try {
      await handleUpdateStatus(copiar);
      await handleUpdateStatus(slackMessage);
      await handleUpdateStatus(mondayStatus);
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
          />
          Test mode: {isTest ? "Yes" : "No"}
        </label>
      </div>

      <button onClick={() => handleUpdateStatus(copiar)}>Copy</button>
      <button onClick={() => handleUpdateStatus(slackMessage)}>Slack</button>
      <button onClick={() => handleUpdateStatus(mondayStatus)}>Monday</button>
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
