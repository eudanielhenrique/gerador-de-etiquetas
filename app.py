import os
import sys
import time
import base64
import io
from flask import Flask, render_template, request, jsonify, send_from_directory
from PIL import Image, ImageEnhance
import qrcode
from PySide6.QtGui import QGuiApplication, QPageSize, QPainter, QImage
from PySide6.QtCore import QSizeF
from PySide6.QtPrintSupport import QPrinter, QPrinterInfo

# Ensure QGuiApplication is initialized
qt_app = QGuiApplication.instance() or QGuiApplication(sys.argv)

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

@app.route('/api/print', methods=['OPTIONS'])
@app.route('/api/printers', methods=['OPTIONS'])
def handle_options():
    return '', 204

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/printers', methods=['GET'])
def get_printers():
    try:
        printers = []
        default_printer = None
        for p in QPrinterInfo.availablePrinters():
            name = p.printerName()
            is_def = p.isDefault()
            is_therm = any(k in name.upper() for k in ['HOMOLOGACAO', 'TANCA', 'TP-', 'POS', 'RECEIPT', 'THERMAL', 'CUPOM'])
            if is_def:
                default_printer = name
            printers.append({
                'name': name,
                'is_default': is_def,
                'is_thermal': is_therm
            })
            
        # Prioritize thermal printer as recommended
        recommended = next((p['name'] for p in printers if p['name'] == 'HOMOLOGACAO'), default_printer)
        return jsonify({
            'success': True,
            'printers': printers,
            'recommended': recommended
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/qrcode', methods=['GET'])
def get_qrcode():
    data = request.args.get('data', 'https://salgadosecia.online/')
    try:
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=8,
            border=1
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color='black', back_color='white').convert('RGB')
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        b64 = 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()
        return jsonify({'success': True, 'image': b64})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/upload-logo', methods=['POST'])
def upload_logo():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'Nenhum arquivo enviado'}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Nome de arquivo inválido'}), 400
            
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ['.png', '.jpg', '.jpeg', '.webp', '.bmp']:
            return jsonify({'success': False, 'error': 'Formato não suportado'}), 400
            
        filename = f"logo_custom_{int(time.time())}{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Read and return base64
        with open(filepath, 'rb') as f:
            b64 = f"data:image/{ext.replace('.', '')};base64," + base64.b64encode(f.read()).decode()
            
        return jsonify({
            'success': True,
            'url': f"/static/uploads/{filename}",
            'image_b64': b64
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/print', methods=['POST'])
def handle_print():
    try:
        data = request.get_json()
        printer_name = data.get('printer_name', 'HOMOLOGACAO')
        copies = int(data.get('copies', 1))
        cut_each = bool(data.get('cut_each', True))
        image_b64 = data.get('image_data', '')
        
        if not image_b64:
            return jsonify({'success': False, 'error': 'Nenhuma imagem fornecida'}), 400
            
        if copies < 1:
            copies = 1
        if copies > 100:
            copies = 100
            
        # Decode base64 image
        if ',' in image_b64:
            image_b64 = image_b64.split(',')[1]
        img_bytes = base64.b64decode(image_b64)
        pil_img = Image.open(io.BytesIO(img_bytes)).convert('RGB')
        
        # Ensure exact 574 x 639 size for 203 DPI thermal head
        if pil_img.size != (574, 639):
            pil_img = pil_img.resize((574, 639), Image.Resampling.LANCZOS)
            
        raw_data = pil_img.tobytes('raw', 'RGB')
        qimg = QImage(raw_data, pil_img.width, pil_img.height, pil_img.width * 3, QImage.Format.Format_RGB888).copy()
        
        printer_info = QPrinterInfo.printerInfo(printer_name)
        if printer_info.isNull():
            return jsonify({'success': False, 'error': f"Impressora '{printer_name}' não encontrada"}), 404
            
        is_thermal = any(k in printer_name.upper() for k in ['HOMOLOGACAO', 'TANCA', 'TP-', 'POS', 'RECEIPT', 'THERMAL', 'CUPOM'])
        
        for i in range(1, copies + 1):
            printer = QPrinter(printer_info)
            printer.setDocName(f"Etiqueta_{i}_{int(time.time())}")
            if is_thermal:
                printer.setResolution(203)
                printer.setPageSize(QPageSize(QSizeF(72.0, 80.0), QPageSize.Unit.Millimeter))
                
            painter = QPainter(printer)
            # Fill white background and inset image for guillotine safety margins
            painter.fillRect(painter.window(), Qt.GlobalColor.white)
            target_rect = painter.window().adjusted(0, 16, 0, -24)
            painter.drawImage(target_rect, qimg)
            painter.end()
            
            if cut_each and i < copies:
                time.sleep(1.2)  # Pause for hardware cutter
                
        return jsonify({
            'success': True,
            'message': f"{copies} etiqueta(s) enviada(s) para '{printer_name}' com corte automático!"
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    port = 5000
    print(f"Iniciando Editor de Etiquetas na porta {port}...")
    app.run(host='127.0.0.1', port=port, debug=False, threaded=False)
