import requests
import sys
import json
import tempfile
import os
from datetime import datetime
from pathlib import Path

class SecurityFileAnalyzerTester:
    def __init__(self, base_url="https://cleanpii.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
        
        result = {
            "test_name": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} - {name}")
        if details:
            print(f"   Details: {details}")

    def test_api_health(self):
        """Test API health endpoint"""
        try:
            response = requests.get(f"{self.api_url}/", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}, Response: {response.json() if success else response.text}"
            self.log_test("API Health Check", success, details)
            return success
        except Exception as e:
            self.log_test("API Health Check", False, f"Error: {str(e)}")
            return False

    def create_test_file(self, filename, content):
        """Create a temporary test file"""
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, filename)
        
        if filename.endswith('.txt'):
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        return file_path

    def test_single_file_upload(self):
        """Test single file upload and analysis"""
        try:
            # Create test file with PII data
            test_content = """
            John Doe
            SSN: 123-45-6789
            Email: john.doe@example.com
            Phone: (555) 123-4567
            Credit Card: 4532-1234-5678-9012
            Address: 123 Main Street, Anytown
            
            This is a test document containing various types of personally identifiable information.
            The document should be analyzed for security vulnerabilities and PII detection.
            """
            
            file_path = self.create_test_file("test_document.txt", test_content)
            
            with open(file_path, 'rb') as f:
                files = {'file': ('test_document.txt', f, 'text/plain')}
                response = requests.post(f"{self.api_url}/upload-single", files=files, timeout=30)
            
            success = response.status_code == 200
            if success:
                data = response.json()
                pii_count = len(data.get('pii_detected', []))
                details = f"Status: {response.status_code}, PII detected: {pii_count}, File type: {data.get('file_type')}"
                
                # Verify expected PII detection
                if pii_count >= 5:  # Should detect at least SSN, email, phone, credit card, name
                    details += " - PII detection working correctly"
                else:
                    details += f" - WARNING: Expected more PII items, only found {pii_count}"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("Single File Upload & Analysis", success, details)
            
            # Clean up
            os.unlink(file_path)
            
            return success, response.json() if success else {}
            
        except Exception as e:
            self.log_test("Single File Upload & Analysis", False, f"Error: {str(e)}")
            return False, {}

    def test_batch_file_upload(self):
        """Test batch file upload and analysis"""
        try:
            # Create multiple test files
            files_data = [
                ("doc1.txt", "Employee: Jane Smith\nSSN: 987-65-4321\nEmail: jane@company.com"),
                ("doc2.txt", "Customer phone: (555) 987-6543\nCredit Card: 5555-4444-3333-2222"),
            ]
            
            file_paths = []
            files_for_upload = []
            
            for filename, content in files_data:
                file_path = self.create_test_file(filename, content)
                file_paths.append(file_path)
                files_for_upload.append(('files', (filename, open(file_path, 'rb'), 'text/plain')))
            
            # Add batch name
            data = {'batch_name': 'test_batch_analysis'}
            
            response = requests.post(f"{self.api_url}/upload-batch", files=files_for_upload, data=data, timeout=45)
            
            # Close file handles
            for _, (_, file_handle, _) in files_for_upload:
                file_handle.close()
            
            success = response.status_code == 200
            if success:
                data = response.json()
                files_processed = data.get('files_processed', 0)
                batch_id = data.get('id')
                details = f"Status: {response.status_code}, Files processed: {files_processed}, Batch ID: {batch_id}"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("Batch File Upload & Analysis", success, details)
            
            # Clean up
            for file_path in file_paths:
                os.unlink(file_path)
            
            return success, response.json() if success else {}
            
        except Exception as e:
            self.log_test("Batch File Upload & Analysis", False, f"Error: {str(e)}")
            return False, {}

    def test_analysis_history(self):
        """Test analysis history retrieval"""
        try:
            response = requests.get(f"{self.api_url}/analysis-history", timeout=15)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                single_files = len(data.get('single_files', []))
                batches = len(data.get('batches', []))
                details = f"Status: {response.status_code}, Single files: {single_files}, Batches: {batches}"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("Analysis History Retrieval", success, details)
            return success, response.json() if success else {}
            
        except Exception as e:
            self.log_test("Analysis History Retrieval", False, f"Error: {str(e)}")
            return False, {}

    def test_export_functionality(self, batch_id):
        """Test Excel export functionality"""
        if not batch_id:
            self.log_test("Excel Export", False, "No batch ID available for testing")
            return False
        
        try:
            response = requests.get(f"{self.api_url}/export-results/{batch_id}", timeout=20)
            success = response.status_code == 200
            
            if success:
                # Check if response is Excel file
                content_type = response.headers.get('content-type', '')
                is_excel = 'spreadsheet' in content_type or 'excel' in content_type
                file_size = len(response.content)
                details = f"Status: {response.status_code}, Content-Type: {content_type}, Size: {file_size} bytes, Is Excel: {is_excel}"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("Excel Export", success, details)
            return success
            
        except Exception as e:
            self.log_test("Excel Export", False, f"Error: {str(e)}")
            return False

    def test_pii_detection_accuracy(self):
        """Test PII detection accuracy with known patterns"""
        try:
            # Test content with specific PII patterns
            test_content = """
            Personal Information:
            Name: Michael Johnson
            SSN: 555-12-3456
            Email: michael.johnson@testcompany.org
            Phone: +1 (555) 234-5678
            Credit Card: 4111-1111-1111-1111
            Address: 456 Oak Avenue, Springfield
            ZIP: 12345-6789
            Driver's License: D123456789
            Bank Account: 1234567890123456
            """
            
            file_path = self.create_test_file("pii_test.txt", test_content)
            
            with open(file_path, 'rb') as f:
                files = {'file': ('pii_test.txt', f, 'text/plain')}
                response = requests.post(f"{self.api_url}/upload-single", files=files, timeout=30)
            
            success = response.status_code == 200
            if success:
                data = response.json()
                pii_detected = data.get('pii_detected', [])
                pii_types = [item['type'] for item in pii_detected]
                
                # Check for expected PII types
                expected_types = ['name', 'ssn', 'email', 'phone', 'credit_card', 'address', 'zip_code']
                detected_expected = [pii_type for pii_type in expected_types if pii_type in pii_types]
                
                details = f"PII detected: {len(pii_detected)}, Types found: {detected_expected}, All types: {pii_types}"
                
                # Consider successful if at least 5 expected types are detected
                success = len(detected_expected) >= 5
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("PII Detection Accuracy", success, details)
            
            # Clean up
            os.unlink(file_path)
            
            return success
            
        except Exception as e:
            self.log_test("PII Detection Accuracy", False, f"Error: {str(e)}")
            return False

    def run_comprehensive_test(self):
        """Run all tests in sequence"""
        print("🔍 Starting Security File Analyzer API Tests...")
        print("=" * 60)
        
        # Test 1: API Health
        if not self.test_api_health():
            print("❌ API is not accessible. Stopping tests.")
            return False
        
        # Test 2: Single file upload
        single_success, single_result = self.test_single_file_upload()
        
        # Test 3: Batch file upload
        batch_success, batch_result = self.test_batch_file_upload()
        batch_id = batch_result.get('id') if batch_success else None
        
        # Test 4: Analysis history
        self.test_analysis_history()
        
        # Test 5: Export functionality (if we have a batch ID)
        if batch_id:
            self.test_export_functionality(batch_id)
        
        # Test 6: PII detection accuracy
        self.test_pii_detection_accuracy()
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return True
        else:
            print("⚠️  Some tests failed. Check details above.")
            return False

def main():
    tester = SecurityFileAnalyzerTester()
    success = tester.run_comprehensive_test()
    
    # Save test results
    results_file = "/app/backend_test_results.json"
    with open(results_file, 'w') as f:
        json.dump({
            "summary": {
                "total_tests": tester.tests_run,
                "passed_tests": tester.tests_passed,
                "success_rate": (tester.tests_passed/tester.tests_run)*100 if tester.tests_run > 0 else 0,
                "timestamp": datetime.now().isoformat()
            },
            "test_results": tester.test_results
        }, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: {results_file}")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())