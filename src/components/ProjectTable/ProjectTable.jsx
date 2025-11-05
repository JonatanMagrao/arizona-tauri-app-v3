import React from "react";
import "./ProjectTable.css";
import ProjectRow from "../ProjectRow/ProjectRow";

export default function ProjectTable({ data, openFolder, openThumbnail, openParentFileFolder,miroEndpoints, disabled }) {

  const rows = data.map((item,i) => {

    if(item.status === "error"){
      // console.log(item.msg)
      return null
    }

    const id = `${item.id.game_code}-${item.id.project_type}-${item.id.project_number}-${item.id.project_iteration}`
    const loc = item?.language?.abbr ? item.language.abbr.toUpperCase() : ""
    const duration = item.duration ? item.duration : ""
    const mktoutData = item.mktout_folder_path
    const masterData = item.master_folder_path
    const previewPath = item.video_to_preview

    return (
      <ProjectRow
        key={`${id}_${i}`}
        id={id}
        type={item.type_label}
        loc={loc}
        game={item.game.name}
        name={item.project_name.replace(`${id}_`,"").replace(`_${loc}_${duration}s`,"")}
        duration={`${duration} Seconds`}
        owners={item.producers}
        status={item.status}
        mktoutData={mktoutData}
        masterData={masterData}
        previewPath={previewPath}
        openFolder={openFolder}
        openThumbnail={openThumbnail}
        openParentFileFolder={openParentFileFolder}
        miroEndpoints={miroEndpoints}
        disabled={disabled}
      />
    );
  })
  
  return (
    <div className="board">
      {/* wrapper responsável pela rolagem horizontal quando faltar espaço */}
      <div className="tableWrap">
        <table className="projects">
          <colgroup>
            <col className="col-id" />
            <col className="col-type" />
            <col className="col-loc" />
            <col className="col-game" />
            <col className="col-name" />
            <col className="col-duration" />
            <col className="col-owners" />
            <col className="col-status" />
          </colgroup>

          <thead>
            <tr>
              <th>PROJECT ID</th>
              <th>TYPE</th>
              <th>LOC</th>
              <th>GAME</th>
              <th>PROJECT NAME</th>
              <th>DURATION</th>
              <th>OWNERS</th>
              <th>STATUS</th>
            </tr>
          </thead>

          <tbody>
            {rows}
          </tbody>
        </table>
      </div>
    </div>
  );
}
