import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any

class DistrictDataAnalyzer:
    def __init__(self, json_file_path: str = "districts_with_constituencies_and_parts.json", log_to_file: bool = True):
        """Initialize the analyzer with the JSON file path."""
        self.json_file_path = json_file_path
        self.data = None
        self.log_to_file = log_to_file
        self.log_file = None
        
        # Setup logging to file if enabled
        if self.log_to_file:
            self.setup_logging()
        
        self.load_data()
    
    def setup_logging(self):
        """Setup file logging with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = f"district_analysis_{timestamp}.log"
        print(f"📝 Logging output to: {self.log_file}")
    
    def log_print(self, *args, **kwargs):
        """Print to console and also write to log file if logging is enabled."""
        # Print to console
        print(*args, **kwargs)
        
        # Write to log file if enabled
        if self.log_to_file and self.log_file:
            try:
                with open(self.log_file, "a", encoding="utf-8") as f:
                    # Convert all arguments to strings and join them
                    message = " ".join(str(arg) for arg in args)
                    f.write(message + "\n")
            except Exception as e:
                print(f"Warning: Could not write to log file: {e}")
    
    def load_data(self) -> bool:
        """Load the JSON data from file."""
        try:
            with open(self.json_file_path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
            self.log_print(f"✅ Successfully loaded data from {self.json_file_path}")
            return True
        except FileNotFoundError:
            self.log_print(f"❌ Error: {self.json_file_path} not found")
            return False
        except json.JSONDecodeError:
            self.log_print(f"❌ Error: Invalid JSON in {self.json_file_path}")
            return False
    
    def get_district_summary(self) -> List[Dict[str, Any]]:
        """Get a summary of all districts with their constituency and part counts."""
        if not self.data:
            return []
        
        summary = []
        for district in self.data:
            district_info = {
                "id": district["id"],
                "name": district["Name"],
                "constituency_count": len(district["Constituencies"]),
                "total_parts": 0,
                "constituencies": []
            }
            
            for constituency in district["Constituencies"]:
                part_list = constituency.get("partList", {}).get("payload", [])
                constituency_info = {
                    "name": constituency["asmblyName"],
                    "ac_number": constituency["asmblyNo"],
                    "part_count": len(part_list),
                    "parts": [{"number": part["partNumber"], "name": part["partName"]} for part in part_list]
                }
                district_info["constituencies"].append(constituency_info)
                district_info["total_parts"] += len(part_list)
            
            summary.append(district_info)
        
        return summary
    
    def get_district_by_id(self, district_id: str) -> Dict[str, Any]:
        """Get detailed information for a specific district by ID."""
        if not self.data:
            return {}
        
        for district in self.data:
            if district["id"] == district_id:
                return district
        return {}
    
    def get_district_by_name(self, district_name: str) -> Dict[str, Any]:
        """Get detailed information for a specific district by name."""
        if not self.data:
            return {}
        
        for district in self.data:
            if district["Name"].lower() == district_name.lower():
                return district
        return {}
    
    def get_constituency_info(self, district_id: str, constituency_name: str = None, ac_number: str = None) -> Dict[str, Any]:
        """Get information about a specific constituency."""
        district = self.get_district_by_id(district_id)
        if not district:
            return {}
        
        for constituency in district["Constituencies"]:
            if constituency_name and constituency["asmblyName"] == constituency_name:
                return constituency
            if ac_number and constituency["asmblyNo"] == ac_number:
                return constituency
        
        return {}
    
    def get_total_stats(self) -> Dict[str, Any]:
        """Get overall statistics for all districts."""
        if not self.data:
            return {}
        
        total_districts = len(self.data)
        total_constituencies = 0
        total_parts = 0
        
        for district in self.data:
            total_constituencies += len(district["Constituencies"])
            for constituency in district["Constituencies"]:
                part_list = constituency.get("partList", {}).get("payload", [])
                total_parts += len(part_list)
        
        return {
            "total_districts": total_districts,
            "total_constituencies": total_constituencies,
            "total_parts": total_parts,
            "average_constituencies_per_district": total_constituencies / total_districts if total_districts > 0 else 0,
            "average_parts_per_constituency": total_parts / total_constituencies if total_constituencies > 0 else 0
        }
    
    def search_constituencies(self, search_term: str) -> List[Dict[str, Any]]:
        """Search for constituencies by name."""
        if not self.data:
            return []
        
        results = []
        search_term_lower = search_term.lower()
        
        for district in self.data:
            for constituency in district["Constituencies"]:
                if search_term_lower in constituency["asmblyName"].lower():
                    result = {
                        "district_id": district["id"],
                        "district_name": district["Name"],
                        "constituency_name": constituency["asmblyName"],
                        "ac_number": constituency["asmblyNo"],
                        "part_count": len(constituency.get("partList", {}).get("payload", []))
                    }
                    results.append(result)
        
        return results
    
    def export_district_summary(self, output_file: str = "district_summary.json"):
        """Export a summary of all districts to a JSON file."""
        summary = self.get_district_summary()
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            self.log_print(f"✅ District summary exported to {output_file}")
            return True
        except Exception as e:
            self.log_print(f"❌ Error exporting summary: {e}")
            return False
    
    def print_district_summary(self):
        """Print a formatted summary of all districts."""
        summary = self.get_district_summary()
        if not summary:
            self.log_print("No data available")
            return
        
        self.log_print("\n" + "="*80)
        self.log_print("DISTRICT SUMMARY")
        self.log_print("="*80)
        
        for district in summary:
            self.log_print(f"\n📁 {district['name']} (ID: {district['id']})")
            self.log_print(f"   Constituencies: {district['constituency_count']}")
            self.log_print(f"   Total Parts: {district['total_parts']}")
            
            if district['constituency_count'] > 0:
                self.log_print("   Constituencies:")
                for constituency in district['constituencies']:
                    self.log_print(f"     • {constituency['name']} (AC: {constituency['ac_number']}) - {constituency['part_count']} parts")
    
    def print_total_stats(self):
        """Print overall statistics."""
        stats = self.get_total_stats()
        if not stats:
            self.log_print("No data available")
            return
        
        self.log_print("\n" + "="*50)
        self.log_print("OVERALL STATISTICS")
        self.log_print("="*50)
        self.log_print(f"Total Districts: {stats['total_districts']}")
        self.log_print(f"Total Constituencies: {stats['total_constituencies']}")
        self.log_print(f"Total Parts: {stats['total_parts']}")
        self.log_print(f"Average Constituencies per District: {stats['average_constituencies_per_district']:.2f}")
        self.log_print(f"Average Parts per Constituency: {stats['average_parts_per_constituency']:.2f}")
    
    def export_detailed_report(self, output_file: str = None):
        """Export a detailed report with all analysis to a text file."""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"detailed_district_report_{timestamp}.txt"
        
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                # Write header
                f.write("="*80 + "\n")
                f.write("DETAILED DISTRICT ANALYSIS REPORT\n")
                f.write("="*80 + "\n")
                f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # Write overall statistics
                stats = self.get_total_stats()
                f.write("OVERALL STATISTICS\n")
                f.write("-"*50 + "\n")
                f.write(f"Total Districts: {stats['total_districts']}\n")
                f.write(f"Total Constituencies: {stats['total_constituencies']}\n")
                f.write(f"Total Parts: {stats['total_parts']}\n")
                f.write(f"Average Constituencies per District: {stats['average_constituencies_per_district']:.2f}\n")
                f.write(f"Average Parts per Constituency: {stats['average_parts_per_constituency']:.2f}\n\n")
                
                # Write district details
                summary = self.get_district_summary()
                f.write("DISTRICT DETAILS\n")
                f.write("-"*50 + "\n")
                
                for district in summary:
                    f.write(f"\n📁 {district['name']} (ID: {district['id']})\n")
                    f.write(f"   Constituencies: {district['constituency_count']}\n")
                    f.write(f"   Total Parts: {district['total_parts']}\n")
                    
                    if district['constituency_count'] > 0:
                        f.write("   Constituencies:\n")
                        for constituency in district['constituencies']:
                            f.write(f"     • {constituency['name']} (AC: {constituency['ac_number']}) - {constituency['part_count']} parts\n")
                
                # Write top districts by parts
                f.write("\n" + "="*50 + "\n")
                f.write("TOP DISTRICTS BY TOTAL PARTS\n")
                f.write("="*50 + "\n")
                sorted_districts = sorted(summary, key=lambda x: x['total_parts'], reverse=True)
                for i, district in enumerate(sorted_districts[:10], 1):
                    f.write(f"{i:2d}. {district['name']}: {district['total_parts']} parts\n")
                
                # Write top constituencies by parts
                f.write("\n" + "="*50 + "\n")
                f.write("TOP CONSTITUENCIES BY PARTS\n")
                f.write("="*50 + "\n")
                all_constituencies = []
                for district in summary:
                    for constituency in district['constituencies']:
                        all_constituencies.append({
                            'district': district['name'],
                            'name': constituency['name'],
                            'ac_number': constituency['ac_number'],
                            'part_count': constituency['part_count']
                        })
                
                sorted_constituencies = sorted(all_constituencies, key=lambda x: x['part_count'], reverse=True)
                for i, constituency in enumerate(sorted_constituencies[:15], 1):
                    f.write(f"{i:2d}. {constituency['name']} ({constituency['district']}) - AC: {constituency['ac_number']} - {constituency['part_count']} parts\n")
            
            self.log_print(f"✅ Detailed report exported to {output_file}")
            return True
        except Exception as e:
            self.log_print(f"❌ Error exporting detailed report: {e}")
            return False

def main():
    """Main function to demonstrate the analyzer functionality."""
    analyzer = DistrictDataAnalyzer()
    
    if not analyzer.data:
        analyzer.log_print("Failed to load data. Exiting.")
        return
    
    # Print overall statistics
    analyzer.print_total_stats()
    
    # Print district summary
    analyzer.print_district_summary()
    
    # Example: Get specific district info
    analyzer.log_print("\n" + "="*50)
    analyzer.log_print("EXAMPLE: HYDERABAD DISTRICT INFO")
    analyzer.log_print("="*50)
    hyderabad = analyzer.get_district_by_name("Hyderabad")
    if hyderabad:
        analyzer.log_print(f"District: {hyderabad['Name']}")
        analyzer.log_print(f"ID: {hyderabad['id']}")
        analyzer.log_print(f"Constituencies: {len(hyderabad['Constituencies'])}")
        
        total_parts = 0
        for constituency in hyderabad['Constituencies']:
            part_list = constituency.get("partList", {}).get("payload", [])
            total_parts += len(part_list)
        analyzer.log_print(f"Total Parts: {total_parts}")
    else:
        analyzer.log_print("Hyderabad district not found")
    
    # Export summary to JSON file
    analyzer.export_district_summary()
    
    # Export detailed report
    analyzer.export_detailed_report()
    
    analyzer.log_print(f"\n📁 Analysis complete! Check the log file: {analyzer.log_file}")

if __name__ == "__main__":
    main()
