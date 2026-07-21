from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import urllib.parse

class VulnerableHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed_path.query)

        # 1. Sensitive Information Disclosure (.env file exposure)
        if parsed_path.path in ['/.env', '/config.json', '/.git/config']:
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"DB_PASSWORD=SuperSecretPassword123!\nAWS_SECRET_KEY=AKIAIOSFODNN7EXAMPLE\nAPI_KEY=live_sk_998877665544332211")
            return

        # 2. Reflected XSS Vulnerability & Unescaped Output
        search_query = query.get('q', [''])[0]
        
        self.send_response(200)
        # Intentional CORS misconfiguration and missing security headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()

        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>Vulnerable Test Application</title>
        </head>
        <body>
            <h1>⚠️ Vulnerable Web Application for Security Testing</h1>
            <p>This is an intentionally vulnerable test target running inside GitHub Actions runner.</p>
            
            <form action="/" method="GET">
                <input type="text" name="q" placeholder="Search..." value="{search_query}">
                <button type="submit">Search</button>
            </form>

            <div id="results">
                <h2>Search Results for: {search_query}</h2>
            </div>

            <ul>
                <li><a href="/.env">Exposed .env file</a></li>
                <li><a href="/config.json">Exposed Config</a></li>
            </ul>
        </body>
        </html>
        """
        self.wfile.write(html_content.encode('utf-8'))

    # Suppress verbose log messages
    def log_message(self, format, *args):
        return

if __name__ == '__main__':
    server_address = ('0.0.0.0', 8080)
    # Use ThreadingHTTPServer to handle high-concurrency requests from Nuclei scanner without timing out
    httpd = ThreadingHTTPServer(server_address, VulnerableHandler)
    print("Multi-threaded Vulnerable Server listening on port 8080...")
    httpd.serve_forever()
