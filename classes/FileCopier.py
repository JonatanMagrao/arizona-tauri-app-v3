from collections import namedtuple, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import shutil
import os
import psutil
import filecmp
import threading
import time
from typing import Iterable, Union, Optional, Sequence

from utils import long_path

CopyTask = namedtuple("CopyTask", ["source", "destination"])
PathLike = Union[str, Path]

class FileCopier:
    def __init__(self):
        self.max_workers = self._detect_max_workers()

        # === DEDUP: índices por destino (root) + lock ===
        self._dest_indexes: dict[Path, dict[int, list[Path]]] = {}
        self._index_lock = threading.Lock()

    def _detect_max_workers(self):
        cpu_count = os.cpu_count() or 4
        cpu_usage = psutil.cpu_percent(interval=1)
        ram_available_gb = psutil.virtual_memory().available / (1024 ** 3)

        cpu_limit = max(1, cpu_count // 2) if cpu_usage > 80 else max(2,
                                                                      cpu_count - 2) if cpu_usage > 50 else cpu_count
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
        """Retorna (idx_mutavel, key_root). Sempre garante existência do índice."""
        key = long_path(root).resolve()
        with self._index_lock:
            idx = self._dest_indexes.get(key)

        if idx is None:
            # tenta construir (fora do lock pesado) e registrar
            self._ensure_index(root)
            with self._index_lock:
                idx = self._dest_indexes.get(key)
                if idx is None:
                    # fallback anti-raça: garante um índice vazio
                    idx = defaultdict(list)
                    self._dest_indexes[key] = idx

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
                # if source.is_file() and source.suffix.lower() in self.ignored_file_extensions:
                #     print(f"⏭️  Skipping excluded file: {source}")
                #     return
                # if source.is_dir() and source.name.lower() in self.ignored_folder_names:
                #     print(f"⏭️  Skipping excluded folder: {source}")
                #     return

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
                    raise Exception(
                        f"Tamanho diferente após cópia: {destination}")
                return

            except Exception as e:
                print(
                    f"Erro ao copiar {source} (tentativa {attempt+1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    print(f"❌ Falha permanente em {source}")

    def copy_tasks(self, tasks: list[CopyTask]):
        roots = set()
        for t in tasks:
            root = t.destination if t.source.is_dir() else t.destination.parent
            # normalize a mesma “key” usada internamente
            root_key = long_path(root).resolve()
            roots.add(root_key)

        for r in roots:
            self._ensure_index(r)

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(self._copy_item, task) for task in tasks]
            for f in futures:
                f.result()

    def copy_all_projects(self, groups: list[list]):
        tasks = []
        for group in groups:
            if not group or len(group) < 2:
                continue  # precisa ter src + ao menos 1 destino
            src = Path(group[0])

            seen = set()
            for item in group[1:]:
                if not item:
                    continue
                dstn = Path(item)   
                if dstn == src or dstn in seen:
                    continue
                seen.add(dstn)
                tasks.append(CopyTask(source=src, destination=dstn))

        if tasks:
            print("Copying projects...")
            self.copy_tasks(tasks)

        for task in groups:
            print("Copied:")
            print(f"\tFrom: {task[0]}")
            for dest in task[1:]:
                print(f"\tTo: {dest}")
            print("")

    def copy_variadic_groups(self, groups: Iterable[Sequence[PathLike]]):
        """
        Recebe grupos no formato (src, dest1, dest2, ...)
        e dispara as cópias reaproveitando copy_tasks().
        """
        tasks: list[CopyTask] = []
        for group in groups:
            if not group or len(group) < 2:
                continue  # precisa de src + pelo menos 1 destino

            src = Path(group[0])

            seen: set[Path] = set()
            for dest in group[1:]:
                if not dest:
                    continue
                dstn = Path(dest)
                if dstn == src or dstn in seen:
                    continue
                seen.add(dstn)
                tasks.append(CopyTask(source=src, destination=dstn))

        if tasks:
            self.copy_tasks(tasks)