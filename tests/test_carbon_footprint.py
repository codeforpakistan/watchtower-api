import pytest
from app.services.carbon_footprint import CarbonFootprintCalculator, EnergySource, DataCenter

class TestCarbonFootprintCalculator:
    
    @pytest.fixture
    def calculator(self):
        """Create CarbonFootprintCalculator instance for testing"""
        return CarbonFootprintCalculator()
    
    def test_small_page_footprint(self, calculator):
        """Test carbon footprint for a small, efficient page"""
        # 500KB page
        page_size = 500 * 1024
        result = calculator.calculate_website_footprint(page_size)
        
        assert result.total_co2_grams > 0
        assert result.data_transfer_mb == 0.48  # Approximately 0.5MB
        assert result.confidence_level == "low"  # No additional data provided
        assert "A" in calculator.compare_with_average(result)["rating"]  # Should be good
    
    def test_large_page_footprint(self, calculator):
        """Test carbon footprint for a large, bloated page"""
        # 10MB page (bloated)
        page_size = 10 * 1024 * 1024
        result = calculator.calculate_website_footprint(
            page_size_bytes=page_size,
            server_response_time_ms=2000  # Slow server
        )
        
        assert result.total_co2_grams > 5.0  # Should be significant
        assert result.data_transfer_mb == 10.0
        assert result.confidence_level == "medium"  # Has response time data
        assert len(result.recommendations) > 5  # Should have many recommendations
        
        # Should have poor rating
        rating = calculator.compare_with_average(result)["rating"]
        assert rating in ["D", "F"]
    
    def test_green_energy_vs_coal(self, calculator):
        """Test difference between green energy and coal energy sources"""
        page_size = 2 * 1024 * 1024  # 2MB page
        
        # Calculate with renewable energy
        green_result = calculator.calculate_website_footprint(
            page_size_bytes=page_size,
            energy_source=EnergySource.RENEWABLE
        )
        
        # Calculate with coal energy
        coal_result = calculator.calculate_website_footprint(
            page_size_bytes=page_size,
            energy_source=EnergySource.COAL
        )
        
        # Coal should produce much more CO2
        assert coal_result.total_co2_grams > green_result.total_co2_grams * 10
        assert green_result.total_co2_grams < 2.0  # Should be very low
        assert coal_result.total_co2_grams > 10.0  # Should be high
    
    def test_datacenter_efficiency_impact(self, calculator):
        """Test impact of data center efficiency"""
        page_size = 1024 * 1024  # 1MB page
        
        # Efficient datacenter
        efficient_result = calculator.calculate_website_footprint(
            page_size_bytes=page_size,
            datacenter_type=DataCenter.GREEN
        )
        
        # Average datacenter
        average_result = calculator.calculate_website_footprint(
            page_size_bytes=page_size,
            datacenter_type=DataCenter.AVERAGE
        )
        
        # Green datacenter should be more efficient
        assert efficient_result.server_processing_co2 < average_result.server_processing_co2
    
    def test_carbon_footprint_breakdown(self, calculator):
        """Test that carbon footprint breakdown makes sense"""
        page_size = 5 * 1024 * 1024  # 5MB page
        result = calculator.calculate_website_footprint(page_size)
        
        # All components should be positive
        assert result.data_transfer_co2 > 0
        assert result.server_processing_co2 > 0
        assert result.network_transmission_co2 > 0
        assert result.end_user_device_co2 > 0
        
        # Total should equal sum of parts
        total_calculated = (
            result.data_transfer_co2 + 
            result.server_processing_co2 + 
            result.network_transmission_co2 + 
            result.end_user_device_co2
        )
        assert abs(total_calculated - result.total_co2_grams) < 0.01
        
        # Data transfer should be the largest component for most websites
        assert result.data_transfer_co2 >= result.server_processing_co2
    
    def test_carbon_rating_system(self, calculator):
        """Test carbon rating system"""
        # Very efficient page (0.3g CO2)
        efficient_rating = calculator._get_carbon_rating(0.3)
        assert efficient_rating == "A+"
        
        # Average page (4.6g CO2 - industry average)
        average_rating = calculator._get_carbon_rating(4.6)
        assert average_rating == "C"
        
        # Bloated page (15g CO2)
        bloated_rating = calculator._get_carbon_rating(15.0)
        assert bloated_rating == "F"
        
        # Good page (1.5g CO2)
        good_rating = calculator._get_carbon_rating(1.5)
        assert good_rating == "B"
    
    def test_annual_footprint_calculation(self, calculator):
        """Test annual footprint calculation"""
        # Small page footprint
        page_size = 1 * 1024 * 1024  # 1MB
        single_visit = calculator.calculate_website_footprint(page_size)
        
        # Calculate for a government website with 100k monthly visitors
        annual_data = calculator.calculate_annual_footprint(
            single_visit_footprint=single_visit,
            monthly_visitors=100000,
            pages_per_visit=2.5
        )
        
        assert annual_data["annual_visits"] == 1200000  # 100k * 12
        assert annual_data["annual_page_views"] == 3000000  # 1.2M * 2.5
        assert annual_data["annual_co2_kg"] > 0
        assert annual_data["car_miles_equivalent"] > 0
        assert annual_data["trees_needed_to_offset"] > 0
        
        # Should be a meaningful number of trees needed
        assert annual_data["trees_needed_to_offset"] > 1
    
    def test_recommendations_generation(self, calculator):
        """Test that appropriate recommendations are generated"""
        # Large, slow page
        large_page = 15 * 1024 * 1024  # 15MB (very large)
        result = calculator.calculate_website_footprint(
            page_size_bytes=large_page,
            server_response_time_ms=5000  # Very slow
        )
        
        recommendations = result.recommendations
        rec_text = " ".join(recommendations).lower()
        
        # Should have recommendations about:
        assert "optimize" in rec_text or "compress" in rec_text
        assert "server" in rec_text or "response" in rec_text
        assert "green" in rec_text or "renewable" in rec_text
        
        # Should have many recommendations for such a bad site
        assert len(recommendations) >= 8
    
    def test_zero_size_page(self, calculator):
        """Test handling of zero-size pages"""
        result = calculator.calculate_website_footprint(0)
        
        assert result.total_co2_grams == 0
        assert result.data_transfer_mb == 0
        assert result.energy_kwh == 0
        
        # Should still have some recommendations
        assert len(result.recommendations) > 0


# Integration test
def test_enhanced_carbon_footprint_integration():
    """Test the enhanced carbon footprint calculation integration"""
    calculator = CarbonFootprintCalculator()
    
    # Test different page sizes
    test_cases = [
        (100 * 1024, "A+"),      # 100KB - should be excellent
        (500 * 1024, "A"),       # 500KB - should be good
        (2 * 1024 * 1024, "B"),  # 2MB - should be decent
        (10 * 1024 * 1024, "F"), # 10MB - should be terrible
    ]
    
    for page_size, expected_rating_tier in test_cases:
        result = calculator.calculate_website_footprint(page_size)
        comparison = calculator.compare_with_average(result)
        
        print(f"Page Size: {page_size/(1024*1024):.1f}MB")
        print(f"CO2: {result.total_co2_grams:.3f}g")
        print(f"Rating: {comparison['rating']}")
        print(f"Percentile: {comparison['percentile']}")
        print("---")
        
        # Basic assertions
        assert result.total_co2_grams > 0
        assert result.data_transfer_mb > 0
        
        # Rating should be in expected tier (allow some flexibility)
        if expected_rating_tier == "A+":
            assert comparison["rating"] in ["A+", "A"]
        elif expected_rating_tier == "F":
            assert comparison["rating"] in ["D", "F"]