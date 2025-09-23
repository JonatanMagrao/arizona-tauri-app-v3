from collections import namedtuple, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import shutil
import os
import psutil
import filecmp
import threading

from functions import long_path

CopyTask = namedtuple("CopyTask", ["source", "destination"])

class FileCopier:
    def __init__(self, config: dict = {}):
        self.max_workers = self._detect_max_workers()
        self.ignored_file_extensions = set(
            ext.lower() for ext in config.get("ignored_copy_file_extensions", [])
        )
        self.ignored_folder_names = set(
            name.lower() for name in config.get("ignored_copy_folder_names", [])
        )

        # === DEDUP: índices por destino (root) + lock ===
        self._dest_indexes: dict[Path, dict[int, list[Path]] ] = {}
        self._index_lock = threading.Lock()

    def _detect_max_workers(self):
        cpu_count = os.cpu_count() or 4
        cpu_usage = psutil.cpu_percent(interval=1)
        ram_available_gb = psutil.virtual_memory().available / (1024 ** 3)

        cpu_limit = max(1, cpu_count // 2) if cpu_usage > 80 else max(2, cpu_count - 2) if cpu_usage > 50 else cpu_count
        ram_limit = 2 if ram_available_gb < 4 else 4 if ram_available_gb < 8 else 8

        return min(cpu_limit, ram_limit)

    # === DEDUP: helpers de índice/conferência ===
    def _ensure_index(self, root: Path):
        """Garante que há um índice de tamanho->arquivos para o destino root."""
        key = long_path(root).resolve()
        with self._index_lock:
            if key in self._dest_indexes:
                return
        # constrói fora do lock pesado; só grava dentro
        idx = defaultdict(list)
        if root.exists():
            for p in long_path(root).rglob("*"):
                if p.is_file():
                    try:
                        idx[p.stat().st_size].append(Path(p))
                    except FileNotFoundError:
                        pass
        with self._index_lock:
            self._dest_indexes[key] = idx

    def _get_index(self, root: Path):
        """Retorna (idx_mutavel, key_root)."""
        key = long_path(root).resolve()
        with self._index_lock:
            idx = self._dest_indexes.get(key)
        if idx is None:
            self._ensure_index(root)
            with self._index_lock:
                idx = self._dest_indexes[key]
        return idx, key

    def _register_in_index(self, key_root: Path, file_path: Path):
        """Após copiar, registra o arquivo no índice (por tamanho)."""
        try:
            size = file_path.stat().st_size
        except FileNotFoundError:
            return
        with self._index_lock:
            self._dest_indexes[key_root].setdefault(size, []).append(file_path)

    def _has_duplicate_in_index(self, src_file: Path, idx: dict[int, list[Path]]) -> bool:
        """True se existir NO DESTINO algum arquivo com conteúdo idêntico ao src_file."""
        try:
            size = src_file.stat().st_size
        except FileNotFoundError:
            return False
        for cand in idx.get(size, []):
            try:
                if filecmp.cmp(str(long_path(src_file)), str(long_path(cand)), shallow=False):
                    return True
            except FileNotFoundError:
                continue
        return False

    def _copy_folder(self, source: Path, destination: Path):
        source_lp = long_path(source)
        destination_lp = long_path(destination)

        # Garante que a raiz do destino exista (mantém sua lógica + evita falha quando tudo é pulado)
        destination_lp.mkdir(parents=True, exist_ok=True)

        # Índice de dedup para este destino
        idx, key_root = self._get_index(destination)

        for item in source.rglob("*"):
            if item.is_file() and item.suffix.lower() in self.ignored_file_extensions:
                continue
            if any(part.lower() in self.ignored_folder_names for part in item.parts):
                continue

            relative_path = item.relative_to(source)
            item_lp = long_path(item)
            target_path = destination / relative_path
            target_path_lp = long_path(target_path)

            try:
                if item_lp.is_dir():
                    target_path_lp.mkdir(parents=True, exist_ok=True)
                else:
                    # === DEDUP: se já houver ARQUIVO IDÊNTICO em qualquer lugar do destino, pula
                    if self._has_duplicate_in_index(item, idx):
                        continue

                    target_path_lp.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item_lp, target_path_lp)

                    # atualiza índice
                    self._register_in_index(key_root, target_path)

            except Exception as e:
                print(f"⚠️ Failed to copy {item_lp} → {target_path_lp}: {e}")

    def _copy_item(self, task: CopyTask, max_retries=3):
        source = task.source
        destination = task.destination
        source_lp = long_path(source)
        destination_lp = long_path(destination)

        # Define a raiz do destino para dedup:
        # - se copiando uma pasta, a raiz é o próprio destino
        # - se copiando um arquivo, a raiz é a pasta do arquivo
        dest_root = destination if source.is_dir() else destination.parent
        idx, key_root = self._get_index(dest_root)

        for attempt in range(max_retries):
            try:
                if source.is_file() and source.suffix.lower() in self.ignored_file_extensions:
                    print(f"⏭️  Skipping excluded file: {source}")
                    return
                if source.is_dir() and source.name.lower() in self.ignored_folder_names:
                    print(f"⏭️  Skipping excluded folder: {source}")
                    return

                if source.is_file():
                    # === DEDUP: pular se já existir arquivo idêntico em QUALQUER lugar do destino
                    if self._has_duplicate_in_index(source, idx):
                        return
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source_lp, destination_lp)
                    # atualiza índice
                    self._register_in_index(key_root, destination)

                elif source.is_dir():
                    # garante que a raiz exista (mantém sua verificação posterior)
                    destination.mkdir(parents=True, exist_ok=True)
                    self._copy_folder(source, destination)

                if not destination.exists():
                    raise Exception(f"Destino não criado: {destination}")
                if source.is_file() and source.stat().st_size != destination.stat().st_size:
                    raise Exception(f"Tamanho diferente após cópia: {destination}")
                return

            except Exception as e:
                print(f"Erro ao copiar {source} (tentativa {attempt+1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    print(f"❌ Falha permanente em {source}")

    def copy_tasks(self, tasks: list[CopyTask]):
        # Pré-cria índices dos destinos (evita reconstruções por thread)
        roots = set()
        for t in tasks:
            root = t.destination if t.source.is_dir() else t.destination.parent
            roots.add(root)
        for r in roots:
            self._ensure_index(r)

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(self._copy_item, task) for task in tasks]
            for f in futures:
                f.result()

    def copy_all_projects(self, all_contents: list[tuple[Path, tuple[Path, Path]]]):
        all_file_tasks = []

        for src_folder_path, (mktout, master) in all_contents:
            all_file_tasks.append(CopyTask(source=src_folder_path, destination=mktout))
            all_file_tasks.append(CopyTask(source=src_folder_path, destination=master))

            print(f"Copying: __ {master.name} __\n"
                  f"From: {src_folder_path.parent}\n"
                  f"To: {mktout}\n"
                  f"To: {master}\n")

        self.copy_tasks(all_file_tasks)
