def process_http_request(environ, start_response):
    status = '200 OK'
    response_headers = [
        ('Content-type', 'text/plain; charset=utf-8'),
    ]
    start_response(status, response_headers)
    text = 'Here be dragons'.encode('utf-8')
    return [text]

# pip install gunicorn
# gunicorn -b 127.0.0.1:8001 select_supplier.wsgi:application 
# kill -9 `ps aux | grep gunicorn | awk '{print $2}'` 
