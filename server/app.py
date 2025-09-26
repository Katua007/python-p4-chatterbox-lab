# server/app.py
from flask import Flask, request, make_response
from flask_cors import CORS
from flask_migrate import Migrate
from models import db, Message
from datetime import datetime

app = Flask(__name__)

# --- Configuration ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- Extensions ---
CORS(app)
db.init_app(app)
migrate = Migrate(app, db)


# --- Helper Function for Serialization ---
def message_to_dict(message):
    """Converts a Message object to a dictionary for JSON response."""
    return {
        'id': message.id,
        'body': message.body,
        'username': message.username,
        # Convert datetime objects to ISO format string for JSON
        'created_at': message.created_at.isoformat(),
        'updated_at': message.updated_at.isoformat(),
    }


# --- Routes ---

# GET /messages & POST /messages
@app.route('/messages', methods=['GET', 'POST'])
def messages():
    if request.method == 'GET':
        # GET /messages: returns an array of all messages, ordered by created_at ascending.
        messages_list = Message.query.order_by(Message.created_at).all()
        messages_json = [message_to_dict(m) for m in messages_list]

        return make_response(messages_json, 200)

    elif request.method == 'POST':
        # POST /messages: creates a new message.
        data = request.get_json()
        
        # Simple input validation
        if not data or 'body' not in data or 'username' not in data:
            return make_response({'errors': ['Missing body or username in request data.']}, 400)

        try:
            new_message = Message(
                body=data.get('body'),
                username=data.get('username')
            )
            
            db.session.add(new_message)
            db.session.commit()

            # Return the newly created post as JSON (201 Created)
            return make_response(message_to_dict(new_message), 201)

        except ValueError as e:
            # Catches validation errors from the model
            return make_response({'errors': [str(e)]}, 400)
        except Exception:
             # Catches other potential database errors
            return make_response({'errors': ['Could not process the message creation.']}, 500)


# PATCH /messages/<int:id> & DELETE /messages/<int:id>
@app.route('/messages/<int:id>', methods=['PATCH', 'DELETE'])
def message_by_id(id):
    # Find the message first
    message = db.session.get(Message, id)
    if not message:
        return make_response({'error': 'Message not found'}, 404)

    if request.method == 'PATCH':
        # PATCH /messages/<int:id>: updates the body of the message.
        data = request.get_json()
        
        if 'body' in data:
            try:
                # The onupdate=datetime.utcnow handles the updated_at timestamp
                message.body = data['body'] 
                db.session.add(message)
                db.session.commit()

                # Return the updated message as JSON (202 Accepted)
                return make_response(message_to_dict(message), 202)
            
            except ValueError as e:
                return make_response({'errors': [str(e)]}, 400)
            except Exception:
                return make_response({'errors': ['Could not update the message.']}, 500)
        
        else:
            return make_response({'errors': ['Missing body in update request.']}, 400)


    elif request.method == 'DELETE':
        # DELETE /messages/<int:id>: deletes the message.
        db.session.delete(message)
        db.session.commit()

        # Return 204 No Content for a successful deletion
        return make_response('', 204)


if __name__ == '__main__':
    app.run(port=5000, debug=True)