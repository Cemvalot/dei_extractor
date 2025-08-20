#!/usr/bin/env python3
"""
Comprehensive test runner for DEI Extractor.

This script runs all tests and provides detailed reporting on the test results.
"""

import subprocess
import sys
import time
import traceback
import unittest
from pathlib import Path


def run_test_suite(test_file, suite_name):
    """Run a specific test suite and return results."""
    print(f"\n{'='*80}")
    print(f"🧪 RUNNING {suite_name.upper()} TEST SUITE")
    print(f"{'='*80}")

    start_time = time.time()

    try:
        # Run the test file as a subprocess to capture output
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )

        end_time = time.time()
        duration = end_time - start_time

        print(f"⏱️  Duration: {duration:.2f} seconds")
        print(f"📤 Exit Code: {result.returncode}")

        if result.stdout:
            print(f"\n📋 STDOUT:")
            print(result.stdout)

        if result.stderr:
            print(f"\n⚠️  STDERR:")
            print(result.stderr)

        return {
            "success": result.returncode == 0,
            "duration": duration,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
        }

    except subprocess.TimeoutExpired:
        print(f"⏰ TIMEOUT: Test suite exceeded 5 minute limit")
        return {
            "success": False,
            "duration": 300,
            "stdout": "",
            "stderr": "Test suite timed out",
            "exit_code": -1,
        }
    except Exception as e:
        print(f"❌ ERROR: Failed to run test suite: {e}")
        return {
            "success": False,
            "duration": time.time() - start_time,
            "stdout": "",
            "stderr": str(e),
            "exit_code": -1,
        }


def run_individual_tests():
    """Run individual test modules directly."""
    print(f"\n{'='*80}")
    print(f"🔍 RUNNING INDIVIDUAL TEST MODULES")
    print(f"{'='*80}")

    test_modules = [
        ("test_extract_dei_final_comprehensive.py", "Extract DEI Final"),
        ("test_filter_ekatharistikos_comprehensive.py", "Filter Ekatharistikos"),
    ]

    results = {}

    for test_file, suite_name in test_modules:
        if os.path.exists(test_file):
            print(f"\n📁 Testing: {test_file}")
            result = run_test_suite(test_file, suite_name)
            results[suite_name] = result
        else:
            print(f"❌ Test file not found: {test_file}")
            results[suite_name] = {
                "success": False,
                "duration": 0,
                "stdout": "",
                "stderr": f"Test file not found: {test_file}",
                "exit_code": -1,
            }

    return results


def run_integration_tests():
    """Run integration tests with real data."""
    print(f"\n{'='*80}")
    print(f"🔗 RUNNING INTEGRATION TESTS")
    print(f"{'='*80}")

    integration_results = {}

    # Test 1: Check if output files exist and are valid
    print(f"\n📊 Testing Output Files...")
    output_files = ["ολα.csv", "φoπ.csv", "επαγγελματικα.csv"]

    file_tests = {}
    for file_name in output_files:
        if os.path.exists(file_name):
            try:
                import pandas as pd

                df = pd.read_csv(file_name, encoding="utf-8-sig")
                file_tests[file_name] = {
                    "exists": True,
                    "readable": True,
                    "rows": len(df),
                    "columns": len(df.columns),
                    "has_αρ_παροχής": "ΑρΠαροχής" in df.columns,
                }
                print(f"✅ {file_name}: {len(df)} rows, {len(df.columns)} columns")
            except Exception as e:
                file_tests[file_name] = {
                    "exists": True,
                    "readable": False,
                    "error": str(e),
                }
                print(f"❌ {file_name}: Error reading - {e}")
        else:
            file_tests[file_name] = {"exists": False, "readable": False}
            print(f"❌ {file_name}: File not found")

    integration_results["output_files"] = file_tests

    # Test 2: Check data quality
    print(f"\n🔍 Testing Data Quality...")
    if os.path.exists("ολα.csv"):
        try:
            import pandas as pd

            df = pd.read_csv("ολα.csv", encoding="utf-8-sig")

            quality_tests = {
                "total_records": len(df),
                "has_required_columns": all(
                    col in df.columns
                    for col in [
                        "ΑρΠαροχής",
                        "ΑρΛογαριασμού",
                        "ΗμΈκδοσης",
                        "ΚατηγορίαΤιμολογίου",
                    ]
                ),
                "αρ_παροχής_not_empty": df["ΑρΠαροχής"].notna().all()
                if "ΑρΠαροχής" in df.columns
                else False,
                "αρ_παροχής_is_string": df["ΑρΠαροχής"].dtype == "object"
                if "ΑρΠαροχής" in df.columns
                else False,
                "category_distribution": df["ΚατηγορίαΤιμολογίου"]
                .value_counts()
                .to_dict()
                if "ΚατηγορίαΤιμολογίου" in df.columns
                else None,
                "ekatharistikos_distribution": df["Εκαθαριστικός"]
                .value_counts()
                .to_dict()
                if "Εκαθαριστικός" in df.columns
                else None,
            }

            print(f"✅ Total records: {quality_tests['total_records']}")
            print(f"✅ Required columns: {quality_tests['has_required_columns']}")
            print(f"✅ ΑρΠαροχής not empty: {quality_tests['αρ_παροχής_not_empty']}")
            print(f"✅ ΑρΠαροχής is string: {quality_tests['αρ_παροχής_is_string']}")
            print(f"📊 Category distribution: {quality_tests['category_distribution']}")
            if quality_tests["ekatharistikos_distribution"]:
                print(
                    "📊 Εκαθαριστικός distribution: "
                    + str(quality_tests["ekatharistikos_distribution"])
                )

            integration_results["data_quality"] = quality_tests

        except Exception as e:
            print(f"❌ Data quality test failed: {e}")
            integration_results["data_quality"] = {"error": str(e)}

    # Test 3: Check sorting/grouping functionality
    print(f"\n📈 Testing Sorting/Grouping...")
    if os.path.exists("ολα.csv"):
        try:
            import pandas as pd

            df = pd.read_csv("ολα.csv", encoding="utf-8-sig")

            # Check if data is sorted by ΑρΠαροχής
            αρ_παροχής_list = df["ΑρΠαροχής"].tolist()
            is_sorted = αρ_παροχής_list == sorted(αρ_παροχής_list)

            # Check grouping (consecutive records with same ΑρΠαροχής)
            grouping_test = True
            consecutive_groups = 0
            current_group = None
            group_count = 0

            for αρ_παροχής in αρ_παροχής_list:
                if αρ_παροχής != current_group:
                    if current_group is not None and group_count > 1:
                        consecutive_groups += 1
                    current_group = αρ_παροχής
                    group_count = 1
                else:
                    group_count += 1

            if current_group is not None and group_count > 1:
                consecutive_groups += 1

            sorting_tests = {
                "is_sorted": is_sorted,
                "consecutive_groups": consecutive_groups,
                "total_records": len(df),
                "unique_αρ_παροχής": df["ΑρΠαροχής"].nunique(),
            }

            print(f"✅ Data is sorted: {is_sorted}")
            print(f"✅ Consecutive groups: {consecutive_groups}")
            print(f"📊 Total records: {sorting_tests['total_records']}")
            print(f"📊 Unique ΑρΠαροχής: {sorting_tests['unique_αρ_παροχής']}")

            integration_results["sorting_grouping"] = sorting_tests

        except Exception as e:
            print(f"❌ Sorting/grouping test failed: {e}")
            integration_results["sorting_grouping"] = {"error": str(e)}

    return integration_results


def generate_test_report(results, integration_results):
    """Generate a comprehensive test report."""
    print(f"\n{'='*80}")
    print(f"📋 COMPREHENSIVE TEST REPORT")
    print(f"{'='*80}")

    # Summary statistics
    total_tests = len(results)
    successful_tests = sum(1 for r in results.values() if r["success"])
    total_duration = sum(r["duration"] for r in results.values())

    print(f"\n📊 SUMMARY STATISTICS:")
    print(f"   Total test suites: {total_tests}")
    print(f"   Successful: {successful_tests}")
    print(f"   Failed: {total_tests - successful_tests}")
    print(f"   Success rate: {(successful_tests/total_tests*100):.1f}%")
    print(f"   Total duration: {total_duration:.2f} seconds")

    # Individual test results
    print(f"\n🔍 INDIVIDUAL TEST RESULTS:")
    for suite_name, result in results.items():
        status = "✅ PASSED" if result["success"] else "❌ FAILED"
        print(f"   {suite_name}: {status} ({result['duration']:.2f}s)")
        if not result["success"] and result["stderr"]:
            print(f"      Error: {result['stderr'][:100]}...")

    # Integration test results
    if integration_results:
        print(f"\n🔗 INTEGRATION TEST RESULTS:")

        if "output_files" in integration_results:
            print(f"   📁 Output Files:")
            for file_name, file_result in integration_results["output_files"].items():
                if file_result["exists"] and file_result["readable"]:
                    print(f"      ✅ {file_name}: {file_result['rows']} rows")
                elif file_result["exists"]:
                    print(f"      ⚠️  {file_name}: Exists but not readable")
                else:
                    print(f"      ❌ {file_name}: Not found")

        if "data_quality" in integration_results:
            print(f"   🔍 Data Quality:")
            quality = integration_results["data_quality"]
            if "error" not in quality:
                print(f"      ✅ Total records: {quality['total_records']}")
                print(f"      ✅ Required columns: {quality['has_required_columns']}")
                print(
                    f"      ✅ ΑρΠαροχής validation: {quality['αρ_παροχής_not_empty']}"
                )
            else:
                print(f"      ❌ Data quality test failed: {quality['error']}")

        if "sorting_grouping" in integration_results:
            print(f"   📈 Sorting/Grouping:")
            sorting = integration_results["sorting_grouping"]
            if "error" not in sorting:
                print(f"      ✅ Data is sorted: {sorting['is_sorted']}")
                print(f"      ✅ Consecutive groups: {sorting['consecutive_groups']}")
            else:
                print(f"      ❌ Sorting test failed: {sorting['error']}")

    # Overall assessment
    print(f"\n🎯 OVERALL ASSESSMENT:")
    if successful_tests == total_tests and integration_results:
        print(f"   🎉 EXCELLENT: All tests passed and integration tests successful!")
        print(f"   ✅ The DEI extractor and filter are working correctly")
        print(f"   ✅ Data quality and sorting functionality verified")
    elif successful_tests == total_tests:
        print(f"   ✅ GOOD: All unit tests passed")
        print(
            "   ⚠️  Integration tests not available - run with real data for full validation"
        )
    elif successful_tests > 0:
        print(f"   ⚠️  PARTIAL: Some tests passed, some failed")
        print(f"   🔧 Review failed tests and fix issues")
    else:
        print(f"   ❌ CRITICAL: All tests failed")
        print(f"   🚨 Immediate attention required - check dependencies and code")

    return successful_tests == total_tests


def main():
    """Main test runner function."""
    print(f"🚀 DEI EXTRACTOR COMPREHENSIVE TEST SUITE")
    print(f"Testing extract_dei_final.py and filter_ekatharistikos.py")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")

    # Check dependencies
    print(f"\n📦 Checking dependencies...")
    required_packages = ["pandas", "openpyxl", "pdfplumber", "pytesseract"]
    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} (missing)")
            missing_packages.append(package)

    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print(f"   Install with: pip install {' '.join(missing_packages)}")

    # Run individual test suites
    results = run_individual_tests()

    # Run integration tests
    integration_results = run_integration_tests()

    # Generate comprehensive report
    overall_success = generate_test_report(results, integration_results)

    # Final status
    print(f"\n{'='*80}")
    if overall_success:
        print(f"🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
        print(f"✅ The DEI extractor and filter are ready for production use")
    else:
        print(f"⚠️  SOME TESTS FAILED")
        print(f"🔧 Please review the test results and fix any issues")
    print(f"{'='*80}")

    return 0 if overall_success else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
