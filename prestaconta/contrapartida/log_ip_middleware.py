# log_ip_middleware.py
from django.utils.deprecation import MiddlewareMixin

class LogIPMiddleware(MiddlewareMixin):
    def process_request(self, request):
        ip = self.get_client_ip(request)
        method = request.method
        path = request.path
        if method == "GET":
            print(f"[{method}] {ip} -> {path}")
        return None

    def get_client_ip(self, request):
        # Caso esteja atrás de proxy ou load balancer
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
