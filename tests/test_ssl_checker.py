import pytest
import asyncio
from app.services.ssl_checker import SSLChecker
from app.models.ssl import SSLSecurityReport

class TestSSLChecker:
    
    @pytest.fixture
    def ssl_checker(self):
        """Create SSLChecker instance for testing"""
        return SSLChecker()
    
    @pytest.mark.asyncio
    async def test_good_ssl_site(self, ssl_checker):
        """Test SSL check on a site with good SSL configuration"""
        # Test with a known good SSL site
        result = await ssl_checker.check_ssl_comprehensive("https://google.com")
        
        assert result["hostname"] == "google.com"
        assert result["port"] == 443
        assert result["certificate"]["valid"] is True
        assert result["certificate"]["expired"] is False
        assert result["https_redirect"]["enforced"] is True
        assert result["security_score"] > 70  # Should have a good security score
        assert result["shame_worthy"]["worthy"] is False
    
    @pytest.mark.asyncio 
    async def test_expired_cert_detection(self, ssl_checker):
        """Test detection of expired certificates"""
        # Test with a site known to have SSL issues (or create mock)
        # For demo, we'll test with badssl.com which provides test SSL scenarios
        result = await ssl_checker.check_ssl_comprehensive("https://expired.badssl.com")
        
        if "error" not in result:  # If the test site is accessible
            assert result["certificate"]["expired"] is True
            assert result["security_score"] < 50  # Should have low score
            assert result["shame_worthy"]["worthy"] is True
            assert "expired" in str(result["shame_worthy"]["reasons"]).lower()
    
    @pytest.mark.asyncio
    async def test_self_signed_cert_detection(self, ssl_checker):
        """Test detection of self-signed certificates"""
        result = await ssl_checker.check_ssl_comprehensive("https://self-signed.badssl.com")
        
        if "error" not in result:  # If the test site is accessible
            assert result["certificate"]["self_signed"] is True
            assert result["security_score"] < 70
            assert result["shame_worthy"]["worthy"] is True
    
    @pytest.mark.asyncio
    async def test_http_only_site(self, ssl_checker):
        """Test site that doesn't enforce HTTPS"""
        # This will test HTTP redirect behavior
        result = await ssl_checker.check_ssl_comprehensive("http://neverssl.com")
        
        if "error" not in result:
            assert result["https_redirect"]["enforced"] is False
            assert result["security_score"] < 50
            assert result["shame_worthy"]["worthy"] is True
    
    def test_security_score_calculation(self, ssl_checker):
        """Test security score calculation logic"""
        # Test with mock certificate data
        cert_info = {
            "valid": True,
            "expired": False,
            "self_signed": False,
            "days_until_expiry": 90,
            "key_size": 2048
        }
        
        ssl_config = {
            "vulnerable_protocols": []
        }
        
        https_info = {
            "enforced": True,
            "hsts_enabled": True
        }
        
        score = ssl_checker._calculate_security_score(cert_info, ssl_config, https_info)
        assert score == 100  # Perfect score
        
        # Test with expired certificate
        cert_info["expired"] = True
        score = ssl_checker._calculate_security_score(cert_info, ssl_config, https_info)
        assert score <= 60  # Should be heavily penalized
    
    def test_shame_assessment(self, ssl_checker):
        """Test shame-worthiness assessment"""
        # Test expired certificate
        cert_info = {"expired": True, "self_signed": False}
        ssl_config = {"vulnerable_protocols": []}
        https_info = {"enforced": True}
        
        shame = ssl_checker._is_shame_worthy(cert_info, ssl_config, https_info)
        assert shame["worthy"] is True
        assert shame["severity"] == "critical"
        assert len(shame["reasons"]) > 0
        
        # Test good configuration
        cert_info = {"expired": False, "self_signed": False}
        shame = ssl_checker._is_shame_worthy(cert_info, ssl_config, https_info)
        assert shame["worthy"] is False
        assert shame["severity"] == "none"
    
    def test_recommendations_generation(self, ssl_checker):
        """Test security recommendations generation"""
        cert_info = {
            "expired": True,
            "self_signed": True,
            "days_until_expiry": -10,
            "key_size": 1024
        }
        
        ssl_config = {
            "vulnerable_protocols": ["TLSv1.0", "SSLv3"]
        }
        
        https_info = {
            "enforced": False,
            "hsts_enabled": False
        }
        
        recommendations = ssl_checker._generate_recommendations(cert_info, ssl_config, https_info)
        
        assert len(recommendations) > 0
        # Should have recommendations for all the issues
        rec_text = " ".join(recommendations).lower()
        assert "expired" in rec_text or "renew" in rec_text
        assert "https" in rec_text
        assert "hsts" in rec_text


# Real-world integration tests
@pytest.mark.asyncio
async def test_real_government_sites():
    """Test SSL checking on real government websites"""
    ssl_checker = SSLChecker()
    
    # Test sites with different SSL configurations
    test_sites = [
        "https://www.usa.gov",          # Should have good SSL
        "https://www.google.com",       # Reference good site
    ]
    
    results = []
    for site in test_sites:
        print(f"\n🔍 Checking SSL for: {site}")
        result = await ssl_checker.check_ssl_comprehensive(site)
        results.append(result)
        
        if "error" not in result:
            print(f"✅ Security Score: {result['security_score']}/100")
            print(f"🔒 Certificate Valid: {result['certificate']['valid']}")
            print(f"📅 Days until expiry: {result['certificate']['days_until_expiry']}")
            print(f"🛡️  HTTPS Enforced: {result['https_redirect']['enforced']}")
            print(f"😱 Shame Worthy: {result['shame_worthy']['worthy']}")
            
            if result["recommendations"]:
                print("💡 Recommendations:")
                for rec in result["recommendations"]:
                    print(f"   - {rec}")
        else:
            print(f"❌ Error: {result['error']}")
    
    # Basic assertions
    for result in results:
        if "error" not in result:
            assert "security_score" in result
            assert isinstance(result["security_score"], int)
            assert 0 <= result["security_score"] <= 100


@pytest.mark.asyncio
async def test_shame_wall_candidates():
    """Find government sites that deserve to be on a 'shame wall'"""
    ssl_checker = SSLChecker()
    
    # Test some potentially problematic sites
    test_sites = [
        "http://neverssl.com",          # HTTP only site (for testing)
        "https://expired.badssl.com",   # Expired cert (test site)
        "https://self-signed.badssl.com" # Self-signed cert (test site)
    ]
    
    shame_candidates = []
    
    for site in test_sites:
        try:
            result = await ssl_checker.check_ssl_comprehensive(site)
            if "error" not in result and result["shame_worthy"]["worthy"]:
                shame_candidates.append({
                    "site": site,
                    "severity": result["shame_worthy"]["severity"],
                    "reasons": result["shame_worthy"]["reasons"],
                    "score": result["security_score"]
                })
                print(f"\n🚨 SHAME CANDIDATE: {site}")
                print(f"   Severity: {result['shame_worthy']['severity']}")
                print(f"   Score: {result['security_score']}/100")
                print(f"   Reasons: {', '.join(result['shame_worthy']['reasons'])}")
        except Exception as e:
            print(f"Error checking {site}: {e}")
    
    print(f"\n📊 Found {len(shame_candidates)} shame-worthy sites")
    return shame_candidates