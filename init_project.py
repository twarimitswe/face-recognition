from pathlib import Path

#Canonical project structure

structure={
    "data/enroll":[],
    "data/db":[],
    "models":["embedder_arcface.onnx"],
    "src":[
        "camera.py",
        "align.py",
        "detect.py",
        "embed.py",
        "enroll.py",
        "evaluate.py",
        "haar_5pt.py",
        "landmark.py",
        "recognize.py",
    ],
    "book":[],
}

for forlder, files in structure.items() :
    folder_path=Path(forlder)
    folder_path.mkdir(parents=True,exist_ok=True)

    for file in files:
        file_path=folder_path/file
        if not file_path.exists():
            file_path.touch()

print("face recognition project structure is created successfully.")

    
    