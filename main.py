import json
from http.server import HTTPServer, BaseHTTPRequestHandler

USERS_LIST = [
    {
        "id": 1,
        "username": "theUser",
        "firstName": "John",
        "lastName": "James",
        "email": "john@email.com",
        "password": "12345",
    }
]


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    def _set_response(self, status_code=200, body=None):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(body if body is not None else {}).encode('utf-8'))

    def _pars_body(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                return None
            return json.loads(self.rfile.read(content_length).decode('utf-8'))
        except Exception:
            return None

    def _validate_user_fields(self, user, check_id=True):
        """Validates individual user object structure and field types."""
        if not isinstance(user, dict):
            return False
        
        required_fields = {
            "username": str,
            "firstName": str,
            "lastName": str,
            "email": str,
            "password": str
        }
        if check_id:
            required_fields["id"] = int

        if set(user.keys()) != set(required_fields.keys()):
            return False

        for key, expected_type in required_fields.items():
            if not isinstance(user[key], expected_type) or isinstance(user[key], bool):
                return False

        return True

    def do_GET(self):
        global USERS_LIST

        if self.path == '/reset':
            USERS_LIST = [
                {
                    "id": 1,
                    "username": "theUser",
                    "firstName": "John",
                    "lastName": "James",
                    "email": "john@email.com",
                    "password": "12345",
                }
            ]
            self._set_response(200, USERS_LIST)

        elif self.path == '/users':
            self._set_response(200, USERS_LIST)

        elif self.path.startswith('/user/'):
            username = self.path[6:]  # Extract username after '/user/'
            user = next((u for u in USERS_LIST if u.get("username") == username), None)
            
            if user:
                self._set_response(200, user)
            else:
                self._set_response(400, {"error": "User not found"})
                
        else:
            self._set_response(404, {"error": "Not Found"})

    def do_POST(self):
        body = self._pars_body()

        if self.path == '/user':
            if body is None or not self._validate_user_fields(body, check_id=True):
                self._set_response(400, {})
                return

            if any(u['id'] == body['id'] for u in USERS_LIST):
                self._set_response(400, {})
                return

            USERS_LIST.append(body)
            self._set_response(201, body)

        elif self.path == '/user/createWithList':
            if not isinstance(body, list) or len(body) == 0:
                self._set_response(400, {})
                return

            for user in body:
                if not self._validate_user_fields(user, check_id=True):
                    self._set_response(400, {})
                    return

            existing_ids = {u['id'] for u in USERS_LIST}
            new_ids = [u['id'] for u in body]

            if any(new_id in existing_ids for new_id in new_ids) or len(new_ids) != len(set(new_ids)):
                self._set_response(400, {})
                return

            USERS_LIST.extend(body)
            self._set_response(201, body)

        else:
            self._set_response(404, {})

    def do_PUT(self):
        if self.path.startswith('/user/'):
            try:
                user_id = int(self.path[6:])
            except ValueError:
                self._set_response(400, {"error": "not valid request data"})
                return

            body = self._pars_body()

            # Validate PUT request body structure
            if body is None or not self._validate_user_fields(body, check_id=False):
                self._set_response(400, {"error": "not valid request data"})
                return

            user = next((u for u in USERS_LIST if u.get("id") == user_id), None)

            if not user:
                self._set_response(404, {"error": "User not found"})
                return

            user.update(body)
            self._set_response(200, user)
        else:
            self._set_response(404, {"error": "Not Found"})

    def do_DELETE(self):
        if self.path.startswith('/user/'):
            try:
                user_id = int(self.path[6:])
            except ValueError:
                self._set_response(404, {"error": "User not found"})
                return

            user = next((u for u in USERS_LIST if u.get("id") == user_id), None)

            if user:
                USERS_LIST.remove(user)
                self._set_response(200, {})
            else:
                self._set_response(404, {"error": "User not found"})
        else:
            self._set_response(404, {"error": "User not found"})


def run(server_class=HTTPServer, handler_class=SimpleHTTPRequestHandler, host='localhost', port=8000):
    server_address = (host, port)
    httpd = server_class(server_address, handler_class)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()


if __name__ == '__main__':
    from sys import argv

    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()