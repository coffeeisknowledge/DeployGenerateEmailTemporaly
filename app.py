from flask import Flask, jsonify, request, Response
from flasgger import Swagger
from tempmail import EMail
from io import BytesIO

app = Flask(__name__)

swagger_config = {
    "swagger": "2.0",
    "headers": [
    ],
    "specs": [
        {
            "endpoint": 'apispec_1',
            "route": '/apispec_1.json',
            "rule_filter": lambda rule: True,  # all in
            "model_filter": lambda tag: True,  # all in
        }
    ],
    "static_url_path": "/flasgger_static",
    # "static_folder": "static",  # must be set by user
    "swagger_ui": True,
    "specs_route": "/apidocs/",
    "info": {
        "title": "Temporaly - TempMailAPI",
        "description": "API for generating and retrieving information pertaining to temporary emails",
        "contact": {
        "responsibleOrganization": "CodeMinds",
        "responsibleDeveloper": "CodeMinds Team",
        "url": "https://github.com/CodeMinds-AppsMoviles-SW65",
        },
        "version": "1.0.0"
    },
    "shemes": [
        "http",
        "https"
    ],
}

swagger = Swagger(app, config=swagger_config)


email = None

@app.route('/api/v1/create_email', methods=['POST'])
def CreateEmail():
    """
    Create a temporary email address.
    ---
    tags:
      - Email
    responses:
      200:
        description: A temporary email address
        schema:
          type: object
          properties:
            address:
              type: string
              example: test@example.com
      500:
        description: Internal Server Error
    """
    global email
    email = EMail()
    return jsonify(address=email.address), 200

@app.route('/api/v1/inbox', methods=['GET'])
def Inbox():
    """
    Get the inbox messages of the temporary email.
    ---
    tags:
      - Inbox
    responses:
      200:
        description: A list of messages in the inbox
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              from_addr:
                type: string
              subject:
                type: string
              date_str:
                type: string
                example: '2024-09-26 12:34:56'
      500:
        description: Internal Server Error
    """
    inbox = email.get_inbox()
    return jsonify([{
        'id': msg.id,
        'from_addr': msg.from_addr,
        'subject': msg.subject,
        'date_str': msg.date_str
    } for msg in inbox]), 200

@app.route('/api/v1/messages/<int:message_id>', methods=['GET'])
def ReadMessage(message_id):
    """
    Read a specific message by ID.
    ---
    tags:
      - Messages
    parameters:
      - name: message_id
        in: path
        required: true
        type: integer
    responses:
      200:
        description: The content of the message
        schema:
          type: object
          properties:
            id:
              type: integer
            from_addr:
              type: string
            subject:
              type: string
            body:
              type: string
            date_str:
              type: string
              example: '2024-09-26 12:34:56'
      404:
        description: Message not found
      500:
        description: Internal Server Error
    """
    try:
        message = email.get_message(message_id)
        return jsonify({
            'id': message.id,
            'from_addr': message.from_addr,
            'subject': message.subject,
            'body': message.body,
            'date_str': message.date_str
        }), 200
    except Exception as e:
        return jsonify(error=str(e)), 404

@app.route('/api/v1/messages/<int:message_id>/attachments/<string:filename>', methods=['GET'])
def DownloadAttachment(message_id, filename):
    """
    Download an attachment from a message.
    ---
    tags:
      - Attachments
    parameters:
      - name: message_id
        in: path
        required: true
        type: integer
      - name: filename
        in: path
        required: true
        type: string
    responses:
      200:
        description: Attachment file content
        schema:
          type: string
          format: binary
      404:
        description: Attachment not found
      500:
        description: Internal Server Error
    """
    # email = EMail()  # Manage the email instance appropriately
    # try:
    #     attachment = email.get_message(message_id).attachments
    #     for att in attachment:
    #         if att.filename == filename:
    #             return att.download(), 200
    #     return jsonify(error="Attachment not found"), 404
    # except Exception as e:
    #     return jsonify(error=str(e)), 404
    try:
        attachment = email.get_message(message_id).attachments
        for att in attachment:
            if att.filename == filename:
                # Asumiendo que `att.download()` devuelve los datos del archivo como bytes
                file_data = att.download()

                if not isinstance(file_data, bytes):
                    file_data = file_data.encode('utf-8')
                
                # Configurar el tipo de contenido basado en la extensión del archivo
                if filename.endswith('.txt'):
                    content_type = 'text/plain'
                elif filename.endswith('.pdf'):
                    content_type = 'application/pdf'
                elif filename.endswith('.jpg') or filename.endswith('.jpeg'):
                    content_type = 'image/jpeg'
                elif filename.endswith('.png'):
                    content_type = 'image/png'
                elif filename.endswith('.docx'):
                    content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                else:
                    content_type = 'application/octet-stream'  # Tipo genérico para archivos binarios
                
                response = Response(BytesIO(file_data), content_type=content_type)
                response.headers['Content-Disposition'] = f'attachment; filename={filename}'
                
                return response, 200

        return jsonify(error="Attachment not found"), 404
    except Exception as e:
        return jsonify(error=str(e)), 404

if __name__ == '__main__':
    app.run(debug=True)
