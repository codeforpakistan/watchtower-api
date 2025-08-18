from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Dict, Any

class SSLCertificate(BaseModel):
    valid: bool
    expired: bool
    self_signed: bool
    days_until_expiry: int
    issuer: Optional[str] = None
    subject: Optional[str] = None
    valid_from: Optional[str] = None
    valid_until: Optional[str] = None
    san_domains: List[str] = []
    signature_algorithm: Optional[str] = None
    key_size: Optional[int] = None
    certificate_chain_length: int = 0
    errors: List[str] = []

class HTTPSConfiguration(BaseModel):
    enforced: bool
    redirects_to_https: bool
    hsts_enabled: bool
    hsts_max_age: Optional[int] = None
    mixed_content_risk: bool = False

class SSLConfiguration(BaseModel):
    protocols_supported: List[str] = []
    ciphers_supported: List[str] = []
    vulnerable_protocols: List[str] = []
    weak_ciphers: List[str] = []
    perfect_forward_secrecy: bool = False
    compression_enabled: bool = False
    renegotiation_secure: bool = True

class ShameAssessment(BaseModel):
    worthy: bool
    severity: str  # none, low, medium, high, critical
    reasons: List[str] = []

class SSLSecurityReport(BaseModel):
    url: str
    hostname: str
    port: int
    scan_date: str
    https_redirect: HTTPSConfiguration
    certificate: SSLCertificate
    ssl_configuration: SSLConfiguration
    security_score: int  # 0-100
    recommendations: List[str] = []
    shame_worthy: ShameAssessment

class SSLBulkScanResult(BaseModel):
    """For scanning multiple government sites at once"""
    total_scanned: int
    shame_worthy_sites: List[Dict[str, Any]] = []
    expired_certificates: List[Dict[str, Any]] = []
    no_https_sites: List[Dict[str, Any]] = []
    overall_statistics: Dict[str, Any] = {}
    scan_date: datetime