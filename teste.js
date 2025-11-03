const objeto = {
  "miro_endpoints": {
    "video": {
      "dd": [
        { "start": 1, "end": 100, "endpoint": "uXjVO5iAfsE=/" },
        { "start": 101, "end": 149, "endpoint": "uXjVP-2_oqc=/" },
        { "start": 150, "end": 199, "endpoint": "uXjVMef6-BM=/" },
        { "start": 200, "end": 249, "endpoint": "uXjVNnFDjy8=/" },
        { "start": 250, "end": 299, "endpoint": "uXjVNwBlKMU=/" },
        { "start": 300, "end": 349, "endpoint": "uXjVNwDoAUw=/" }
      ],
      "dx": [
        { "start": 1, "end": 49, "endpoint": "uXjVPBEktmQ=/" },
        { "start": 49, "end": 99, "endpoint": "uXjVNwQVTKg=/" },
        { "start": 100, "end": 149, "endpoint": "uXjVNwVk3Lw=/" }
      ],
      "ds": [
        { "start": 1, "end": 49, "endpoint": "uXjVLC8dgkY=/" },
        { "start": 50, "end": 100, "endpoint": "uXjVJadnxlI=/" }
      ]
    }
  }
}

console.log(objeto.miro_endpoints.video.dd.find(({ start, end }) => 150 >= start && 150 <= end))