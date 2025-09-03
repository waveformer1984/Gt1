#!/usr/bin/env python3
"""
Comprehensive Web Services Report Generator
Consolidates all testing results into a final verification report
"""

import json
import time
import os
from typing import Dict, Any, List
from pathlib import Path

class ComprehensiveReportGenerator:
    """Generate comprehensive web services verification report."""
    
    def __init__(self):
        self.report_files = [
            "web_services_verification_report.json",
            "api_endpoint_test_report.json", 
            "websocket_test_report.json",
            "security_performance_test_report.json"
        ]
        
    def log(self, message: str, level: str = "INFO"):
        """Log a message with timestamp."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def load_report_data(self) -> Dict[str, Any]:
        """Load all available test report data."""
        reports = {}
        
        for report_file in self.report_files:
            if os.path.exists(report_file):
                try:
                    with open(report_file, 'r') as f:
                        reports[report_file] = json.load(f)
                    self.log(f"✅ Loaded {report_file}")
                except Exception as e:
                    self.log(f"❌ Failed to load {report_file}: {e}")
                    reports[report_file] = {"error": str(e)}
            else:
                self.log(f"⚠️  {report_file} not found")
                reports[report_file] = {"status": "not_found"}
        
        return reports
    
    def analyze_web_services_verification(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze web services verification results."""
        if "error" in data or "status" in data:
            return {
                "status": "INCOMPLETE",
                "summary": "Web services verification did not complete successfully",
                "details": data
            }
        
        summary = data.get("summary", {})
        
        return {
            "status": "PASS" if summary.get("failed", 0) == 0 else "PARTIAL",
            "total_tests": summary.get("total_tests", 0),
            "passed": summary.get("passed", 0),
            "failed": summary.get("failed", 0),
            "success_rate": (summary.get("passed", 0) / summary.get("total_tests", 1)) * 100,
            "key_findings": self.extract_key_findings(data.get("results", []))
        }
    
    def analyze_api_endpoint_tests(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze API endpoint test results."""
        if "error" in data or "status" in data:
            return {
                "status": "INCOMPLETE",
                "summary": "API endpoint tests did not complete successfully",
                "details": data
            }
        
        endpoint_summary = data.get("api_endpoint_tests", {}).get("summary", {})
        load_test = data.get("load_tests", {})
        
        return {
            "status": "PASS" if endpoint_summary.get("failed_tests", 0) == 0 else "PARTIAL",
            "endpoint_tests": {
                "total": endpoint_summary.get("total_endpoints_tested", 0),
                "successful": endpoint_summary.get("successful_tests", 0),
                "failed": endpoint_summary.get("failed_tests", 0),
                "success_rate": endpoint_summary.get("success_rate", 0),
                "avg_response_time": endpoint_summary.get("average_response_time", 0)
            },
            "load_test": {
                "requests_per_second": load_test.get("requests_per_second", 0),
                "success_rate": load_test.get("success_rate", 0),
                "total_requests": load_test.get("total_requests", 0)
            },
            "websocket_status": data.get("websocket_tests", {}).get("websocket_test", "UNKNOWN")
        }
    
    def analyze_security_performance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze security and performance test results."""
        if "error" in data or "status" in data:
            return {
                "status": "INCOMPLETE",
                "summary": "Security and performance tests did not complete successfully",
                "details": data
            }
        
        summary = data.get("summary", {})
        security_tests = data.get("security_tests", {})
        performance_tests = data.get("performance_tests", {})
        
        return {
            "status": "PASS" if summary.get("failed_tests", 0) == 0 else "PARTIAL",
            "overall_success_rate": summary.get("success_rate", 0),
            "security": {
                "passed": security_tests.get("passed", 0),
                "total": security_tests.get("total", 0),
                "status": "PASS" if security_tests.get("passed", 0) == security_tests.get("total", 0) else "PARTIAL"
            },
            "performance": {
                "passed": performance_tests.get("passed", 0),
                "total": performance_tests.get("total", 0),
                "status": "PASS" if performance_tests.get("passed", 0) == performance_tests.get("total", 0) else "PARTIAL"
            }
        }
    
    def extract_key_findings(self, results: List[Dict[str, Any]]) -> List[str]:
        """Extract key findings from test results."""
        findings = []
        
        for result in results:
            if result.get("status") == "PASS":
                findings.append(f"✅ {result.get('test_name', 'Unknown test')} passed")
            elif result.get("status") == "FAIL":
                findings.append(f"❌ {result.get('test_name', 'Unknown test')} failed: {result.get('message', 'No details')}")
        
        return findings
    
    def assess_overall_status(self, analyses: Dict[str, Any]) -> str:
        """Assess overall web services status."""
        statuses = []
        
        for analysis in analyses.values():
            if isinstance(analysis, dict) and "status" in analysis:
                statuses.append(analysis["status"])
        
        if all(status == "PASS" for status in statuses):
            return "FULLY_OPERATIONAL"
        elif any(status == "PASS" for status in statuses):
            return "PARTIALLY_OPERATIONAL"
        elif any(status == "PARTIAL" for status in statuses):
            return "LIMITED_FUNCTIONALITY"
        else:
            return "NEEDS_ATTENTION"
    
    def generate_recommendations(self, analyses: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        # Check web services verification
        ws_verification = analyses.get("web_services_verification", {})
        if ws_verification.get("status") != "PASS":
            recommendations.append("🔧 Complete web services setup - some core components are not fully functional")
        
        # Check API performance
        api_analysis = analyses.get("api_endpoint_tests", {})
        if api_analysis.get("status") == "PASS":
            avg_response = api_analysis.get("endpoint_tests", {}).get("avg_response_time", 0)
            if avg_response > 0.1:
                recommendations.append("⚡ Consider optimizing API response times (currently averaging {:.3f}s)".format(avg_response))
        
        # Check WebSocket functionality
        if api_analysis.get("websocket_status") in ["SKIPPED", "FAIL"]:
            recommendations.append("🔌 WebSocket functionality needs attention - real-time features may not work")
        
        # Check security
        security_perf = analyses.get("security_performance", {})
        if security_perf.get("security", {}).get("status") != "PASS":
            recommendations.append("🔒 Review security configurations - some security tests did not pass")
        
        if not recommendations:
            recommendations.append("✅ All systems operational - web services are functioning well")
        
        return recommendations
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate the comprehensive verification report."""
        self.log("📊 Generating comprehensive web services verification report...")
        
        # Load all report data
        reports = self.load_report_data()
        
        # Analyze each report type
        analyses = {
            "web_services_verification": self.analyze_web_services_verification(
                reports.get("web_services_verification_report.json", {})
            ),
            "api_endpoint_tests": self.analyze_api_endpoint_tests(
                reports.get("api_endpoint_test_report.json", {})
            ),
            "security_performance": self.analyze_security_performance(
                reports.get("security_performance_test_report.json", {})
            )
        }
        
        # Assess overall status
        overall_status = self.assess_overall_status(analyses)
        
        # Generate recommendations
        recommendations = self.generate_recommendations(analyses)
        
        # Create comprehensive report
        comprehensive_report = {
            "report_metadata": {
                "title": "ballsDeepnit Web Services Comprehensive Verification Report",
                "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "report_version": "1.0",
                "total_test_suites": len([a for a in analyses.values() if a.get("status") != "INCOMPLETE"])
            },
            "executive_summary": {
                "overall_status": overall_status,
                "status_description": self.get_status_description(overall_status),
                "key_metrics": self.extract_key_metrics(analyses),
                "critical_issues": self.extract_critical_issues(analyses),
                "recommendations": recommendations
            },
            "detailed_analyses": analyses,
            "test_coverage": {
                "core_functionality": analyses.get("web_services_verification", {}).get("status", "INCOMPLETE"),
                "api_endpoints": analyses.get("api_endpoint_tests", {}).get("status", "INCOMPLETE"),
                "security": analyses.get("security_performance", {}).get("security", {}).get("status", "INCOMPLETE"),
                "performance": analyses.get("security_performance", {}).get("performance", {}).get("status", "INCOMPLETE"),
                "websocket_support": analyses.get("api_endpoint_tests", {}).get("websocket_status", "UNKNOWN")
            },
            "raw_data": reports
        }
        
        return comprehensive_report
    
    def get_status_description(self, status: str) -> str:
        """Get human-readable status description."""
        descriptions = {
            "FULLY_OPERATIONAL": "All web services are functioning correctly and pass all tests",
            "PARTIALLY_OPERATIONAL": "Most web services are working but some issues were detected",
            "LIMITED_FUNCTIONALITY": "Basic functionality works but significant limitations exist",
            "NEEDS_ATTENTION": "Multiple issues detected that require immediate attention"
        }
        return descriptions.get(status, "Status could not be determined")
    
    def extract_key_metrics(self, analyses: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key metrics from analyses."""
        api_analysis = analyses.get("api_endpoint_tests", {})
        security_perf = analyses.get("security_performance", {})
        
        return {
            "api_success_rate": api_analysis.get("endpoint_tests", {}).get("success_rate", 0),
            "avg_response_time_ms": (api_analysis.get("endpoint_tests", {}).get("avg_response_time", 0) * 1000),
            "load_test_rps": api_analysis.get("load_test", {}).get("requests_per_second", 0),
            "security_score": security_perf.get("security", {}).get("passed", 0) / max(security_perf.get("security", {}).get("total", 1), 1) * 100,
            "performance_score": security_perf.get("performance", {}).get("passed", 0) / max(security_perf.get("performance", {}).get("total", 1), 1) * 100
        }
    
    def extract_critical_issues(self, analyses: Dict[str, Any]) -> List[str]:
        """Extract critical issues that need attention."""
        issues = []
        
        for test_type, analysis in analyses.items():
            if analysis.get("status") == "INCOMPLETE":
                issues.append(f"❌ {test_type.replace('_', ' ').title()} did not complete")
            elif analysis.get("status") == "PARTIAL":
                issues.append(f"⚠️  {test_type.replace('_', ' ').title()} has some failures")
        
        return issues
    
    def save_and_display_report(self, report: Dict[str, Any]) -> None:
        """Save and display the comprehensive report."""
        # Save JSON report
        report_filename = "COMPREHENSIVE_WEB_SERVICES_VERIFICATION_REPORT.json"
        with open(report_filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Display executive summary
        print("\n" + "="*80)
        print("🚀 BALLSDEEPNIT WEB SERVICES VERIFICATION REPORT")
        print("="*80)
        
        summary = report["executive_summary"]
        print(f"\n📊 OVERALL STATUS: {summary['overall_status']}")
        print(f"📝 DESCRIPTION: {summary['status_description']}")
        
        print("\n🔑 KEY METRICS:")
        metrics = summary["key_metrics"]
        print(f"   • API Success Rate: {metrics['api_success_rate']:.1f}%")
        print(f"   • Avg Response Time: {metrics['avg_response_time_ms']:.1f}ms")
        print(f"   • Load Test RPS: {metrics['load_test_rps']:.1f}")
        print(f"   • Security Score: {metrics['security_score']:.1f}%")
        print(f"   • Performance Score: {metrics['performance_score']:.1f}%")
        
        if summary["critical_issues"]:
            print("\n⚠️  CRITICAL ISSUES:")
            for issue in summary["critical_issues"]:
                print(f"   {issue}")
        else:
            print("\n✅ No critical issues detected")
        
        print("\n💡 RECOMMENDATIONS:")
        for rec in summary["recommendations"]:
            print(f"   {rec}")
        
        print("\n📋 TEST COVERAGE:")
        coverage = report["test_coverage"]
        for test_type, status in coverage.items():
            icon = "✅" if status == "PASS" else "⚠️" if status in ["PARTIAL", "WARNING"] else "❌"
            print(f"   {icon} {test_type.replace('_', ' ').title()}: {status}")
        
        print(f"\n📄 Full report saved to: {report_filename}")
        print("="*80)

def main():
    """Main function to generate comprehensive report."""
    generator = ComprehensiveReportGenerator()
    report = generator.generate_comprehensive_report()
    generator.save_and_display_report(report)

if __name__ == "__main__":
    main()