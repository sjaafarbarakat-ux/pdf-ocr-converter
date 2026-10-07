# PDF OCR Converter

Conversor manual de arquivos PDF para texto/ocr em Windows usando Python.

Funcionalidades:
- Processa PDFs em uma pasta escolhida
- Pode buscar também em subpastas
- Tenta extrair texto nativo do PDF
- Se não houver texto, faz OCR com Tesseract
- Salva arquivos `.txt` ao lado do PDF
- Suporta saída em texto ou JSON
- Não executa automaticamente ao abrir a pasta; você dispara o comando manualmente

Requisitos do sistema:
- Python 3.10+
- Tesseract OCR
- Poppler para Windows

Instalação rápida:

1. Instale Python 3.10+
2. Instale Tesseract OCR
3. Instale Poppler para Windows e lembre do caminho
4. Instale as dependências:

```bat
pip install -r requirements.txt
```

5. Ajuste os caminhos no arquivo `process_pdfs.py`, se necessário:
- `TESSERACT_CMD` (opcional)
- `POPPLER_PATH` (opcional)

Uso:

Na pasta que contém os PDFs:

```bat
python process_pdfs.py
```

Ou passando a pasta explicitamente:

```bat
python process_pdfs.py --folder "C:\Documentos\PDFs"
```

Opções:

```bat
python process_pdfs.py --help
```

Exemplos:

```bat
python process_pdfs.py --folder "C:\Documentos\PDFs" --recursive
python process_pdfs.py --folder "C:\Documentos\PDFs" --output json
python process_pdfs.py --folder "C:\Documentos\PDFs" --lang "por+eng"
python process_pdfs.py --folder "C:\Documentos\PDFs" --recursive --skip-existing
```

Observações:
- O programa não roda sozinho ao abrir a pasta.
- Ele só processa quando você executa o comando manualmente.
- Arquivos `.txt` e `.json` são salvos ao lado do PDF original.

Exemplo de saída esperada:

```txt
Processando 3 PDF(s)
-> arquivo1.pdf
  Texto extraído com sucesso.
  Salvo em: C:\Documentos\PDFs\arquivo1.txt
```
