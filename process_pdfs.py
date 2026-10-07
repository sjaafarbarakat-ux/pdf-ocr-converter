import argparse
import json
import os
import sys
from pathlib import Path
from typing import Iterable, List, Optional

import fitz  # PyMuPDF
from pdf2image import convert_from_path
import pytesseract
from PIL import Image, ImageOps

# ------------------------------------------------------------
# Configurações do Windows
# ------------------------------------------------------------
# Se o Tesseract não estiver no PATH, ajuste aqui.
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Se o Poppler não estiver no PATH, ajuste aqui.
# Exemplos comuns:
#   C:\poppler\Library\bin
#   C:\Program Files\poppler\bin
#   C:\tools\poppler\bin
COMMON_POPPLER_PATHS = [
    r"C:\poppler\Library\bin",
    r"C:\poppler\bin",
    r"C:\Program Files\poppler\bin",
    r"C:\Program Files\Poppler\bin",
]

# Tente usar o primeiro local válido; caso contrário, deixe None.
def find_poppler_path() -> Optional[str]:
    for candidate in COMMON_POPPLER_PATHS:
        if os.path.exists(candidate):
            return candidate
    return None

POPPLER_PATH = find_poppler_path()

if os.path.exists(TESSERACT_CMD):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

# ------------------------------------------------------------
# Funções auxiliares
# ------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Converte PDFs para texto e OCR manualmente em uma pasta do Windows.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--folder",
        type=str,
        default=".",
        help="Pasta contendo os PDFs. Use '.' para a pasta atual.",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Processa também PDFs em subpastas.",
    )
    parser.add_argument(
        "--lang",
        type=str,
        default="por+eng",
        help="Idiomas do OCR (ex.: 'por+eng', 'eng', 'por').",
    )
    parser.add_argument(
        "--output",
        type=str,
        choices=["txt", "json", "both"],
        default="txt",
        help="Formato da saída gerada para cada PDF.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Sobrescreve arquivos de saída existentes.",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Pula arquivos de saída que já existem.",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="Resolução usada ao converter páginas para OCR.",
    )
    return parser.parse_args()


def find_pdf_files(folder: Path, recursive: bool) -> List[Path]:
    pattern = "**/*.pdf" if recursive else "*.pdf"
    files = sorted(folder.glob(pattern), key=lambda p: str(p).lower())
    return [p for p in files if p.is_file()]


def file_exists_for_output(pdf_path: Path, output_format: str) -> bool:
    txt_path = pdf_path.with_suffix(".txt")
    json_path = pdf_path.with_suffix(".json")
    if output_format == "txt":
        return txt_path.exists()
    if output_format == "json":
        return json_path.exists()
    return txt_path.exists() or json_path.exists()


def should_process(pdf_path: Path, output_format: str, overwrite: bool, skip_existing: bool) -> bool:
    if overwrite:
        return True
    if not skip_existing:
        return True
    return not file_exists_for_output(pdf_path, output_format)


def extract_text_native(pdf_path: Path) -> str:
    text_parts: List[str] = []
    try:
        doc = fitz.open(str(pdf_path))
        for page_number, page in enumerate(doc, start=1):
            page_text = page.get_text("text").strip()
            if page_text:
                text_parts.append(f"--- Página {page_number} ---\n{page_text}\n")
        doc.close()
    except Exception as exc:
        print(f"  [WARN] Extração nativa falhou: {exc}")
    return "\n".join(text_parts).strip()


def ocr_pdf(pdf_path: Path, lang: str, dpi: int) -> str:
    try:
        pages = convert_from_path(
            str(pdf_path),
            dpi=dpi,
            poppler_path=POPPLER_PATH,
            fmt="ppm",
        )
    except Exception as exc:
        print(f"  [ERRO] Falha ao converter PDF para imagens: {exc}")
        return ""

    ocr_parts: List[str] = []
    for idx, page_image in enumerate(pages, start=1):
        try:
            gray = ImageOps.grayscale(page_image)
            page_text = pytesseract.image_to_string(gray, lang=lang)
            cleaned = page_text.strip()
            if cleaned:
                ocr_parts.append(f"--- Página {idx} ---\n{cleaned}\n")
        except Exception as exc:
            print(f"  [WARN] Falha OCR na página {idx}: {exc}")
    return "\n".join(ocr_parts).strip()


def save_txt(pdf_path: Path, text: str) -> Path:
    out_path = pdf_path.with_suffix(".txt")
    out_path.write_text(text, encoding="utf-8")
    return out_path


def save_json(pdf_path: Path, text: str) -> Path:
    out_path = pdf_path.with_suffix(".json")
    payload = {
        "arquivo_pdf": str(pdf_path.name),
        "texto": text,
    }
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


def process_pdf(pdf_path: Path, output_format: str, lang: str, dpi: int, overwrite: bool, skip_existing: bool) -> bool:
    if not should_process(pdf_path, output_format, overwrite, skip_existing):
        print(f"-> {pdf_path.name}")
        print("  [SKIP] Já existe resultado para este PDF.")
        return False

    print(f"-> {pdf_path.name}")

    text = extract_text_native(pdf_path)
    if not text.strip():
        print("  [OCR] Texto nativo não encontrado. Usando OCR...")
        text = ocr_pdf(pdf_path, lang=lang, dpi=dpi)

    if not text.strip():
        print("  [ERRO] Nenhum texto foi extraído do PDF.")
        return False

    produced = []
    if output_format in ("txt", "both"):
        txt_path = save_txt(pdf_path, text)
        produced.append(str(txt_path))
    if output_format in ("json", "both"):
        json_path = save_json(pdf_path, text)
        produced.append(str(json_path))

    print(f"  [OK] Texto extraído com sucesso.")
    for item in produced:
        print(f"  Salvo em: {item}")
    return True


def main() -> int:
    args = parse_args()

    folder = Path(args.folder).expanduser().resolve()
    if not folder.exists():
        print(f"[ERRO] Pasta não existe: {folder}")
        return 1
    if not folder.is_dir():
        print(f"[ERRO] Caminho não é uma pasta: {folder}")
        return 2

    pdf_files = find_pdf_files(folder, args.recursive)
    if not pdf_files:
        print(f"Nenhum arquivo PDF encontrado em: {folder}")
        return 0

    print(f"Processando {len(pdf_files)} PDF(s) em: {folder}")

    results = []
    for pdf_path in pdf_files:
        results.append(
            process_pdf(
                pdf_path,
                output_format=args.output,
                lang=args.lang,
                dpi=args.dpi,
                overwrite=args.overwrite,
                skip_existing=args.skip_existing,
            )
        )

    success_count = sum(1 for item in results if item)
    print(f"\nResumo: {success_count}/{len(pdf_files)} PDF(s) processados com sucesso.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
