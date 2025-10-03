import logging
from typing import Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class EnergySource(Enum):
    """Different energy sources with their carbon intensities (gCO2/kWh)"""
    GLOBAL_AVERAGE = 475
    COAL = 820
    NATURAL_GAS = 490
    RENEWABLE = 40
    NUCLEAR = 12
    HYDRO = 24
    WIND = 11
    SOLAR = 40

class DataCenter(Enum):
    """Different data center types with their PUE (Power Usage Effectiveness)"""
    AVERAGE = 1.8
    EFFICIENT = 1.2
    HYPERSCALE = 1.1
    GREEN = 1.05

@dataclass
class CarbonFootprintResult:
    """Result of carbon footprint calculation"""
    total_co2_grams: float
    energy_kwh: float
    data_transfer_mb: float
    data_transfer_co2: float
    server_processing_co2: float
    network_transmission_co2: float
    end_user_device_co2: float
    methodology: str
    confidence_level: str  # high, medium, low
    recommendations: list[str]

class CarbonFootprintCalculator:
    """
    Calculate carbon footprint for websites based on multiple factors:
    - Data transfer (page weight)
    - Server processing energy
    - Network transmission
    - End-user device energy consumption
    - Website-wide estimation (not just homepage)
    """

    def __init__(self):
        # Default assumptions (can be overridden)
        self.energy_source = EnergySource.GLOBAL_AVERAGE
        self.datacenter_pue = DataCenter.AVERAGE
        self.network_efficiency = 0.81  # kWh per GB transferred

    def calculate_website_footprint(
        self,
        page_size_bytes: int,
        server_response_time_ms: Optional[float] = None,
        monthly_visitors: Optional[int] = None,
        energy_source: Optional[EnergySource] = None,
        datacenter_type: Optional[DataCenter] = None,
        estimated_pages: Optional[int] = None,
        pages_per_visit: float = 3.0
    ) -> CarbonFootprintResult:
        """
        Calculate comprehensive carbon footprint for a website

        Args:
            page_size_bytes: Total page size in bytes (homepage)
            server_response_time_ms: Server response time in milliseconds
            monthly_visitors: Estimated monthly visitors
            energy_source: Energy source for calculations
            datacenter_type: Data center efficiency
            estimated_pages: Estimated total pages on website (for scaling)
            pages_per_visit: Average pages viewed per visit

        Returns:
            CarbonFootprintResult with detailed breakdown
        """
        # Use provided values or defaults
        energy_source = energy_source or self.energy_source
        datacenter_type = datacenter_type or self.datacenter_pue

        # Convert bytes to MB/GB
        page_size_mb = page_size_bytes / (1024 * 1024)
        page_size_gb = page_size_mb / 1024

        # Calculate different components of carbon footprint for SINGLE PAGE
        data_transfer_co2 = self._calculate_data_transfer_footprint(
            page_size_gb, energy_source
        )

        server_processing_co2 = self._calculate_server_processing_footprint(
            page_size_bytes, server_response_time_ms, energy_source, datacenter_type
        )

        network_transmission_co2 = self._calculate_network_transmission_footprint(
            page_size_gb, energy_source
        )

        end_user_device_co2 = self._calculate_end_user_device_footprint(
            page_size_bytes, energy_source
        )

        # Total footprint PER PAGE
        total_co2_per_page = (
            data_transfer_co2 +
            server_processing_co2 +
            network_transmission_co2 +
            end_user_device_co2
        )

        # Calculate total energy consumption per page
        total_energy_kwh_per_page = total_co2_per_page / energy_source.value * 1000

        # WEBSITE-WIDE ESTIMATION
        # If we have visitor data, calculate per-visit footprint
        if monthly_visitors and estimated_pages:
            # Average visit sees multiple pages
            total_co2_per_visit = total_co2_per_page * pages_per_visit
            total_energy_per_visit = total_energy_kwh_per_page * pages_per_visit

            # Scale to reflect website complexity
            # Government websites typically have many pages that contribute to overall footprint
            website_scale_factor = min(estimated_pages / 10, 50)  # Cap at 50x

            # Total represents per-visit impact considering site complexity
            total_co2 = total_co2_per_visit * (1 + (website_scale_factor * 0.1))
            total_energy_kwh = total_energy_per_visit * (1 + (website_scale_factor * 0.1))
        else:
            # Without visitor data, use per-page but note it's underestimated
            total_co2 = total_co2_per_page
            total_energy_kwh = total_energy_kwh_per_page

        # Generate recommendations
        recommendations = self._generate_carbon_recommendations(
            page_size_mb, total_co2, server_response_time_ms, estimated_pages
        )

        # Determine confidence level
        confidence = self._determine_confidence_level(
            server_response_time_ms, monthly_visitors, estimated_pages
        )

        return CarbonFootprintResult(
            total_co2_grams=round(total_co2, 4),
            energy_kwh=round(total_energy_kwh, 6),
            data_transfer_mb=round(page_size_mb, 2),
            data_transfer_co2=round(data_transfer_co2, 4),
            server_processing_co2=round(server_processing_co2, 4),
            network_transmission_co2=round(network_transmission_co2, 4),
            end_user_device_co2=round(end_user_device_co2, 4),
            methodology="Sustainable Web Design Model + Website Carbon Calculator (scaled for website size)",
            confidence_level=confidence,
            recommendations=recommendations
        )

    def _calculate_data_transfer_footprint(
        self,
        page_size_gb: float,
        energy_source: EnergySource
    ) -> float:
        """
        Calculate CO2 from data transfer
        Based on: 0.81 kWh per GB transferred (global average)
        """
        # Energy consumption for data transfer
        energy_kwh = page_size_gb * self.network_efficiency

        # Convert to CO2 (grams)
        co2_grams = energy_kwh * energy_source.value

        return co2_grams

    def _calculate_server_processing_footprint(
        self,
        page_size_bytes: int,
        response_time_ms: Optional[float],
        energy_source: EnergySource,
        datacenter_type: DataCenter
    ) -> float:
        """
        Calculate CO2 from server processing
        Based on page complexity and response time
        """
        # Base energy consumption (watts per request)
        base_server_watts = 0.5  # Conservative estimate for a web request

        # Adjust based on page size (larger pages need more processing)
        size_factor = min(page_size_bytes / (1024 * 1024), 10)  # Cap at 10MB equivalent

        # Adjust based on response time if available
        time_factor = 1.0
        if response_time_ms:
            # Longer response times indicate more server work
            time_factor = min(response_time_ms / 500, 5)  # Cap at 5x for very slow responses

        # Calculate energy consumption
        server_watts = base_server_watts * (1 + size_factor * 0.1) * time_factor
        server_kwh = (server_watts / 1000) * (1 / 3600)  # Convert to kWh (assuming 1 second processing)

        # Apply datacenter PUE (Power Usage Effectiveness)
        total_kwh = server_kwh * datacenter_type.value

        # Convert to CO2
        co2_grams = total_kwh * energy_source.value

        return co2_grams

    def _calculate_network_transmission_footprint(
        self,
        page_size_gb: float,
        energy_source: EnergySource
    ) -> float:
        """
        Calculate CO2 from network infrastructure
        Separate from data transfer - this is the network equipment energy
        """
        # Network infrastructure energy (routers, switches, etc.)
        # Approximately 0.1 kWh per GB for network equipment
        network_kwh = page_size_gb * 0.1

        co2_grams = network_kwh * energy_source.value

        return co2_grams

    def _calculate_end_user_device_footprint(
        self,
        page_size_bytes: int,
        energy_source: EnergySource
    ) -> float:
        """
        Calculate CO2 from end-user device energy consumption
        Based on page rendering complexity
        """
        # Base device energy for rendering (watts)
        base_device_watts = 2.0  # CPU + screen energy for web browsing

        # Adjust based on page size (larger pages take more energy to render)
        size_factor = page_size_bytes / (1024 * 1024)  # MB

        # Estimate rendering time (seconds)
        rendering_time_seconds = 3 + (size_factor * 0.5)  # Base 3 seconds + extra for large pages

        # Calculate energy consumption
        device_kwh = (base_device_watts / 1000) * (rendering_time_seconds / 3600)

        # Convert to CO2
        co2_grams = device_kwh * energy_source.value

        return co2_grams

    def _generate_carbon_recommendations(
        self,
        page_size_mb: float,
        total_co2_grams: float,
        response_time_ms: Optional[float],
        estimated_pages: Optional[int] = None
    ) -> list[str]:
        """Generate recommendations to reduce carbon footprint"""
        recommendations = []

        # Website-wide recommendations
        if estimated_pages and estimated_pages > 100:
            recommendations.append(f"🌐 Website has ~{estimated_pages} pages - optimize site-wide to maximize impact")

        # Page size recommendations
        if page_size_mb > 3.0:
            recommendations.append("🗜️ Optimize images and compress assets to reduce page size")
        if page_size_mb > 5.0:
            recommendations.append("🚫 Remove unnecessary JavaScript and CSS frameworks")
        if page_size_mb > 10.0:
            recommendations.append("⚡ Implement lazy loading for images and videos")

        # Performance recommendations
        if response_time_ms and response_time_ms > 1000:
            recommendations.append("🚀 Optimize server response time to reduce processing energy")
        if response_time_ms and response_time_ms > 3000:
            recommendations.append("🏗️ Consider using a Content Delivery Network (CDN)")

        # General recommendations
        if total_co2_grams > 1.0:
            recommendations.append("🌱 Switch to green hosting providers powered by renewable energy")
        if total_co2_grams > 5.0:
            recommendations.append("♻️ Implement aggressive caching strategies")
            recommendations.append("🌿 Consider carbon offset programs for high-traffic sites")

        # Always include these
        recommendations.extend([
            "📱 Optimize for mobile devices to reduce data usage",
            "🔧 Minimize HTTP requests and enable compression",
            "🌍 Use efficient web fonts and avoid excessive web fonts"
        ])

        return recommendations

    def _determine_confidence_level(
        self,
        response_time_ms: Optional[float],
        monthly_visitors: Optional[int],
        estimated_pages: Optional[int] = None
    ) -> str:
        """Determine confidence level of the calculation"""
        score = 0

        # We have response time data
        if response_time_ms is not None:
            score += 1

        # We have visitor data
        if monthly_visitors is not None:
            score += 1

        # We have page count data
        if estimated_pages is not None:
            score += 1

        if score >= 3:
            return "high"
        elif score >= 2:
            return "medium"
        else:
            return "low"

    def calculate_annual_footprint(
        self,
        single_visit_footprint: CarbonFootprintResult,
        monthly_visitors: int,
        pages_per_visit: float = 3.0
    ) -> Dict[str, Any]:
        """
        Calculate annual carbon footprint for a website

        Args:
            single_visit_footprint: Carbon footprint for a single page visit
            monthly_visitors: Number of monthly visitors
            pages_per_visit: Average pages viewed per visit

        Returns:
            Annual footprint data including comparisons
        """
        # Calculate annual totals
        annual_visits = monthly_visitors * 12
        annual_page_views = annual_visits * pages_per_visit
        annual_co2_kg = (single_visit_footprint.total_co2_grams * annual_page_views) / 1000

        # Fun comparisons
        car_miles_equivalent = annual_co2_kg / 0.404  # kg CO2 per mile for average car
        tree_equivalent = annual_co2_kg / 21.8  # kg CO2 absorbed by tree per year

        return {
            "annual_co2_kg": round(annual_co2_kg, 2),
            "annual_visits": annual_visits,
            "annual_page_views": annual_page_views,
            "car_miles_equivalent": round(car_miles_equivalent, 1),
            "trees_needed_to_offset": round(tree_equivalent, 1),
            "percentage_of_average_person_footprint": round((annual_co2_kg / 4000) * 100, 2)  # 4000kg average person/year
        }

    def compare_with_average(self, footprint: CarbonFootprintResult) -> Dict[str, Any]:
        """Compare footprint with industry averages"""
        # Industry averages (grams CO2 per page view)
        AVERAGE_WEBSITE = 4.6
        GOOD_WEBSITE = 1.76
        EXCELLENT_WEBSITE = 0.5

        co2_per_page = footprint.total_co2_grams

        return {
            "grams_co2_per_page": co2_per_page,
            "vs_average_website": round(co2_per_page / AVERAGE_WEBSITE, 2),
            "vs_good_website": round(co2_per_page / GOOD_WEBSITE, 2),
            "vs_excellent_website": round(co2_per_page / EXCELLENT_WEBSITE, 2),
            "rating": self._get_carbon_rating(co2_per_page),
            "percentile": self._get_percentile(co2_per_page)
        }

    def _get_carbon_rating(self, co2_grams: float) -> str:
        """Get letter grade for carbon footprint"""
        if co2_grams <= 0.5:
            return "A+"
        elif co2_grams <= 1.0:
            return "A"
        elif co2_grams <= 2.0:
            return "B"
        elif co2_grams <= 4.0:
            return "C"
        elif co2_grams <= 7.0:
            return "D"
        else:
            return "F"

    def _get_percentile(self, co2_grams: float) -> int:
        """Get percentile ranking (lower CO2 = higher percentile)"""
        if co2_grams <= 0.5:
            return 95
        elif co2_grams <= 1.0:
            return 85
        elif co2_grams <= 2.0:
            return 70
        elif co2_grams <= 4.0:
            return 50
        elif co2_grams <= 7.0:
            return 25
        else:
            return 10

    def estimate_website_pages(self, url: str, page_size_bytes: int) -> int:
        """
        Estimate number of pages on a website based on heuristics

        This is a rough estimation for government websites:
        - Small sites (< 500KB homepage): ~10-50 pages
        - Medium sites (500KB - 2MB): ~50-200 pages
        - Large sites (> 2MB): ~200-1000 pages
        - Government portals typically have 100-500 pages
        """
        page_size_mb = page_size_bytes / (1024 * 1024)

        # Base estimate on page size (larger homepage usually means more pages)
        if page_size_mb < 0.5:
            base_estimate = 25
        elif page_size_mb < 2.0:
            base_estimate = 100
        elif page_size_mb < 5.0:
            base_estimate = 250
        else:
            base_estimate = 500

        # Government websites (.gov.pk) typically have more pages
        if '.gov.pk' in url or '.gov.' in url:
            base_estimate = int(base_estimate * 1.5)

        # Ministry/department sites tend to be larger
        if any(keyword in url.lower() for keyword in ['ministry', 'department', 'ministry']):
            base_estimate = int(base_estimate * 1.3)

        return min(base_estimate, 1000)  # Cap at 1000 pages
