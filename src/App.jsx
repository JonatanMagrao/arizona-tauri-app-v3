import { useState, useEffect } from "react";
import { callFunction } from "tauri-plugin-python-api";
import "./App.css";
import ProjectsPanel from "./components/ProjectTable/ProjectTable";
import ActionsBar from "./components/ActionBar/ActionBar";

function App() {
  const loadProject = (links) => callFunction("loadProject", [links])
  const copiar = () => callFunction("copiar", [])
  const slackMessage = () => callFunction("slackMessage", [])
  const mondayStatus = () => callFunction("mondayStatus", [])
  const completo = () => callFunction("completo", [])

  const [data,setData] = useState([])
  const [links,setLinks] = useState([])
  const [linksInput, setLinksInput] = useState("")

  const handleLoadProject = async (valueFromBar) => {
    // 1) pega o texto do input (se veio do ActionBar) e normaliza
    const candidate = String(valueFromBar ?? linksInput).trim();

    // 2) monta a lista final, adicionando o candidate se não for vazio nem duplicado
    const finalLinks = candidate
      ? Array.from(new Set([...links, candidate]))
      : [...links];

    if (finalLinks.length === 0) return;

    // 3) chama o Python com a lista combinada
    const saida = JSON.parse(await loadProject(finalLinks));
    setData(saida);

    // 4) limpa fila e input
    setLinks([]);
    setLinksInput("");
  };

  const handleAddLink = (urlFromBar) => {
    const url = String(urlFromBar ?? linksInput).trim();
    if (!url) return;
    // opcional: evitar duplicados
    if (links.includes(url)) {
      setLinksInput("");
      return;
    }
    setLinks(prev => [...prev, url]);  // append sem mutar
    setLinksInput("");                 // limpa o input
  };

  return (
    <div>

      <ActionsBar
        value={linksInput}
        onChange={setLinksInput}
        onEnter={handleAddLink}
        onLeftClick={handleLoadProject}   // primeiro botão
        onRightClick={handleAddLink}  // segundo botão
        leftLabel="Load"
        rightLabel="Add"
      />

      <button onClick={copiar}>copiar</button>
      <button onClick={slackMessage}>slack message</button>
      <button onClick={mondayStatus}>monday</button>
      <button onClick={completo}>completo</button>
      <button onClick={() => {
        console.log(links)
      }}>show</button>
      
      <ProjectsPanel data={data} />

    </div>
  );
}

export default App;
