# Editor e Impressor de Etiquetas Térmicas (80mm) - Salgados & Cia

Sistema completo de edição visual e impressão de etiquetas térmicas de 80mm com acionamento de corte automático (guilhotina).

## 🚀 Recursos
- **Personalização de Logotipo**: Escolha qualquer imagem do computador e ajuste tamanho e posição em tempo real.
- **Nome do Produto**: Edição de texto e tamanho da fonte com botões de atalho rápido.
- **Gerador de QR Code**: Geração instantânea de QR Code para qualquer link ou texto (padrão: `https://salgadosecia.online/`).
- **Data de Validade**: Seleção rápida de datas (+1 dia, +2 dias, +7 dias, etc.).
- **Compatibilidade Térmica**: Otimizado para bobinas térmicas de 80mm (área de impressão 72mm x 80mm / 203 DPI) sem estrias térmicas.
- **Controle de Impressão e Corte**: Reconhecimento automático de impressoras do Windows e acionamento de corte (guilhotina) por etiqueta.
- **Exportação**: Baixe a etiqueta em PNG de alta resolução a qualquer momento.

## 💻 Como Rodar Localmente (com suporte à impressora física)
1. Instale os pacotes necessários:
```bash
pip install flask pillow qrcode pyside6
```
2. Execute o servidor local:
```bash
python app.py
```
ou dê dois cliques no arquivo `iniciar_editor.bat`.
3. Acesse `http://127.0.0.1:5000` no seu navegador.
