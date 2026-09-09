"""Servicio para gestionar túneles de Cloudflare vía API."""
import os
import requests
from django.conf import settings


class CloudflareService:
    """Cliente para la API de Cloudflare."""
    
    BASE_URL = "https://api.cloudflare.com/client/v4"
    
    def __init__(self):
        self.token = os.getenv("CLOUDFLARE_API_TOKEN")
        self.email = os.getenv("CLOUDFLARE_API_EMAIL")
        self.key = os.getenv("CLOUDFLARE_API_KEY")
        self.account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
        self.zone_id = os.getenv("CLOUDFLARE_ZONE_ID")

        if self.token:
            self.headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            }
        elif self.email and self.key:
            self.headers = {
                "X-Auth-Email": self.email,
                "X-Auth-Key": self.key,
                "Content-Type": "application/json",
            }
        else:
            raise ValueError("Configura CLOUDFLARE_API_TOKEN o CLOUDFLARE_API_EMAIL+CLOUDFLARE_API_KEY en .env")
    
    def crear_tunnel(self, nombre: str) -> dict:
        """Crea un túnel y devuelve {tunnel_id, token}."""
        url = f"{self.BASE_URL}/accounts/{self.account_id}/cfd_tunnel"
        data = {"name": nombre, "tunnel_source": "cloudflare"}
        
        r = requests.post(url, headers=self.headers, json=data, timeout=30)
        r.raise_for_status()
        result = r.json()
        
        if not result.get("success"):
            raise Exception(f"Error creando túnel: {result.get('errors')}")
        
        tunnel_id = result["result"]["id"]
        token = result["result"]["token"]
        
        return {"tunnel_id": tunnel_id, "token": token}
    
    def crear_dns_cname(self, subdominio: str, tunnel_id: str) -> bool:
        """Crea registro CNAME apuntando al túnel."""
        url = f"{self.BASE_URL}/zones/{self.zone_id}/dns_records"
        data = {
            "type": "CNAME",
            "name": subdominio,
            "content": f"{tunnel_id}.cfargotunnel.com",
            "proxied": True,  # Naranja = Cloudflare proxy (HTTPS automático)
            "ttl": 1
        }
        
        r = requests.post(url, headers=self.headers, json=data, timeout=30)
        r.raise_for_status()
        result = r.json()
        
        return result.get("success", False)
    
    def verificar_tunel_activo(self, tunnel_id: str) -> bool:
        """Verifica si un túnel tiene conexiones activas."""
        url = f"{self.BASE_URL}/accounts/{self.account_id}/cfd_tunnel/{tunnel_id}"
        
        try:
            r = requests.get(url, headers=self.headers, timeout=10)
            r.raise_for_status()
            result = r.json()
            
            # Un túnel está activo si tiene al menos 1 conexión
            conexiones = result.get("result", {}).get("connections", [])
            return len(conexiones) > 0
        except Exception:
            return False
    

    def configurar_ingress(self, tunnel_id: str, hostname: str, service: str = None) -> bool:
        """Configura las reglas de ingress del túnel (hacia dónde enrutar el tráfico)."""
        if service is None:
            port = getattr(settings, "LABCLIN_INGRESS_PORT", "8000")
            service = f"http://127.0.0.1:{port}"
        url = f"{self.BASE_URL}/accounts/{self.account_id}/cfd_tunnel/{tunnel_id}/configurations"
        data = {
            "config": {
                "ingress": [
                    {
                        "hostname": hostname,
                        "service": service,
                        "originRequest": {"connectTimeout": 10}
                    },
                    {"service": "http_status:404"}
                ]
            }
        }
        r = requests.put(url, headers=self.headers, json=data, timeout=30)
        r.raise_for_status()
        result = r.json()
        return result.get("success", False)

    def eliminar_tunnel(self, tunnel_id: str) -> bool:
        """Elimina un túnel (después de marcarlo como inactivo)."""
        # Primero marcar como inactivo
        url_patch = f"{self.BASE_URL}/accounts/{self.account_id}/cfd_tunnel/{tunnel_id}"
        requests.patch(url_patch, headers=self.headers, json={"active": False}, timeout=30)
        
        # Luego eliminar
        url_delete = url_patch
        r = requests.delete(url_delete, headers=self.headers, timeout=30)
        return r.status_code in (200, 204)
