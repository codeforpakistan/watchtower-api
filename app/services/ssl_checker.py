import ssl
import socket
import datetime
import asyncio
import httpx
from urllib.parse import urlparse
from typing import Dict, Optional, List, Any
from cryptography import x509
from cryptography.hazmat.backends import default_backend
import logging

logger = logging.getLogger(__name__)

class SSLChecker:
    def __init__(self):
        self.timeout = 10
        
    async def check_ssl_comprehensive(self, url: str) -> Dict[str, Any]:
        """
        Comprehensive SSL/TLS security check for a website
        Returns detailed security analysis including certificate validity, encryption strength, etc.
        """
        parsed_url = urlparse(url)
        hostname = parsed_url.hostname
        port = parsed_url.port or 443
        
        if not hostname:
            return {"error": "Invalid URL - no hostname found"}
            
        # Check if site redirects to HTTPS
        https_redirect = await self._check_https_redirect(url)
        
        # Get SSL certificate info
        cert_info = await self._get_certificate_info(hostname, port)
        
        # Check SSL/TLS configuration
        ssl_config = await self._check_ssl_configuration(hostname, port)
        
        # Calculate overall security score
        security_score = self._calculate_security_score(cert_info, ssl_config, https_redirect)
        
        return {
            "url": url,
            "hostname": hostname,
            "port": port,
            "scan_date": datetime.datetime.utcnow().isoformat(),
            "https_redirect": https_redirect,
            "certificate": cert_info,
            "ssl_configuration": ssl_config,
            "security_score": security_score,
            "recommendations": self._generate_recommendations(cert_info, ssl_config, https_redirect),
            "shame_worthy": self._is_shame_worthy(cert_info, ssl_config, https_redirect)
        }
    
    async def _check_https_redirect(self, url: str) -> Dict[str, Any]:
        """Check if HTTP redirects to HTTPS and if HTTPS is enforced"""
        parsed = urlparse(url)
        
        # Test HTTP version
        http_url = f"http://{parsed.hostname}"
        if parsed.port and parsed.port != 80:
            http_url += f":{parsed.port}"
            
        https_info = {
            "enforced": False,
            "redirects_to_https": False,
            "hsts_enabled": False,
            "hsts_max_age": None,
            "mixed_content_risk": False
        }
        
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=self.timeout) as client:
                # Check HTTP redirect
                try:
                    http_response = await client.get(http_url)
                    if http_response.url.scheme == "https":
                        https_info["redirects_to_https"] = True
                        https_info["enforced"] = True
                except Exception as e:
                    logger.debug(f"HTTP check failed for {http_url}: {e}")
                
                # Check HTTPS and HSTS headers
                https_url = url if url.startswith("https://") else f"https://{parsed.hostname}"
                try:
                    https_response = await client.get(https_url)
                    
                    # Check HSTS header
                    hsts_header = https_response.headers.get("strict-transport-security")
                    if hsts_header:
                        https_info["hsts_enabled"] = True
                        # Extract max-age
                        for directive in hsts_header.split(";"):
                            if directive.strip().startswith("max-age="):
                                try:
                                    https_info["hsts_max_age"] = int(directive.split("=")[1])
                                except:
                                    pass
                                    
                except Exception as e:
                    logger.debug(f"HTTPS check failed for {https_url}: {e}")
                    
        except Exception as e:
            logger.error(f"HTTPS redirect check failed for {url}: {e}")
            
        return https_info
    
    async def _get_certificate_info(self, hostname: str, port: int) -> Dict[str, Any]:
        """Get detailed SSL certificate information"""
        cert_info = {
            "valid": False,
            "expired": True,
            "self_signed": False,
            "days_until_expiry": 0,
            "issuer": None,
            "subject": None,
            "valid_from": None,
            "valid_until": None,
            "san_domains": [],
            "signature_algorithm": None,
            "key_size": None,
            "certificate_chain_length": 0,
            "errors": []
        }
        
        try:
            # Create SSL context
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            # Connect and get certificate
            with socket.create_connection((hostname, port), timeout=self.timeout) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert_der = ssock.getpeercert_chain()[0]
                    cert = x509.load_der_x509_certificate(cert_der, default_backend())
                    
                    # Basic certificate info
                    cert_info["valid_from"] = cert.not_valid_before.isoformat()
                    cert_info["valid_until"] = cert.not_valid_after.isoformat()
                    
                    # Check if certificate is valid (not expired)
                    now = datetime.datetime.utcnow()
                    if cert.not_valid_before <= now <= cert.not_valid_after:
                        cert_info["valid"] = True
                        cert_info["expired"] = False
                        
                    # Days until expiry
                    days_until_expiry = (cert.not_valid_after - now).days
                    cert_info["days_until_expiry"] = days_until_expiry
                    
                    # Certificate details
                    cert_info["issuer"] = cert.issuer.rfc4514_string()
                    cert_info["subject"] = cert.subject.rfc4514_string()
                    cert_info["signature_algorithm"] = cert.signature_algorithm_oid._name
                    
                    # Get public key info
                    public_key = cert.public_key()
                    if hasattr(public_key, 'key_size'):
                        cert_info["key_size"] = public_key.key_size
                    
                    # Check for self-signed
                    if cert.issuer == cert.subject:
                        cert_info["self_signed"] = True
                    
                    # Get SAN (Subject Alternative Names)
                    try:
                        san_ext = cert.extensions.get_extension_for_oid(x509.ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
                        cert_info["san_domains"] = [name.value for name in san_ext.value]
                    except x509.ExtensionNotFound:
                        pass
                    
                    # Certificate chain length
                    cert_info["certificate_chain_length"] = len(ssock.getpeercert_chain())
                    
        except ssl.SSLError as e:
            cert_info["errors"].append(f"SSL Error: {str(e)}")
            logger.error(f"SSL error for {hostname}:{port}: {e}")
        except socket.timeout:
            cert_info["errors"].append("Connection timeout")
            logger.error(f"Timeout connecting to {hostname}:{port}")
        except Exception as e:
            cert_info["errors"].append(f"Unexpected error: {str(e)}")
            logger.error(f"Unexpected error checking {hostname}:{port}: {e}")
            
        return cert_info
    
    async def _check_ssl_configuration(self, hostname: str, port: int) -> Dict[str, Any]:
        """Check SSL/TLS configuration and supported protocols"""
        ssl_config = {
            "protocols_supported": [],
            "ciphers_supported": [],
            "vulnerable_protocols": [],
            "weak_ciphers": [],
            "perfect_forward_secrecy": False,
            "compression_enabled": False,
            "renegotiation_secure": True
        }
        
        # Test different TLS versions
        protocols_to_test = [
            ("SSLv2", ssl.PROTOCOL_SSLv23),  # Will be rejected by modern systems
            ("SSLv3", ssl.PROTOCOL_SSLv23),  # Will be rejected by modern systems  
            ("TLSv1.0", ssl.PROTOCOL_TLSv1),
            ("TLSv1.1", ssl.PROTOCOL_TLSv1_1),
            ("TLSv1.2", ssl.PROTOCOL_TLSv1_2),
            ("TLSv1.3", ssl.PROTOCOL_TLS),
        ]
        
        for protocol_name, protocol in protocols_to_test:
            try:
                context = ssl.SSLContext(protocol)
                context.set_ciphers('ALL:@SECLEVEL=0')  # Allow all ciphers for testing
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                
                with socket.create_connection((hostname, port), timeout=5) as sock:
                    with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                        ssl_config["protocols_supported"].append(protocol_name)
                        
                        # Mark vulnerable protocols
                        if protocol_name in ["SSLv2", "SSLv3", "TLSv1.0", "TLSv1.1"]:
                            ssl_config["vulnerable_protocols"].append(protocol_name)
                            
            except Exception:
                # Protocol not supported (which is good for old protocols)
                pass
        
        return ssl_config
    
    def _calculate_security_score(self, cert_info: Dict, ssl_config: Dict, https_info: Dict) -> int:
        """Calculate overall security score (0-100)"""
        score = 100
        
        # Certificate issues
        if not cert_info["valid"]:
            score -= 50  # Major penalty for invalid cert
        if cert_info["expired"]:
            score -= 40  # Major penalty for expired cert
        if cert_info["self_signed"]:
            score -= 30  # Penalty for self-signed
        if cert_info["days_until_expiry"] < 30:
            score -= 20  # Penalty for soon-to-expire cert
        if cert_info["key_size"] and cert_info["key_size"] < 2048:
            score -= 25  # Penalty for weak key
            
        # SSL configuration issues
        if ssl_config["vulnerable_protocols"]:
            score -= len(ssl_config["vulnerable_protocols"]) * 15
            
        # HTTPS enforcement issues
        if not https_info["enforced"]:
            score -= 30  # Major penalty for no HTTPS enforcement
        if not https_info["hsts_enabled"]:
            score -= 15  # Penalty for no HSTS
            
        return max(0, min(100, score))
    
    def _generate_recommendations(self, cert_info: Dict, ssl_config: Dict, https_info: Dict) -> List[str]:
        """Generate security recommendations"""
        recommendations = []
        
        if cert_info["expired"]:
            recommendations.append("🚨 URGENT: SSL certificate has expired - renew immediately")
        elif cert_info["days_until_expiry"] < 30:
            recommendations.append(f"⚠️  SSL certificate expires in {cert_info['days_until_expiry']} days - renew soon")
            
        if cert_info["self_signed"]:
            recommendations.append("🔒 Use a trusted Certificate Authority instead of self-signed certificates")
            
        if not https_info["enforced"]:
            recommendations.append("🔐 Enforce HTTPS by redirecting all HTTP traffic to HTTPS")
            
        if not https_info["hsts_enabled"]:
            recommendations.append("🛡️  Enable HTTP Strict Transport Security (HSTS) headers")
            
        if ssl_config["vulnerable_protocols"]:
            recommendations.append(f"🚫 Disable vulnerable protocols: {', '.join(ssl_config['vulnerable_protocols'])}")
            
        if cert_info["key_size"] and cert_info["key_size"] < 2048:
            recommendations.append("🔑 Use at least 2048-bit RSA keys or 256-bit ECC keys")
            
        return recommendations
    
    def _is_shame_worthy(self, cert_info: Dict, ssl_config: Dict, https_info: Dict) -> Dict[str, Any]:
        """Determine if site deserves to be publicly shamed for poor security"""
        shame_reasons = []
        severity = "none"
        
        if cert_info["expired"]:
            shame_reasons.append("Expired SSL certificate")
            severity = "critical"
        elif not https_info["enforced"]:
            shame_reasons.append("No HTTPS enforcement")
            severity = "high" if severity != "critical" else severity
        elif cert_info["self_signed"]:
            shame_reasons.append("Self-signed certificate")
            severity = "medium" if severity not in ["critical", "high"] else severity
        elif ssl_config["vulnerable_protocols"]:
            shame_reasons.append(f"Supports vulnerable protocols: {', '.join(ssl_config['vulnerable_protocols'])}")
            severity = "medium" if severity not in ["critical", "high"] else severity
            
        return {
            "worthy": len(shame_reasons) > 0,
            "severity": severity,
            "reasons": shame_reasons
        }